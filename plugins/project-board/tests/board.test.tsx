import { describe, expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On } from 'claude-code'

import { findTerms, kDefaultGlossary, mergeSeen } from '../hooks/glossary'
import { buildBoard, folderTitle, formatLocalTime, isClosedByPerson, mergeGlossary, parseBoardCommand, parseDecisions, plainText, tableRows, validateConfig } from '../hooks/parse'
import type { BoardConfig, DecisionSource } from '../hooks/parse'

const kRoadmap = {
  as_of: '2026-10-31',
  tracks: [{ key: 'core', name: '코어' }, { key: 'app', name: '앱' }],
  items: [
    { id: 'C-A', track: 'core', parent: null, title: '계획 A', deps: [], status: '완료' },
    { id: 'C-B', track: 'core', parent: null, title: '정리', deps: [], status: '대기' },
    { id: 'M0', track: 'app', parent: null, title: 'M0 골격', deps: [], status: '대기' },
    { id: 'A-00', track: 'app', parent: 'M0', title: '프로젝트', deps: [], status: '대기' },
    { id: 'M1', track: 'app', parent: null, title: 'M1 접속', deps: ['M0'], status: '대기' },
  ],
}
const kHtml = [
  `<script type="application/json" id="roadmap-data">${JSON.stringify(kRoadmap)}</script>`,
  '<tr><td>Q-01</td><td>미결 질문</td><td>영향</td><td>권고 <span class="badge b-dec">결정 필요</span></td></tr>',
  '<tr><td>Q-16</td><td>해소된 질문</td><td>영향</td><td><span class="badge b-fix">해소</span> 끝남</td></tr>',
  '<tr><td>Q-17</td><td>기록만</td><td>영향</td><td>참고</td></tr>',
  '<tr><td>DR-01</td><td>서명 위치</td><td>미들웨어</td><td>앱</td><td>이유</td></tr>',
].join('\n')
const kPlan = [
  '| ID | 내용 | 막히는 것 | 권고 |',
  '|---|---|---|---|',
  '| U-1 | Xcode 버전 | A-00 | **결정 2026-10-31**: 27.2 로 진행 |',
  '| U-3 | 글꼴 a \\| b | A-05 | 커밋 |',
].join('\n')
const kQ: DecisionSource = {
  file: 'design.html', label: '설계 10절', format: 'html-table', idPrefix: 'Q', kind: 'classify',
  decided: 'badge b-fix">(확정|해소)', pending: 'badge b-dec"',
}
const kConfig: BoardConfig = {
  title: '시험 보드',
  roadmap: { file: 'design.html', format: 'html-script', id: 'roadmap-data', stageTracks: ['app'] },
  decisions: [
    kQ,
    { file: 'design.html', label: '설계 11절', format: 'html-table', idPrefix: 'DR', kind: 'past', detailColumn: 2 },
    { file: 'plan.md', label: '계획', format: 'md-table', idPrefix: 'U', kind: 'classify', decided: '^\\*\\*결정 \\d{4}-\\d{2}-\\d{2}\\*\\*' },
  ],
  glossary: [{ term: 'SSH', meaning: '원격 접속 규약', match: ['SSH'] }],
}
const kFiles: Record<string, string> = { 'design.html': kHtml, 'plan.md': kPlan }
const readFake = async (p: string) => kFiles[p] ?? null

describe('roadmap', () => {
  test('현재 단계는 stageTracks 안에서 착수 가능한 첫 상위 항목', async () => {
    const b = await buildBoard(kConfig, readFake, [], 't')
    expect(b.currentStage.startsWith('M0 착수 가능')).toBe(true)
    expect(b.stages.find(s => s.id === 'M1')?.isCurrent).toBe(false)
    expect(b.stages.some(s => s.id === 'A-00')).toBe(false)
  })
  test('stageTracks 가 없으면 전체 트랙에서 고름(C-B 가 먼저)', async () => {
    const b = await buildBoard({ ...kConfig, roadmap: { file: 'design.html', format: 'html-script', id: 'roadmap-data' } }, readFake, [], 't')
    expect(b.currentStage.startsWith('C-B')).toBe(true)
  })
  test('진행률은 말단 항목 기준', async () => {
    const b = await buildBoard(kConfig, readFake, [], 't')
    expect(b.tracks[0]).toEqual({ name: '코어', done: 1, total: 2, doing: [] })
    expect(b.tracks[1]?.total).toBe(2)
  })
  test('상태 이름을 바꾼 프로젝트도 읽음(json 형식)', async () => {
    const en = { tracks: kRoadmap.tracks, items: kRoadmap.items.map(i => ({ ...i, status: i.status === '완료' ? 'done' : 'todo' })) }
    const cfg: BoardConfig = { roadmap: { file: 'r.json', format: 'json', statuses: { done: 'done', waiting: 'todo' }, stageTracks: ['app'] } }
    const b = await buildBoard(cfg, async () => JSON.stringify(en), [], 't')
    expect(b.tracks[0]?.done).toBe(1)
    expect(b.currentStage.startsWith('M0')).toBe(true)
  })
  test('파일이 없거나 script 가 없으면 경고만 남기고 계속', async () => {
    const b = await buildBoard(kConfig, async p => (p === 'plan.md' ? kPlan : null), [], 't')
    expect(b.warnings).toContain('design.html 없음')
    expect(b.recent.map(r => r.id)).toEqual(['U-1'])
    const b2 = await buildBoard(kConfig, async p => (p === 'design.html' ? '<p>x</p>' : null), [], 't')
    expect(b2.warnings.some(w => w.includes('roadmap-data'))).toBe(true)
  })
})

describe('title', () => {
  test('folderTitle 은 경로의 마지막 폴더 이름(끝 구분자·윈도 경로 포함)', async () => {
    expect(folderTitle('/Users/me/work/poketshell')).toBe('poketshell')
    expect(folderTitle('/Users/me/work/my-app/')).toBe('my-app')
    expect(folderTitle('C:\\work\\demo')).toBe('demo')
  })
  test('folderTitle 은 빈 경로·루트에서 기본값', async () => {
    expect(folderTitle('')).toBe('Project Board')
    expect(folderTitle('/')).toBe('Project Board')
  })
  test('설정에 title 이 없으면 폴더 이름, 있으면 title', async () => {
    const { title, ...rest } = kConfig
    expect(title).toBe('시험 보드')
    expect((await buildBoard(rest, readFake, [], 't', 'my-app')).title).toBe('my-app')
    expect((await buildBoard(kConfig, readFake, [], 't', 'my-app')).title).toBe('시험 보드')
  })
})

describe('decisions', () => {
  test('html 표: 확정·해소 / 결정 필요로 나뉘고 기록만인 행은 빠짐', async () => {
    const d = parseDecisions(kHtml, kQ)
    expect(d.decided.map(r => r.id)).toEqual(['Q-16'])
    expect(d.pending.map(r => r.id)).toEqual(['Q-01'])
  })
  test('md 표: 결정 표식으로 나뉘고 이스케이프된 | 는 칸을 나누지 않음', async () => {
    const d = parseDecisions(kPlan, kConfig.decisions![2]!)
    expect(d.decided.map(r => r.id)).toEqual(['U-1'])
    expect(d.pending[0]?.topic).toBe('글꼴 a \\| b')
  })
  test('past 는 모든 행, detailColumn 으로 칸을 고름', async () => {
    const b = await buildBoard(kConfig, readFake, [], 't')
    expect(b.past).toEqual([{ id: 'DR-01', topic: '서명 위치', detail: '미들웨어', source: '설계 11절', sig: 'DR-01\0서명 위치\0미들웨어\0앱\0이유' }])
  })
  test('sig 는 표시값이 잘리거나 쓰이지 않는 칸까지 행 전체 — 뒷부분·중간 칸 변경이 달라짐', () => {
    const src: DecisionSource = { file: 'd.md', label: 'D', format: 'md-table', idPrefix: 'D', kind: 'past' }
    const tail = 'x'.repeat(200)
    const sigOf = (text: string) => parseDecisions(text, src).past[0]!
    const a = sigOf(`| D-1 | 주제 | 중간A | ${tail}A |`)
    const b = sigOf(`| D-1 | 주제 | 중간A | ${tail}B |`)
    const c = sigOf(`| D-1 | 주제 | 중간B | ${tail}A |`)
    expect(a.detail).toBe(b.detail) // 표시값은 잘려 같음
    expect(new Set([a.sig, b.sig, c.sig]).size).toBe(3)
  })
  test('분류 규칙 밖의 행은 other 로 따로 모음 (기록만인 행)', () => {
    const d = parseDecisions(kHtml, kQ)
    expect(d.other.map(r => r.id)).toEqual(['Q-17'])
  })
  test('소스별 행 수를 기록 — 분류에서 빠진 행도 셈', async () => {
    const b = await buildBoard(kConfig, readFake, [], 't')
    expect(b.sourceRows).toEqual({ '로드맵 design.html': 5, '설계 10절 (design.html)': 3, '설계 11절 (design.html)': 1, '계획 (plan.md)': 2 })
    expect(b.unclassified.map(r => r.id)).toEqual(['Q-17'])
  })
  test('행 경계를 넘지 않음 — ID 없는 행 사이의 셀을 섞지 않음', async () => {
    const html = '<tr><td>Q-01</td><td>a</td></tr><tr><td>x</td><td>b</td></tr>'
    expect(tableRows(html, { format: 'html-table', idPrefix: 'Q' })).toEqual([['Q-01', 'a']])
  })
})

describe('config', () => {
  test('정상 설정은 오류 없음', async () => {
    expect(validateConfig(kConfig)).toEqual([])
  })
  test('잘못된 형식·정규식·필수값을 문장으로 알림', async () => {
    const errs = validateConfig({ roadmap: { file: 1, format: 'xml' }, decisions: [{ kind: 'classify', decided: '(' }] })
    expect(errs.length).toBeGreaterThan(3)
    expect(validateConfig([])).toEqual(['설정은 JSON 객체여야 함'])
  })
})

describe('glossary', () => {
  test('프로젝트 용어가 같은 이름의 기본 용어를 덮어씀', async () => {
    const merged = mergeGlossary(kDefaultGlossary, [{ term: 'TDD', meaning: '바꾼 뜻', match: ['TDD'] }])
    expect(merged.filter(t => t.term === 'TDD').map(t => t.meaning)).toEqual(['바꾼 뜻'])
  })
  test('영문은 단어 경계로, 한글은 포함으로 찾음', async () => {
    const g = [...kDefaultGlossary, { term: 'Esc', meaning: '키', match: ['Esc'] }]
    const found = findTerms('워크트리에서 lint 를 돌림. escape 는 아님', g)
    expect(found).toContain('git worktree')
    expect(found).toContain('lint(린트)')
    expect(found).not.toContain('Esc')
  })
  test('mergeSeen 은 새 용어를 앞에 두고 중복을 없앰', async () => {
    expect(mergeSeen(['a', 'b'], ['b', 'c'])).toEqual(['b', 'c', 'a'])
  })
  test('plainText 는 태그를 벗기고 엔티티를 풂', async () => {
    expect(plainText('<code>a&lt;b</code> &amp; c')).toBe('a<b & c')
  })
})

test('패널에 탭 4개와 새로고침이 그려지고 설정이 없으면 안내를 보임', async $ => {
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'project-board', surface, component: 'Pane', requestId: 'project-board',
      props: { title: 'Project Board', isFocused: false, bodyColumns: 60, placement: 'dock', scroll: { offset: 0, bodyRows: 20 }, view: {} },
    })
    for (const key of ['tab-status', 'tab-terms', 'tab-decisions', 'tab-changes', 'refresh']) {
      expect(await ui.find({ key })).toBeDefined()
    }
    await ui.press({ key: 'tab-terms' })
    await ui.unmount()
  }
})

describe('시각 표시', () => {
  test('로컬 시각을 자리 맞춰 YYYY-MM-DD HH:mm 으로 만듦 (TZ 와 무관)', () => {
    expect(formatLocalTime(new Date(2026, 0, 5, 3, 7))).toBe('2026-01-05 03:07')
    expect(formatLocalTime(new Date(2026, 10, 2, 13, 0))).toBe('2026-11-02 13:00')
    expect(formatLocalTime(new Date(2026, 11, 31, 23, 59))).toBe('2026-12-31 23:59')
  })
  test('절대 시각(UTC 04:00)은 실행 TZ 의 로컬 시각으로 — Seoul 에서 13:00, UTC 에서 04:00', () => {
    const d = new Date('2026-11-02T04:00:00Z')
    // 실행 TZ 를 getTimezoneOffset(분, UTC 보다 앞서면 음수)으로 알아냄: Seoul = -540, UTC = 0
    const offset = d.getTimezoneOffset()
    if (offset === -540) {
      expect(formatLocalTime(d)).toBe('2026-11-02 13:00')
    } else if (offset === 0) {
      expect(formatLocalTime(d)).toBe('2026-11-02 04:00')
    } else {
      expect(formatLocalTime(d)).toMatch(/^2026-11-0[123] \d\d:00$/)
    }
  })
})

describe('명령 인자', () => {
  test('빈 인자·on 은 열기, off 는 닫기, 대소문자·앞뒤 공백 허용', () => {
    expect(parseBoardCommand('')).toBe('on')
    expect(parseBoardCommand('  ')).toBe('on')
    expect(parseBoardCommand('on')).toBe('on')
    expect(parseBoardCommand(' ON ')).toBe('on')
    expect(parseBoardCommand('off')).toBe('off')
    expect(parseBoardCommand('\tOff\n')).toBe('off')
  })
  test('그 밖의 인자는 null (패널을 건드리지 않음)', () => {
    for (const a of ['of', 'off now', 'on off', 'close', '1', '--off']) {
      expect(parseBoardCommand(a)).toBeNull()
    }
  })
})

// ---- 엔진 통합: 세션 시작·명령·turn.complete ----

const kCfg = JSON.stringify({ title: '통합', roadmap: { file: 'design.html', format: 'html-script', id: 'roadmap-data' } })

function world(on: On, opts: { nowMs?: number; closeError?: string; statError?: boolean; panes?: string[]; afterStat?: (path: string, files: Record<string, string>) => void; files?: Record<string, string>; git?: (argv: readonly string[]) => { exitCode?: number; stdout?: string; stderr?: string } } = {}) {
  const log = { opens: [] as string[], closes: [] as string[], gitCalls: [] as string[], gitInits: [] as unknown[], reads: [] as string[], toasts: [] as string[] }
  const clock = mock.clock(on, { now: opts.nowMs ?? Date.now() })
  const files: Record<string, string> = { '.claude/project-board.json': kCfg, 'design.html': kHtml, ...opts.files }
  on('session.cwd', async () => ({ value: '/work/demo' }))
  on('session.start', async (_$, e) => ({ cwd: e.cwd }))
  on('classic.SessionStart', async () => ({}))
  on('turn.complete', async () => ({ text: '' }))
  on('command.register', async () => ({ value: { name: 'project-board' } }) as never)
  const fileOf = (path: string) => Object.keys(files).find(k => path.endsWith(`/${k}`) || path === k)
  on('fs.stat', async (_$, e) => {
    const name = fileOf(e.path)
    const text = name === undefined ? undefined : files[name]
    if (opts.statError || text === undefined) {
      return { deny: `ENOENT ${e.path}` } as never
    }
    // 내용이 바뀌면 지문도 바뀌게 — 길이가 같은 수정('대기'→'완료')도 잡도록 내용 해시를 mtime 으로 씀
    let hash = 0
    for (const ch of text) {
      hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
    }
    opts.afterStat?.(e.path, files)
    return { value: { kind: 'file', size: text.length, mtimeMs: hash, isLink: false } } as never
  })
  // 엔진 자리의 그리기: footer 는 받은 modes 를 그대로, 밴드는 엔진 몫 한 줄
  on('ui.render', { component: 'SessionMode' }, async ($$, e) => {
    const { Text } = $$.ui.resolve(e)
    return <Text key="modes">{e.props.modes.join(' | ')}</Text>
  })
  on('ui.render', { component: 'AbovePrompt' }, async ($$, e) => {
    const { Text } = $$.ui.resolve(e)
    return <Text key="engine-band">engine</Text>
  })
  on('ui.panes', async () => ({ value: (opts.panes ?? []).map(id => ({ id, title: id, isShown: true, isFocused: false, isPlaced: true })) }) as never)
  on('ui.toast', async (_$, e) => {
    log.toasts.push(e.text)
    return { value: undefined } as never
  })
  on('fs.read', async (_$, e) => {
    log.reads.push(e.path)
    // 엔진이 상대 경로를 절대 경로로 풀어 넘김
    const name = fileOf(e.path)
    const text = name === undefined ? undefined : files[name]
    if (text === undefined) {
      return { deny: `ENOENT ${e.path}` } as never
    }
    return { value: text } as never
  })
  on('ui.open', async (_$, e) => {
    log.opens.push(e.id)
    return { value: { isPlaced: true } } as never
  })
  on('ui.close', async (_$, e) => {
    log.closes.push(e.id)
    return (opts.closeError ? { deny: opts.closeError } : { value: undefined }) as never
  })
  on('process.run', async (_$, e) => {
    log.gitCalls.push(e.argv.join(' '))
    log.gitInits.push(e.init)
    const r = opts.git ? opts.git(e.argv) : { exitCode: 128, stderr: 'fatal: not a git repository' }
    return { value: { exitCode: 0, stdout: '', stderr: '', ...r } } as never
  })
  return { log, files, clock }
}
const kStart = { cwd: '/work/demo', surface: 'terminal', isInteractive: true } as const
const run = ($: Engine, args = '') =>
  $.command.run({ command: 'project-board', args, origin: { kind: 'composer' }, presentation: { isFullscreen: true, columns: 160 } })
const kDone = { answer: '', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' } as const

describe('엔진 통합', () => {
  test('세션 시작에 패널이 열리고 /project-board 와 on 은 다시 읽고 열기', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    expect(w.log.opens.length).toBe(1)
    const r1 = await run($)
    const r2 = await run($, ' ON ')
    expect(w.log.opens.length).toBe(3)
    expect(r1.text).toContain('열었습니다')
    expect(r2.text).toContain('열었습니다')
  })
  test('off 는 패널을 닫고, 이미 닫힌 상태의 off 도 오류가 없음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    const r = await run($, 'off')
    expect(w.log.closes).toEqual(['project-board'])
    expect(r.text).toContain('닫았습니다')
    const again = await run($, 'OFF ')
    expect(w.log.closes.length).toBe(2)
    expect(again.text).toContain('닫았습니다')
  })
  test('close 가 거부돼도 off 는 던지지 않고 사유를 알림', async ($, on) => {
    const w = world(on, { closeError: '거부됨' })
    await $.session.start(kStart)
    const r = await run($, 'off')
    expect(r.text).toContain('거부됨')
    expect(w.log.opens.length).toBe(1)
  })
  test('알 수 없는 인자는 패널을 열지도 닫지도 않고 사용법을 알림', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    const opensBefore = w.log.opens.length
    const r = await run($, 'close')
    expect(w.log.opens.length).toBe(opensBefore)
    expect(w.log.closes).toEqual([])
    expect(r.text).toContain('사용법')
  })
  test('off 뒤 turn.complete 와 세션 시작 재호출(플러그인 리로드)이 패널을 다시 열지 않음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    await run($, 'off')
    const opens = w.log.opens.length
    await $.turn.complete({ ...kDone })
    await $.session.start(kStart)
    expect(w.log.opens.length).toBe(opens)
    await run($, 'on')
    expect(w.log.opens.length).toBe(opens + 1)
    await $.session.start(kStart)
    expect(w.log.opens.length).toBe(opens + 2)
  })
  test('기준은 첫 session.start 에서만 잡고, 다시 불려도 리셋되지 않음 — 변경 탭에 이전 기준 시각과 변화가 남음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    const roadmap = JSON.parse(kHtml.match(/>(\{.*\})<\/script>/)![1]!)
    roadmap.items[1].status = '완료'
    w.files['design.html'] = kHtml.replace(/>\{.*\}<\/script>/, `>${JSON.stringify(roadmap)}</script>`)
    await $.turn.complete({ ...kDone })
    await $.session.start(kStart)
    const ui = await $.ui.mount({
      plugin: 'project-board', surface: 'terminal', component: 'Pane', requestId: 'project-board',
      props: { title: 't', isFocused: false, bodyColumns: 80, placement: 'dock', scroll: { offset: 0, bodyRows: 20 }, view: {} },
    })
    await ui.press({ key: 'tab-changes' })
    const md = (await ui.find({ type: 'Markdown' }))?.text ?? ''
    expect(md).toContain('대기 → 완료')
    expect(md).toContain('C-B')
    await ui.unmount()
  })
  test('git 저장소가 아니면 변경 탭에 해당 없음, 변경 탭 갱신 중 git 실패는 오류로 보임', async ($, on) => {
    let broken = false
    const w = world(on, {
      git: () => {
        if (broken) {
          return { exitCode: 1, stderr: 'fatal: boom' }
        }
        return { exitCode: 128, stderr: 'fatal: not a git repository' }
      },
    })
    await $.session.start(kStart)
    const mountPane = async () => {
      const ui = await $.ui.mount({
        plugin: 'project-board', surface: 'terminal', component: 'Pane', requestId: 'project-board',
        props: { title: 't', isFocused: false, bodyColumns: 80, placement: 'dock', scroll: { offset: 0, bodyRows: 20 }, view: {} },
      })
      await ui.press({ key: 'tab-changes' })
      return ui
    }
    let ui = await mountPane()
    expect((await ui.find({ type: 'Markdown' }))?.text).toContain('해당 없음')
    await ui.unmount()
    expect(w.log.gitCalls.length).toBeGreaterThan(0)
    broken = true
    await $.turn.complete({ ...kDone })
    ui = await mountPane()
    expect((await ui.find({ type: 'Markdown' }))?.text).toContain('git')
    await ui.unmount()
  })
  test('하위 에이전트 턴은 다시 읽지 않음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    const before = w.log.gitCalls.length
    await $.turn.complete({ ...kDone, agentId: 'sub-1' })
    expect(w.log.gitCalls.length).toBe(before)
    await $.turn.complete({ ...kDone })
    expect(w.log.gitCalls.length).toBeGreaterThan(before)
  })

  const kPaneProps = { title: 't', isFocused: false, bodyColumns: 80, placement: 'dock', scroll: { offset: 0, bodyRows: 20 }, view: {} } as const
  const mount = ($: Engine) =>
    $.ui.mount({ plugin: 'project-board', surface: 'terminal', component: 'Pane', requestId: 'project-board', props: kPaneProps })
  const kStatusKey = (argv: readonly string[]) =>
    argv.filter(a => !['--no-optional-locks', '-c', 'core.quotepath=false'].includes(a)).slice(1).join(' ')
  // HEAD 와 log 를 시험이 바꿀 수 있는 모의 저장소
  const repo = (state: { head: string; log: string; ancestor: number }) => (argv: readonly string[]) => {
    const k = kStatusKey(argv)
    if (k.startsWith('rev-parse --is-inside')) {
      return { stdout: 'true\n' }
    }
    if (k.startsWith('rev-parse --verify')) {
      return { stdout: `${state.head}\n` }
    }
    if (k.startsWith('status')) {
      return { stdout: '' }
    }
    if (k.startsWith('merge-base')) {
      return { exitCode: state.ancestor }
    }
    if (k.startsWith('log')) {
      return { stdout: state.log }
    }
    return { exitCode: 1, stderr: `unexpected ${k}` }
  }

  test('패널 갱신 시각과 변경 탭 기준 시각은 엔진 시계($.clock)를 로컬(TZ) 시각으로 바꾼 값 — UTC 문자열이 아님', async ($, on) => {
    const fixed = new Date('2026-11-01T19:00:00Z')
    world(on, { nowMs: fixed.getTime() })
    await $.session.start(kStart)
    const local = formatLocalTime(fixed)
    const utc = fixed.toISOString().slice(0, 16).replace('T', ' ')
    const ui = await mount($)
    const header = (await ui.findAll({ type: 'Text', text: /갱신/ }))[0]?.text ?? ''
    expect(header).toContain(`갱신 ${local} ·`)
    await ui.press({ key: 'tab-changes' })
    const md = (await ui.find({ type: 'Markdown' }))?.text ?? ''
    expect(md).toContain(`기준: 이 대화 시작 ${local}`)
    if (local !== utc) {
      // 실행 TZ 가 UTC 가 아니면 UTC 문자열이 새어 나오지 않았음을 직접 확인(Seoul: 04:00 이 아니라 19:00)
      expect(header).not.toContain(`갱신 ${utc} ·`)
    }
    await ui.unmount()
  })
  test('turn.complete 가 기준 HEAD 이후의 새 커밋을 변경 탭에 보임', async ($, on) => {
    const state = { head: 'aaa1111', log: '', ancestor: 0 }
    world(on, { git: repo(state) })
    await $.session.start(kStart)
    state.head = 'bbb2222'
    state.log = 'bbb2222 새 커밋 | 파이프\0'
    await $.turn.complete({ ...kDone })
    const ui = await mount($)
    await ui.press({ key: 'tab-changes' })
    const md = (await ui.find({ type: 'Markdown' }))?.text ?? ''
    expect(md).toContain('새 커밋 1개')
    expect(md).toContain('bbb2222 새 커밋 \\| 파이프')
    await ui.unmount()
  })
  test('기준 HEAD 가 조상이 아니면(브랜치 전환) 옛 커밋을 새 커밋으로 보이지 않고 HEAD 이동으로 알림', async ($, on) => {
    const state = { head: 'aaa1111', log: 'old0001 옛 커밋\0', ancestor: 1 }
    world(on, { git: repo(state) })
    await $.session.start(kStart)
    state.head = 'ccc3333'
    await $.turn.complete({ ...kDone })
    const ui = await mount($)
    await ui.press({ key: 'tab-changes' })
    const md = (await ui.find({ type: 'Markdown' }))?.text ?? ''
    expect(md).not.toContain('옛 커밋')
    expect(md).toContain('브랜치 전환')
    await ui.unmount()
  })
  test('git 은 LC_ALL=C 와 시간 제한으로 실행', async ($, on) => {
    const w = world(on, { git: repo({ head: 'aaa1111', log: '', ancestor: 0 }) })
    await $.session.start(kStart)
    expect(w.log.gitInits.length).toBeGreaterThan(0)
    for (const init of w.log.gitInits) {
      expect(init).toMatchObject({ env: { LC_ALL: 'C' }, timeoutMs: 20000 })
    }
  })
  for (const source of ['clear', 'resume'] as const) {
    test(`/clear·세션 안 재개(classic.SessionStart ${source})는 기준과 용어를 새로 잡음`, async ($, on) => {
      const w = world(on)
      await $.session.start(kStart)
      const roadmap = JSON.parse(kHtml.match(/>(\{.*\})<\/script>/)![1]!)
      roadmap.items[1].status = '완료'
      w.files['design.html'] = kHtml.replace(/>\{.*\}<\/script>/, `>${JSON.stringify(roadmap)}</script>`)
      await $.turn.complete({ ...kDone, answer: 'TDD 로 진행' })
      const panel = async (tabKey: string) => {
        const ui = await mount($)
        await ui.press({ key: tabKey })
        const text = (await ui.find({ type: 'Markdown' }))?.text ?? ''
        await ui.unmount()
        return text
      }
      // 사전 조건: 옛 기준에서는 변화와 이번 대화 용어가 보임
      expect(await panel('tab-changes')).toContain('대기 → 완료')
      expect(await panel('tab-terms')).not.toContain('아직 없음')
      await $.classic.SessionStart({ source })
      const changes = await panel('tab-changes')
      expect(changes).not.toContain('대기 → 완료')
      expect(changes).not.toContain('기준 없음')
      expect(changes).toContain('변화 없음')
      expect(await panel('tab-terms')).toContain('아직 없음')
    })
  }
  test('startup·compact 의 classic.SessionStart 는 기준을 건드리지 않음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    const roadmap = JSON.parse(kHtml.match(/>(\{.*\})<\/script>/)![1]!)
    roadmap.items[1].status = '완료'
    w.files['design.html'] = kHtml.replace(/>\{.*\}<\/script>/, `>${JSON.stringify(roadmap)}</script>`)
    await $.turn.complete({ ...kDone })
    for (const source of ['startup', 'compact'] as const) {
      await $.classic.SessionStart({ source })
    }
    const ui = await mount($)
    await ui.press({ key: 'tab-changes' })
    expect((await ui.find({ type: 'Markdown' }))?.text).toContain('대기 → 완료')
    await ui.unmount()
  })
  test('설정 파일이 없는 저장소와 off 상태에서는 turn.complete·session.start 가 git 을 실행하지 않음', async ($, on) => {
    const none = world(on, { git: repo({ head: 'aaa1111', log: '', ancestor: 0 }) })
    delete none.files['.claude/project-board.json']
    await $.session.start(kStart)
    await $.turn.complete({ ...kDone })
    expect(none.log.gitCalls).toEqual([])
  })
  test('off 중 turn.complete 는 git 을 실행하지 않고, on 으로 다시 열면 읽음', async ($, on) => {
    const state = { head: 'aaa1111', log: '', ancestor: 0 }
    const w = world(on, { git: repo(state) })
    await $.session.start(kStart)
    await run($, 'off')
    const before = w.log.gitCalls.length
    state.head = 'bbb2222'
    state.log = 'bbb2222 off 중 커밋\0'
    await $.turn.complete({ ...kDone })
    expect(w.log.gitCalls.length).toBe(before)
    await run($, 'on')
    expect(w.log.gitCalls.length).toBeGreaterThan(before)
    const ui = await mount($)
    await ui.press({ key: 'tab-changes' })
    expect((await ui.find({ type: 'Markdown' }))?.text).toContain('off 중 커밋')
    await ui.unmount()
  })
})

// ---- 1.0.3: 패널 밖 요약·사람이 닫기·변경 감지 생략·변화 알림 ----

describe('패널 밖 요약과 닫기 추적', () => {
  const footer = async ($: Engine) => {
    const ui = await $.ui.mount({ plugin: 'project-board', surface: 'terminal', component: 'SessionMode', props: { modes: ['plan'] } })
    const text = (await ui.find({ type: 'Text', text: /^plan/ }))?.text ?? ''
    await ui.unmount()
    return text
  }
  const kBandProps = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 100, scroll: { offset: 0, bodyRows: 10 }, view: {} }
  const band = async ($: Engine, props: Record<string, unknown> = {}) => {
    const ui = await $.ui.mount({ plugin: 'project-board', surface: 'terminal', component: 'AbovePrompt', props: { ...kBandProps, ...props } as never })
    const mine = (await ui.find({ type: 'Text', text: /^▦ / }))?.text
    const engine = (await ui.find({ type: 'Text', text: /^engine$/ }))?.text
    await ui.unmount()
    return { mine, engine }
  }

  test('사람이 닫은 것만 off 로 봄(plugin·unload·다른 패널은 아님)', () => {
    expect(isClosedByPerson({ id: 'project-board', origin: { kind: 'person' } }, 'project-board')).toBe(true)
    expect(isClosedByPerson({ id: 'project-board', origin: { kind: 'plugin' } }, 'project-board')).toBe(false)
    expect(isClosedByPerson({ id: 'project-board', origin: { kind: 'unload' } }, 'project-board')).toBe(false)
    expect(isClosedByPerson({ id: 'other', origin: { kind: 'person' } }, 'project-board')).toBe(false)
  })
  test('footer 는 엔진의 모드 뒤에 보드 요약을 붙임', async ($, on) => {
    world(on)
    await $.session.start(kStart)
    expect(await footer($)).toMatch(/^plan \| ▦ /)
  })
  test('설정 파일이 없으면 footer 에 아무것도 붙이지 않음', async ($, on) => {
    world(on, { files: { '.claude/project-board.json': undefined as never } })
    await $.session.start(kStart)
    expect(await footer($)).toBe('plan')
  })
  test('패널이 열려 있으면 밴드 없음(엔진 몫은 그대로), off 면 밴드가 엔진 몫 위에 보임', async ($, on) => {
    world(on)
    await $.session.start(kStart)
    expect(await band($)).toEqual({ mine: undefined, engine: 'engine' })
    await run($, 'off')
    const b = await band($)
    expect(b.mine).toContain('/project-board 로 열기')
    expect(b.engine).toBe('engine')
  })
  test('설문이 띠를 쓰는 동안은 양보', async ($, on) => {
    world(on)
    await $.session.start(kStart)
    await run($, 'off')
    expect((await band($, { hasSurvey: true })).mine).toBeUndefined()
  })
  test('off 뒤 /project-board 로 열면 밴드가 사라짐', async ($, on) => {
    world(on)
    await $.session.start(kStart)
    await run($, 'off')
    await run($)
    expect((await band($)).mine).toBeUndefined()
  })
  test('/clear 뒤 off 상태는 엔진의 실제 패널 상태로 다시 맞춤(닫혀 있으면 밴드)', async ($, on) => {
    world(on, { panes: [] })
    await $.session.start(kStart)
    await $.classic.SessionStart({ source: 'clear' })
    expect((await band($)).mine).toContain('/project-board 로 열기')
  })
  test('/clear 뒤 패널이 열려 있으면 밴드 없음', async ($, on) => {
    world(on, { panes: ['project-board'] })
    await $.session.start(kStart)
    await $.classic.SessionStart({ source: 'clear' })
    expect((await band($)).mine).toBeUndefined()
  })
})

describe('변경 감지 생략과 변화 알림', () => {
  const designReads = (w: ReturnType<typeof world>) => w.log.reads.filter(p => p.endsWith('design.html')).length
  const withStatus = (status: string) => {
    const roadmap = JSON.parse(kHtml.match(/>(\{.*\})<\/script>/)![1]!)
    roadmap.items[1].status = status
    return kHtml.replace(/>\{.*\}<\/script>/, `>${JSON.stringify(roadmap)}</script>`)
  }
  const header = async ($: Engine) => {
    const ui = await $.ui.mount({ plugin: 'project-board', surface: 'terminal', component: 'Pane', requestId: 'project-board', props: { title: 't', isFocused: false, bodyColumns: 80, placement: 'dock', scroll: { offset: 0, bodyRows: 20 }, view: {} } as never })
    const text = (await ui.findAll({ type: 'Text', text: /갱신/ }))[0]?.text ?? ''
    return { ui, text }
  }

  test('파일이 그대로면 답변 끝에 다시 읽지 않고 갱신 시각만 바꿈', async ($, on) => {
    const w = world(on, { nowMs: new Date('2026-11-10T01:00:00Z').getTime() })
    await $.session.start(kStart)
    const reads = designReads(w)
    await w.clock.advance(90 * 60000)
    await $.turn.complete({ ...kDone })
    expect(designReads(w)).toBe(reads)
    const { ui, text } = await header($)
    expect(text).toContain(`갱신 ${formatLocalTime(new Date('2026-11-10T02:30:00Z'))}`)
    await ui.unmount()
  })
  test('파일이 바뀌면 다시 읽음(길이가 같은 수정 포함)', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    const reads = designReads(w)
    w.files['design.html'] = withStatus('완료')
    await $.turn.complete({ ...kDone })
    expect(designReads(w)).toBe(reads + 1)
  })
  test('stat 이 실패하면 매번 다시 읽음(옛 값에 고착하지 않음)', async ($, on) => {
    const w = world(on, { statError: true })
    await $.session.start(kStart)
    const reads = designReads(w)
    await $.turn.complete({ ...kDone })
    expect(designReads(w)).toBe(reads + 1)
  })
  test('새로고침 버튼은 파일이 그대로여도 다시 읽음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    const reads = designReads(w)
    const { ui } = await header($)
    await ui.press({ key: 'refresh' })
    expect(designReads(w)).toBe(reads + 1)
    await ui.unmount()
  })
  test('설정에 소스가 추가되면 새 소스도 읽음', async ($, on) => {
    const w = world(on, { files: { 'plan.md': '| U-1 | 질문 | 영향 | 결정 필요 |' } })
    await $.session.start(kStart)
    w.files['.claude/project-board.json'] = JSON.stringify({
      ...JSON.parse(kCfg),
      decisions: [{ file: 'plan.md', label: '계획', format: 'md-table', idPrefix: 'U', kind: 'classify', pending: '결정 필요' }],
    })
    await $.turn.complete({ ...kDone })
    expect(w.log.reads.some(p => p.endsWith('plan.md'))).toBe(true)
  })
  test('처음 읽을 때는 알리지 않고, 로드맵 상태가 바뀌면 toast', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    expect(w.log.toasts).toEqual([])
    w.files['design.html'] = withStatus('완료')
    await $.turn.complete({ ...kDone })
    expect(w.log.toasts).toEqual(['로드맵 C-B: 대기 → 완료'])
  })
  test('지문을 찍은 뒤 읽기 전에 파일이 바뀌면 다음 답변 끝에 다시 읽음', async ($, on) => {
    let isDone = false
    const w = world(on, {
      afterStat: (path, files) => {
        if (!isDone && path.endsWith('design.html')) {
          isDone = true
          files['design.html'] = withStatus('완료')
        }
      },
    })
    await $.session.start(kStart)
    const reads = designReads(w)
    await $.turn.complete({ ...kDone })
    expect(designReads(w)).toBe(reads + 1)
  })
  test('/clear 뒤 첫 읽기는 바뀐 것이 있어도 알리지 않음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    w.files['design.html'] = withStatus('완료')
    await $.classic.SessionStart({ source: 'clear' })
    expect(w.log.toasts).toEqual([])
  })
  test('파일이 그대로면 toast 가 반복되지 않음', async ($, on) => {
    const w = world(on)
    await $.session.start(kStart)
    w.files['design.html'] = withStatus('완료')
    await $.turn.complete({ ...kDone })
    await $.turn.complete({ ...kDone })
    expect(w.log.toasts.length).toBe(1)
  })
})
