import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Baseline, BoardData, BoardTab, DecisionRow, GitNow, GitSnap, Term } from '../types'
import { changesMarkdown, readGit, takeBaseline } from './changes'
import type { GitRun } from './changes'
import { kDefaultGlossary, findTerms, mergeSeen } from './glossary'
import { buildBoard, cell, folderTitle, formatLocalTime, kConfigPath, kDefaultTitle, parseBoardCommand, validateConfig } from './parse'
import type { BoardConfig } from './parse'

const kPane = 'project-board'

const tab = atom({ plugin: 'project-board', key: 'tab' } as const, 'status' as BoardTab)
const data = atom({ plugin: 'project-board', key: 'data' } as const, null as BoardData | null)
const seenTerms = atom({ plugin: 'project-board', key: 'seenTerms' } as const, [] as string[])
// 대화 시작 기준 — 한 번 잡으면 session.start 가 다시 불려도 바꾸지 않음. /clear·세션 안 재개는 새 대화이고 session.start 가 불리지 않으며
// atom 도 비워지므로 classic.SessionStart(source clear·resume)에서 새로 잡음
const baseline = atom({ plugin: 'project-board', key: 'baseline' } as const, null as Baseline | null)
const gitNow = atom({ plugin: 'project-board', key: 'git' } as const, null as GitNow | null)
// /project-board off 로 닫은 상태 — 이번 세션만(다시 열기 전까지 자동으로 열지 않음)
const isOff = atom({ plugin: 'project-board', key: 'isOff' } as const, false)

const kUsage = '사용법: /project-board [on|off] — 인자 없이 또는 on 이면 다시 읽고 패널 열기, off 면 패널 닫기(이번 세션만)'

const kSetupGuide = [
  `### 설정 파일이 없음`,
  `작업 폴더의 \`${kConfigPath}\` 에 무엇을 읽을지 적으면 패널이 채워집니다. 예:`,
  '```json',
  '{',
  '  "title": "My Project",',
  '  "roadmap": { "file": "docs/roadmap.json", "format": "json" },',
  '  "decisions": [',
  '    { "file": "docs/decisions.md", "label": "결정 기록", "format": "md-table", "idPrefix": "DR", "kind": "past" },',
  '    { "file": "docs/questions.md", "label": "미결", "format": "md-table", "idPrefix": "Q", "kind": "classify",',
  '      "decided": "확정|해소", "pending": "결정 필요" }',
  '  ],',
  '  "glossary": [{ "term": "SSH", "meaning": "원격 접속 규약", "match": ["SSH"] }]',
  '}',
  '```',
  '로드맵 JSON 은 `{ tracks: [{key,name}], items: [{id, track, parent, title, deps, status}] }` 형식(상태 기본값 완료·진행·대기·보류·결정 필요).',
].join('\n')

// 엔진 시계($.clock)를 로컬 시각 문자열로 — 시험에서 mock.clock 으로 고정할 수 있음
async function now($: EngineInterface): Promise<string> {
  return formatLocalTime(new Date(await $.clock.now()))
}

async function readOrNull($: EngineInterface, path: string): Promise<string | null> {
  try {
    return (await $.fs.read(path)) as string
  } catch {
    return null
  }
}

async function reloadBoard($: EngineInterface, loadedAt: string): Promise<void> {
  try {
    const raw = await readOrNull($, kConfigPath)
    if (raw === null) {
      await update($, data, () => null)
      return
    }
    const config = JSON.parse(raw) as unknown
    const errors = validateConfig(config)
    if (errors.length) {
      throw new Error(`${kConfigPath}: ${errors.join('; ')}`)
    }
    const title = folderTitle(await $.session.cwd())
    const board = await buildBoard(config as BoardConfig, p => readOrNull($, p), kDefaultGlossary, loadedAt, title)
    await update($, data, () => board)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    await update($, data, prev => ({ ...(prev ?? emptyBoard(loadedAt)), loadedAt, error: message }))
  }
}

async function reloadGit($: EngineInterface): Promise<void> {
  const run: GitRun = async argv => $.process.run(argv, { env: { LC_ALL: 'C' }, timeoutMs: 20000 })
  const base = await read($, baseline)
  const since = base?.git.kind === 'ok' ? { head: base.git.head } : null
  const now = await readGit(run, since)
  await update($, gitNow, () => now)
}

async function reload($: EngineInterface): Promise<void> {
  await reloadBoard($, await now($))
  // 이 플러그인은 전역 활성이라 설정 파일이 없는 저장소와 패널을 끈 상태에서는 git 을 실행하지 않음.
  // 끈 동안의 커밋은 다시 열 때 기준 HEAD 와 비교해 읽으므로 변경 탭에서 빠지지 않음
  if ((await read($, data)) !== null && !(await read($, isOff))) {
    await reloadGit($)
  }
}

// 세션 시작 기준 — 이미 있으면 그대로 둠
async function captureBaseline($: EngineInterface): Promise<void> {
  const board = await read($, data)
  const git = await read($, gitNow)
  const at = await now($)
  const unread: GitSnap = { kind: 'error', message: 'git 을 읽지 않음(설정 파일이 없거나 패널을 끈 상태)' }
  await update($, baseline, prev => prev ?? takeBaseline(board, git?.snap ?? unread, at))
}

function emptyBoard(loadedAt: string): BoardData {
  return {
    title: kDefaultTitle, asOf: '-', currentStage: '-', tracks: [], stages: [], doing: [], nextUp: [],
    recent: [], past: [], pending: [], unclassified: [], glossary: [], sources: [], loadedAt, warnings: [], items: [], sourceRows: {},
  }
}

function statusMarkdown(b: BoardData): string {
  if (!b.tracks.length && !b.stages.length) {
    return '_로드맵이 설정되지 않았거나 읽지 못함 (`roadmap` 항목 확인)_'
  }
  const trackRows = b.tracks
    .map(t => `| ${cell(t.name)} | ${t.done}/${t.total} (${t.total ? Math.round((t.done * 100) / t.total) : 0}%) | ${cell(t.doing.join(' · ') || '—')} |`)
    .join('\n')
  const stageRows = b.stages
    .map(s => `| ${s.isCurrent ? '▶ ' : ''}${s.id} | ${cell(s.title)} | ${s.isCurrent ? `**${s.status}**` : s.status} |`)
    .join('\n')
  return [
    `### 현재 단계\n**${cell(b.currentStage)}**`,
    `- 진행 중: ${b.doing.join(' · ') || '없음'}`,
    `- 다음 착수 가능: ${b.nextUp.join(' · ') || '없음'}`,
    `\n### 트랙별 진행률 (기준 ${b.asOf})\n| 트랙 | 완료 | 진행 중 |\n|---|---|---|\n${trackRows}`,
    `\n### 전체 단계\n| ID | 내용 | 상태 |\n|---|---|---|\n${stageRows}`,
  ].join('\n')
}

function termsMarkdown(glossary: Term[], seen: string[]): string {
  const byTerm = new Map(glossary.map(t => [t.term, t]))
  const recent = seen.map(s => byTerm.get(s)).filter((t): t is Term => t !== undefined)
  const rest = glossary.filter(t => !seen.includes(t.term))
  const table = (list: Term[]) =>
    `| 용어 | 뜻 |\n|---|---|\n${list.map(t => `| **${cell(t.term)}** | ${cell(t.meaning)} |`).join('\n')}`
  return [
    '### 이번 대화에 나온 용어',
    recent.length ? table(recent) : '_아직 없음 — 답변이 끝날 때마다 갱신_',
    '\n### 전체 용어',
    rest.length ? table(rest) : '_없음_',
  ].join('\n')
}

function decisionTable(list: DecisionRow[]): string {
  if (!list.length) {
    return '_없음_'
  }
  return `| ID | 내용 | 결정·권고 | 출처 |\n|---|---|---|---|\n${list
    .map(d => `| ${cell(d.id)} | ${cell(d.topic)} | ${cell(d.detail)} | ${cell(d.source)} |`)
    .join('\n')}`
}

function decisionsMarkdown(b: BoardData): string {
  return [
    `### 현재 결정된 내용 (${b.recent.length})`,
    decisionTable(b.recent),
    `\n### 앞으로 결정해야 할 내용 (${b.pending.length})`,
    decisionTable(b.pending),
    `\n### 지난 결정 (${b.past.length})`,
    decisionTable(b.past),
  ].join('\n')
}

async function openPane($: EngineInterface): Promise<void> {
  const board = await read($, data)
  await $.ui.open({ id: kPane, title: board?.title ?? folderTitle(await $.session.cwd()) })
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'project-board',
      description: '프로젝트 현황판(개발 현황·용어·결정·변경) 패널 열기/닫기',
      argumentHint: '[on|off]',
    })
    await reload($)
    await captureBaseline($)
    // 설정 파일이 있는 프로젝트에서만 저절로 연다. off 로 닫았으면 플러그인이 다시 로드돼도 열지 않음
    if ((await read($, data)) && !(await read($, isOff))) {
      void openPane($)
    }
    return next(e)
  })

  // /clear 와 세션 안 재개는 같은 프로세스에서 새 대화가 시작됨: session.start 는 불리지 않고 atom 은 비워짐
  // (기준·용어가 사라지고 설정 파일도 없는 것처럼 보임). 새 대화 시작 시점을 기준으로 다시 잡음.
  // 패널이 열려 있었는지는 UI 가 들고 있어 건드리지 않음(끈 상태도 그대로 닫힌 채)
  on('classic.SessionStart', async ($, e, next) => {
    if (e.source === 'clear' || e.source === 'resume') {
      await update($, baseline, () => null)
      await update($, seenTerms, () => [])
      await reload($)
      await captureBaseline($)
    }
    return next(e)
  })

  on('command.run', { command: 'project-board' }, async ($, e) => {
    const action = parseBoardCommand(e.args)
    if (action === null) {
      return { text: kUsage }
    }
    if (action === 'off') {
      await update($, isOff, () => true)
      try {
        await $.ui.close({ id: kPane })
      } catch (err) {
        return { text: `패널을 닫지 못했습니다: ${err instanceof Error ? err.message : String(err)}` }
      }
      return { text: '패널을 닫았습니다. 이번 세션에서는 /project-board 로 다시 열 수 있고, 다음 세션에서는 자동으로 열립니다.' }
    }
    await update($, isOff, () => false)
    await reload($)
    await openPane($)
    const board = await read($, data)
    return { text: board ? `${board.title} 패널을 열었습니다.` : `${kConfigPath} 가 없어 설정 안내를 표시했습니다.` }
  })

  // 답변이 끝날 때마다 문서를 다시 읽고(상태·결정이 바뀌었을 수 있음) 답변에 나온 용어를 모은다
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (!e.agentId) {
      await reload($)
      const board = await read($, data)
      const found = findTerms(e.answer ?? '', board?.glossary ?? kDefaultGlossary)
      if (found.length) {
        await update($, seenTerms, prev => mergeSeen(prev, found))
      }
    }
    return result
  })

  on('ui.render', { component: 'Pane', requestId: kPane }, async ($, e) => {
    const { Box, Text, Button, Markdown } = $.ui.resolve(e)
    const current = await read($, tab)
    const board = await read($, data)
    const seen = await read($, seenTerms)
    const tabs: { key: BoardTab; label: string; hotkey: string }[] = [
      { key: 'status', label: '개발 현황', hotkey: '1' },
      { key: 'terms', label: '용어', hotkey: '2' },
      { key: 'decisions', label: '결정', hotkey: '3' },
      { key: 'changes', label: '변경', hotkey: '4' },
    ]
    let body = kSetupGuide
    if (current === 'changes') {
      body = changesMarkdown(await read($, baseline), board, await read($, gitNow))
    } else if (board) {
      if (current === 'status') {
        body = statusMarkdown(board)
      } else if (current === 'terms') {
        body = termsMarkdown(board.glossary, seen)
      } else {
        body = decisionsMarkdown(board)
      }
    }
    return (
      <Box flexDirection="column">
        <Box flexDirection="row" gap={1}>
          {tabs.map(t => (
            <Button
              key={`tab-${t.key}`}
              label={t.label}
              hotkey={t.hotkey}
              variant={t.key === current ? 'primary' : 'secondary'}
              onPress={() => update($, tab, () => t.key)}
            />
          ))}
          <Button key="refresh" label="새로고침" hotkey="r" onPress={() => reload($)} />
        </Box>
        {board?.error && <Text color="red">읽기 실패: {board.error}</Text>}
        {(board?.warnings ?? []).map(w => (
          <Text color="yellow">주의: {w}</Text>
        ))}
        <Text dimColor>
          갱신 {board?.loadedAt ?? '-'} · 출처 {board?.sources.join(', ') || kConfigPath}
        </Text>
        <Markdown key="body" text={body} />
      </Box>
    )
  })
}
