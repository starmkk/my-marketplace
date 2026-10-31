import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { BoardData, BoardTab, DecisionRow, Term } from '../types'
import { kDefaultGlossary, findTerms, mergeSeen } from './glossary'
import { buildBoard, cell, kConfigPath, validateConfig } from './parse'
import type { BoardConfig } from './parse'

const kPane = 'project-board'

const tab = atom({ plugin: 'project-board', key: 'tab' } as const, 'status' as BoardTab)
const data = atom({ plugin: 'project-board', key: 'data' } as const, null as BoardData | null)
const seenTerms = atom({ plugin: 'project-board', key: 'seenTerms' } as const, [] as string[])

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

function now(): string {
  return new Date().toISOString().slice(0, 16).replace('T', ' ')
}

async function readOrNull($: EngineInterface, path: string): Promise<string | null> {
  try {
    return (await $.fs.read(path)) as string
  } catch {
    return null
  }
}

async function reload($: EngineInterface): Promise<void> {
  const loadedAt = now()
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
    const board = await buildBoard(config as BoardConfig, p => readOrNull($, p), kDefaultGlossary, loadedAt)
    await update($, data, () => board)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    await update($, data, prev => ({ ...(prev ?? emptyBoard(loadedAt)), loadedAt, error: message }))
  }
}

function emptyBoard(loadedAt: string): BoardData {
  return {
    title: 'Project Board', asOf: '-', currentStage: '-', tracks: [], stages: [], doing: [], nextUp: [],
    recent: [], past: [], pending: [], glossary: [], sources: [], loadedAt, warnings: [],
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
  await $.ui.open({ id: kPane, title: board?.title ?? 'Project Board' })
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'project-board',
      description: '프로젝트 현황판(개발 현황·용어·결정) 패널 열기',
    })
    await reload($)
    // 설정 파일이 있는 프로젝트에서만 저절로 연다
    if (await read($, data)) {
      void openPane($)
    }
    return next(e)
  })

  on('command.run', { command: 'project-board' }, async $ => {
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
    ]
    let body = kSetupGuide
    if (board) {
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
