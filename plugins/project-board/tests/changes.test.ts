import { describe, expect, test } from 'claude-code/testing'

import {
  changesMarkdown, diffBoard, diffDecisions, diffFiles, diffRoadmap, parseStatusZ, readGit, snapshotDecisions, takeBaseline,
} from '../hooks/changes'
import type { GitRun } from '../hooks/changes'
import { buildBoard } from '../hooks/parse'
import type { BoardConfig } from '../hooks/parse'
import type { Baseline, BoardData, GitNow, GitSnap, ItemSnap } from '../types'

const item = (id: string, status: string, parent: string | null = null, title = `${id} 제목`): ItemSnap => ({ id, title, status, parent })
const row = (id: string, source: string, topic = '주제', detail = '내용', sig?: string) => ({ id, topic, detail, source, ...(sig === undefined ? {} : { sig }) })

const kBoard = (over: Partial<BoardData> = {}): BoardData => ({
  title: 't', asOf: '-', currentStage: '-', tracks: [], stages: [], doing: [], nextUp: [],
  recent: [], past: [], pending: [], unclassified: [], glossary: [], sources: [], loadedAt: 'x', warnings: [], items: [], sourceRows: {}, ...over,
})

describe('로드맵 비교', () => {
  test('상태 변화·추가·삭제를 하위 항목까지 잡음', () => {
    const before = [item('M0', '진행'), item('A-00', '대기', 'M0'), item('A-01', '완료', 'M0')]
    const after = [item('M0', '진행'), item('A-00', '완료', 'M0'), item('A-02', '대기', 'M0')]
    const d = diffRoadmap(before, after)
    expect(d.statusChanged.map(c => [c.id, c.from, c.to])).toEqual([['A-00', '대기', '완료']])
    expect(d.added.map(i => i.id)).toEqual(['A-02'])
    expect(d.removed.map(i => i.id)).toEqual(['A-01'])
  })
  test('변화가 없으면 모두 빈 목록', () => {
    const same = [item('M0', '진행')]
    expect(diffRoadmap(same, same)).toEqual({ statusChanged: [], added: [], removed: [] })
  })
})

describe('결정 비교', () => {
  const snap = (b: Partial<BoardData>) => snapshotDecisions(kBoard(b))
  test('같은 ID 라도 출처가 다르면 다른 항목(출처+ID 기준)', () => {
    const before = snap({ pending: [row('Q-01', '설계 10절')] })
    const after = snap({ pending: [row('Q-01', '설계 10절'), row('Q-01', 'M0 계획')] })
    const d = diffDecisions(before, after)
    expect(d.added.map(r => `${r.source}/${r.id}`)).toEqual(['M0 계획/Q-01'])
    expect(d.removed).toEqual([])
  })
  test('분류 이동과 내용 변경을 구분하고 삭제를 잡음', () => {
    const before = snap({ pending: [row('Q-01', 'A'), row('Q-02', 'A', '주제', '권고 1'), row('Q-03', 'A')] })
    const after = snap({ recent: [row('Q-01', 'A')], pending: [row('Q-02', 'A', '주제', '권고 2')] })
    const d = diffDecisions(before, after)
    expect(d.moved.map(m => [m.row.id, m.from, m.to])).toEqual([['Q-01', 'pending', 'recent']])
    expect(d.edited.map(e => e.row.id)).toEqual(['Q-02'])
    expect(d.removed.map(r => r.id)).toEqual(['Q-03'])
  })
  test('잘린 표시값이 같아도 행 전체(sig)가 다르면 내용 변경 — 뒷부분·중간 칸 변경을 놓치지 않음', () => {
    const d = diffDecisions(
      snap({ pending: [row('Q-01', 'A', '주제', '같은 앞부분…', 'q|주제|중간A|끝'), row('Q-02', 'A', '주제', '같음', 's2')] }),
      snap({ pending: [row('Q-01', 'A', '주제', '같은 앞부분…', 'q|주제|중간B|끝'), row('Q-02', 'A', '주제', '같음', 's2')] }),
    )
    expect(d.edited.map(e => e.row.id)).toEqual(['Q-01'])
  })
  test('분류 밖(other)으로 나간 행은 삭제가 아니라 이동으로, 분류 밖 행의 추가·삭제는 표시하지 않음', () => {
    const before = snap({ pending: [row('Q-01', 'A'), row('Q-02', 'A')], unclassified: [row('Q-09', 'A')] })
    const after = snap({ pending: [row('Q-02', 'A')], unclassified: [row('Q-01', 'A'), row('Q-10', 'A')] })
    const d = diffDecisions(before, after)
    expect(d.removed).toEqual([])
    expect(d.added).toEqual([])
    expect(d.moved.map(m => [m.row.id, m.from, m.to])).toEqual([['Q-01', 'pending', 'other']])
  })
  test('분류 이동과 내용 변경이 함께면 이동으로만 셈', () => {
    const d = diffDecisions(snap({ pending: [row('Q-01', 'A', 't', 'a')] }), snap({ recent: [row('Q-01', 'A', 't', 'b')] }))
    expect(d.moved.length).toBe(1)
    expect(d.edited.length).toBe(0)
  })
})

describe('기준(baseline)과 현황 비교 가능 여부', () => {
  const okGit: GitSnap = { kind: 'ok', head: 'aaa', dirty: [] }
  test('정상 읽기면 기준을 잡고, 설정 없음·읽기 실패·경고가 있으면 비교 불가 사유를 남김', () => {
    expect(takeBaseline(kBoard(), okGit, 't0').board).not.toBeNull()
    expect(takeBaseline(null, okGit, 't0').boardReason).toContain('설정')
    expect(takeBaseline(kBoard({ error: '깨짐' }), okGit, 't0').boardReason).toContain('깨짐')
    const w = takeBaseline(kBoard({ warnings: ['a.html 없음'] }), okGit, 't0')
    expect(w.board).toBeNull()
    expect(w.boardReason).toContain('a.html 없음')
  })
  test('diffBoard: 기준 때 행이 있던 소스가 비었거나 소스 구성(설정)이 바뀌면 삭제가 아니라 비교 불가', () => {
    const base = takeBaseline(kBoard({ sourceRows: { '로드맵 a.json': 2, '결정 (d.md)': 2 } }), okGit, 't0')
    const same = { '로드맵 a.json': 2, '결정 (d.md)': 2 }
    expect(diffBoard(base, kBoard({ sourceRows: same })).kind).toBe('ok')
    const emptied = diffBoard(base, kBoard({ sourceRows: { ...same, '결정 (d.md)': 0 } }))
    expect(emptied.kind === 'unavailable' && emptied.reason).toContain('결정 (d.md)')
    const removedSrc = diffBoard(base, kBoard({ sourceRows: { '로드맵 a.json': 2 } }))
    expect(removedSrc.kind).toBe('unavailable')
    const renamed = diffBoard(base, kBoard({ sourceRows: { '로드맵 a.json': 2, '새 이름 (d.md)': 2 } }))
    expect(renamed.kind).toBe('unavailable')
    // 기준 때도 0행이던 소스가 여전히 0행이면 비교 가능
    const b0 = takeBaseline(kBoard({ sourceRows: { x: 0 } }), okGit, 't0')
    expect(diffBoard(b0, kBoard({ sourceRows: { x: 0 } })).kind).toBe('ok')
  })
  test('diffBoard: 기준 없음·현재 읽기 실패는 비교 불가이지 변화 없음이 아님', () => {
    const base = takeBaseline(kBoard(), okGit, 't0')
    expect(diffBoard(null, kBoard()).kind).toBe('unavailable')
    expect(diffBoard(takeBaseline(null, okGit, 't0'), kBoard()).kind).toBe('unavailable')
    expect(diffBoard(base, null).kind).toBe('unavailable')
    expect(diffBoard(base, kBoard({ error: 'x' })).kind).toBe('unavailable')
    expect(diffBoard(base, kBoard({ warnings: ['b 없음'] })).kind).toBe('unavailable')
    expect(diffBoard(base, kBoard()).kind).toBe('ok')
  })
})

describe('git 상태 파싱', () => {
  test('-z 출력: 한글 경로·공백·이름 바꾸기(원래 경로 건너뜀)·미추적을 읽고 ._ 파일은 뺌', () => {
    const out = [' M 문서/설계 문서.md', '?? new.txt', 'R  b.txt', 'a.txt', '?? dir/._junk', '?? ._top', 'A  c.swift', ''].join('\0')
    expect(parseStatusZ(out)).toEqual(['b.txt', 'c.swift', 'new.txt', '문서/설계 문서.md'])
  })
  test('스테이징된 복사(C)도 원래 경로를 건너뜀', () => {
    expect(parseStatusZ(['C  copy.txt', 'orig.txt', ' M other.txt', ''].join('\0'))).toEqual(['copy.txt', 'other.txt'])
  })
  test('빈 출력은 빈 목록', () => {
    expect(parseStatusZ('')).toEqual([])
  })
})

function fakeRun(table: Record<string, { exitCode?: number; stdout?: string; stderr?: string } | Error>): { run: GitRun; calls: string[][] } {
  const calls: string[][] = []
  const run: GitRun = async argv => {
    calls.push([...argv])
    const key = argv.filter(a => !['--no-optional-locks', '-c', 'core.quotepath=false'].includes(a)).slice(1).join(' ')
    const hit = Object.entries(table).find(([k]) => key.startsWith(k))
    if (!hit) {
      throw new Error(`예상 못 한 git 호출: ${key}`)
    }
    if (hit[1] instanceof Error) {
      throw hit[1]
    }
    return { exitCode: 0, stdout: '', stderr: '', ...hit[1] }
  }
  return { run, calls }
}
const kRepo = {
  'rev-parse --is-inside-work-tree': { stdout: 'true\n' },
  'rev-parse --verify': { stdout: 'abc1234\n' },
  'status': { stdout: ' M a.txt\0?? ._x\0' },
  'merge-base --is-ancestor': { exitCode: 0 },
}

describe('readGit', () => {
  test('정상: HEAD 와 변경 파일을 읽고 quotepath·락 옵션을 줌', async () => {
    const { run, calls } = fakeRun(kRepo)
    const now = await readGit(run, null)
    expect(now.snap).toEqual({ kind: 'ok', head: 'abc1234', dirty: ['a.txt'] })
    expect(now.commits).toEqual([])
    const status = calls.find(c => c.includes('status'))!
    expect(status).toContain('-z')
    expect(status).toContain('--untracked-files=all')
    expect(status).toContain('--no-optional-locks')
    expect(status.join(' ')).toContain('core.quotepath=false')
  })
  test('git 저장소가 아니면 none', async () => {
    const { run } = fakeRun({ 'rev-parse --is-inside-work-tree': { exitCode: 128, stderr: 'fatal: not a git repository (or any of the parent directories): .git' } })
    expect((await readGit(run, null)).snap).toEqual({ kind: 'none' })
  })
  test('그 밖의 git 실패·실행 불가는 error (변경 없음으로 보이지 않음)', async () => {
    const dubious = fakeRun({ 'rev-parse --is-inside-work-tree': { exitCode: 128, stderr: 'fatal: detected dubious ownership' } })
    expect((await readGit(dubious.run, null)).snap.kind).toBe('error')
    const noGit = fakeRun({ 'rev-parse --is-inside-work-tree': new Error('spawn git ENOENT') })
    expect(await readGit(noGit.run, null)).toEqual({ snap: { kind: 'error', message: 'spawn git ENOENT' }, commits: [] })
    const badStatus = fakeRun({ ...kRepo, status: { exitCode: 1, stderr: 'fatal: index file corrupt' } })
    const r = await readGit(badStatus.run, null)
    expect(r.snap.kind).toBe('error')
    expect((r.snap as { message: string }).message).toContain('index file corrupt')
  })
  test('출력이 잘렸으면 error', async () => {
    const { run } = fakeRun(kRepo)
    const truncated: GitRun = async argv => ({ ...(await run(argv)), isStdoutTruncated: argv.includes('status') })
    expect((await readGit(truncated, null)).snap.kind).toBe('error')
  })
  test('기준 HEAD 가 있으면 새 커밋 목록을 읽음 (HEAD 가 같으면 log 를 부르지 않음)', async () => {
    const { run, calls } = fakeRun({ ...kRepo, log: { stdout: 'abc1234 둘째\0def5678 첫째\0' } })
    const moved = await readGit(run, { head: 'old0000' })
    expect(moved.commits).toEqual(['abc1234 둘째', 'def5678 첫째'])
    expect(calls.find(c => c.includes('log'))!.join(' ')).toContain('old0000..HEAD')
    const same = fakeRun({ ...kRepo, 'rev-parse --verify': { stdout: 'old0000\n' } })
    expect((await readGit(same.run, { head: 'old0000' })).commits).toEqual([])
    expect(same.calls.some(c => c.includes('log'))).toBe(false)
  })
  test('제목에 파이프·공백이 든 커밋도 그대로 읽음', async () => {
    const { run } = fakeRun({ ...kRepo, log: { stdout: 'abc1234 a | b  c\0' } })
    expect((await readGit(run, { head: 'old0000' })).commits).toEqual(['abc1234 a | b  c'])
  })
  test('기준 HEAD 가 조상이 아니면(브랜치 전환·rebase) 옛 커밋을 새 커밋으로 읽지 않음 — log 를 부르지 않음', async () => {
    for (const exitCode of [1, 128]) {
      const { run, calls } = fakeRun({ ...kRepo, 'merge-base --is-ancestor': { exitCode }, log: { stdout: 'zzz9999 옛 커밋\0' } })
      const now = await readGit(run, { head: 'old0000' })
      expect(now.commits).toEqual([])
      expect(now.snap.kind).toBe('ok')
      expect(calls.some(c => c.includes('log'))).toBe(false)
      expect(calls.find(c => c.includes('merge-base'))!.slice(-3)).toEqual(['--is-ancestor', 'old0000', 'HEAD'])
    }
  })
  test('조상 검사가 그 밖의 코드로 실패하면 error', async () => {
    const { run } = fakeRun({ ...kRepo, 'merge-base --is-ancestor': { exitCode: 2, stderr: 'boom' } })
    expect((await readGit(run, { head: 'old0000' })).snap.kind).toBe('error')
  })
  test('log 가 실패하면 error (새 커밋 없음으로 보이지 않음)', async () => {
    const { run } = fakeRun({ ...kRepo, log: { exitCode: 128, stderr: 'fatal: bad revision' } })
    const now = await readGit(run, { head: 'old0000' })
    expect(now.snap.kind).toBe('error')
    expect((now.snap as { message: string }).message).toContain('bad revision')
  })
  test('기준 때 커밋이 없던(unborn) 저장소는 HEAD 전체가 새 커밋', async () => {
    const { run, calls } = fakeRun({ ...kRepo, log: { stdout: 'abc1234 첫 커밋\0' } })
    expect((await readGit(run, { head: null })).commits).toEqual(['abc1234 첫 커밋'])
    expect(calls.find(c => c.includes('log'))!).not.toContain('..HEAD')
    expect(calls.some(c => c.includes('merge-base'))).toBe(false)
  })
  test('커밋이 없는 저장소(HEAD 없음)는 head null', async () => {
    const { run } = fakeRun({ ...kRepo, 'rev-parse --verify': { exitCode: 1 } })
    expect((await readGit(run, null)).snap).toEqual({ kind: 'ok', head: null, dirty: ['a.txt'] })
  })
})

describe('파일 변화 비교', () => {
  const ok = (head: string | null, dirty: string[], commits: string[] = []): GitNow => ({ snap: { kind: 'ok', head, dirty }, commits })
  const base = (git: GitSnap): Baseline => takeBaseline(kBoard(), git, 't0')
  test('세션 시작 전부터 변경된 파일과 세션 중 새로 변경된 파일을 구분', () => {
    const d = diffFiles(base({ kind: 'ok', head: 'h1', dirty: ['a', 'b'] }), ok('h1', ['b', 'c']))
    expect(d).toEqual({ kind: 'ok', commits: [], newlyChanged: ['c'], preexisting: ['b'], cleared: ['a'], headMoved: false })
  })
  test('시작 때 변경돼 있던 파일을 되돌리거나 커밋해 깨끗해지면 cleared 로 알림 (없다고 말하지 않음)', () => {
    const d = diffFiles(base({ kind: 'ok', head: 'h1', dirty: ['a.txt'] }), ok('h1', []))
    expect(d.kind === 'ok' && d.cleared).toEqual(['a.txt'])
    const md = changesMarkdown(base({ kind: 'ok', head: 'h1', dirty: ['a.txt'] }), kBoard(), ok('h1', []))
    expect(md).toContain('a.txt')
    expect(md).toContain('깨끗')
  })
  test('HEAD 가 바뀌고 새 커밋이 있으면 headMoved 가 아님', () => {
    const d = diffFiles(base({ kind: 'ok', head: 'h1', dirty: [] }), ok('h2', [], ['h2 커밋']))
    expect(d.kind === 'ok' && d.headMoved).toBe(false)
  })
  test('HEAD 가 바뀌었는데 새 커밋이 없으면 headMoved(되감기·리셋 가능)', () => {
    const d = diffFiles(base({ kind: 'ok', head: 'h1', dirty: [] }), ok('h0', []))
    expect(d.kind === 'ok' && d.headMoved).toBe(true)
    const md = changesMarkdown(base({ kind: 'ok', head: 'h1', dirty: [] }), kBoard(), ok('h0', []))
    expect(md).toContain('브랜치 전환')
  })
  test('저장소가 아니면 해당 없음, 기준 없음·기준 git 오류는 비교 불가, 현재 git 오류는 오류', () => {
    expect(diffFiles(base({ kind: 'none' }), { snap: { kind: 'none' }, commits: [] }).kind).toBe('none')
    expect(diffFiles(null, ok('h', [])).kind).toBe('unavailable')
    expect(diffFiles(base({ kind: 'error', message: 'x' }), ok('h', [])).kind).toBe('unavailable')
    expect(diffFiles(base({ kind: 'ok', head: 'h', dirty: [] }), null).kind).toBe('unavailable')
    expect(diffFiles(base({ kind: 'ok', head: 'h', dirty: [] }), { snap: { kind: 'error', message: '깨짐' }, commits: [] }).kind).toBe('error')
    expect(diffFiles(base({ kind: 'none' }), ok('h', [])).kind).toBe('unavailable')
    expect(diffFiles(base({ kind: 'ok', head: 'h', dirty: [] }), { snap: { kind: 'none' }, commits: [] }).kind).toBe('error')
  })
})

describe('변경 탭 마크다운', () => {
  const git0: GitSnap = { kind: 'ok', head: 'h1', dirty: ['old.txt'] }
  const b0 = takeBaseline(kBoard({ items: [item('M0', '진행')], pending: [row('Q-01', '설계')] }), git0, '2026-11-02 13:00')
  const b1 = kBoard({ items: [item('M0', '완료')], recent: [row('Q-01', '설계')] })
  const g1: GitNow = { snap: { kind: 'ok', head: 'h2', dirty: ['old.txt', '한글.md'] }, commits: ['h2 커밋'] }
  test('기준 시각·로드맵·결정·커밋·파일 구분이 모두 나옴', () => {
    const md = changesMarkdown(b0, b1, g1)
    expect(md).toContain('2026-11-02 13:00')
    expect(md).toContain('진행 → 완료')
    expect(md).toContain('앞으로 결정')
    expect(md).toContain('현재 결정')
    expect(md).toContain('h2 커밋')
    expect(md).toContain('한글.md')
    expect(md).toContain('세션 시작 전부터 변경')
    expect(md).toContain('old.txt')
  })
  test('비교 불가는 사유와 함께 표시하고 변화 없음이라고 쓰지 않음', () => {
    const md = changesMarkdown(takeBaseline(null, { kind: 'error', message: 'git 깨짐' }, 't0'), null, null)
    expect(md).toContain('비교 불가')
    expect(md).not.toContain('변화 없음')
  })
  test('git 이 없는 폴더는 해당 없음, 오류는 오류 문구', () => {
    const none = changesMarkdown(takeBaseline(kBoard(), { kind: 'none' }, 't0'), kBoard(), { snap: { kind: 'none' }, commits: [] })
    expect(none).toContain('해당 없음')
    const err = changesMarkdown(b0, b1, { snap: { kind: 'error', message: '깨짐' }, commits: [] })
    expect(err).toContain('git 오류')
    expect(err).toContain('깨짐')
  })
  test('목록이 길면 상한만 보이고 외 N개로 줄임', () => {
    const dirty = Array.from({ length: 60 }, (_, i) => `f${String(i).padStart(2, '0')}.txt`)
    const md = changesMarkdown(b0, b1, { snap: { kind: 'ok', head: 'h1', dirty }, commits: [] })
    expect(md).toContain('외 ')
    expect(md).not.toContain('f59.txt')
  })
  test('커밋 제목·표 셀의 파이프는 이스케이프되어 표와 목록이 깨지지 않음', () => {
    const b = kBoard({ items: [item('M0', '완료', null, '제목 | 파이프')] })
    const base0 = takeBaseline(kBoard({ items: [item('M0', '진행', null, '제목 | 파이프')] }), git0, 't0')
    const md = changesMarkdown(base0, b, { snap: git0, commits: ['h2 a | b'] })
    expect(md).toContain('제목 \\| 파이프')
    expect(md).toContain('h2 a \\| b')
  })
  test('변화가 실제로 없을 때만 변화 없음', () => {
    const same = kBoard({ items: [item('M0', '진행')], pending: [row('Q-01', '설계')] })
    const md = changesMarkdown(b0, same, { snap: git0, commits: [] })
    expect(md).toContain('변화 없음')
  })
  test('실제 buildBoard 결과로도 이어짐(items 채움)', async () => {
    const html = `<script id="roadmap-data">${JSON.stringify({ tracks: [{ key: 't', name: 'T' }], items: [{ id: 'X', track: 't', parent: null, title: 'x', deps: [], status: '대기' }] })}</script>`
    const cfg: BoardConfig = { roadmap: { file: 'd.html', format: 'html-script', id: 'roadmap-data' } }
    const b = await buildBoard(cfg, async () => html, [], 't')
    expect(b.items.map(i => i.id)).toEqual(['X'])
  })
})
