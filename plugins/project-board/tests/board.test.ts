import { describe, expect, test } from 'claude-code/testing'

import { findTerms, kDefaultGlossary, mergeSeen } from '../hooks/glossary'
import { buildBoard, folderTitle, mergeGlossary, parseDecisions, plainText, tableRows, validateConfig } from '../hooks/parse'
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
    expect(b.past).toEqual([{ id: 'DR-01', topic: '서명 위치', detail: '미들웨어', source: '설계 11절' }])
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

test('패널에 탭 3개와 새로고침이 그려지고 설정이 없으면 안내를 보임', async $ => {
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'project-board', surface, component: 'Pane', requestId: 'project-board',
      props: { title: 'Project Board', isFocused: false, bodyColumns: 60, placement: 'dock', scroll: { offset: 0, bodyRows: 20 }, view: {} },
    })
    for (const key of ['tab-status', 'tab-terms', 'tab-decisions', 'refresh']) {
      expect(await ui.find({ key })).toBeDefined()
    }
    await ui.press({ key: 'tab-terms' })
    await ui.unmount()
  }
})
