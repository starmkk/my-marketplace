// '변경' 탭 — 세션 시작 대비 현황(로드맵·결정)·파일(git) 변화를 비교하는 함수 모음.
// 비교는 순수 함수이고, git 실행만 호출하는 쪽이 넘기는 run 으로 한다.
import type { Baseline, BoardData, DecisionKind, DecisionSnap, GitNow, GitSnap, ItemSnap } from '../types'
import { cell, clip, kConfigPath } from './parse'

const kMaxRows = 20
const kKindLabel: Record<DecisionKind, string> = { recent: '현재 결정', pending: '앞으로 결정', past: '지난 결정', other: '분류 밖(목록에 안 나옴)' }

// ---- 현황 비교 ----

export type RoadmapDiff = {
  statusChanged: { id: string; title: string; from: string; to: string }[]
  added: ItemSnap[]
  removed: ItemSnap[]
}

export function diffRoadmap(before: ItemSnap[], after: ItemSnap[]): RoadmapDiff {
  const was = new Map(before.map(i => [i.id, i]))
  const is = new Map(after.map(i => [i.id, i]))
  return {
    statusChanged: after
      .filter(i => was.has(i.id) && was.get(i.id)?.status !== i.status)
      .map(i => ({ id: i.id, title: i.title, from: was.get(i.id)?.status ?? '', to: i.status })),
    added: after.filter(i => !was.has(i.id)),
    removed: before.filter(i => !is.has(i.id)),
  }
}

export function snapshotDecisions(b: Pick<BoardData, 'recent' | 'pending' | 'past' | 'unclassified'>): DecisionSnap[] {
  return [
    ...b.recent.map(r => ({ ...r, kind: 'recent' as const })),
    ...b.pending.map(r => ({ ...r, kind: 'pending' as const })),
    ...b.past.map(r => ({ ...r, kind: 'past' as const })),
    ...b.unclassified.map(r => ({ ...r, kind: 'other' as const })),
  ]
}

export type DecisionDiff = {
  added: DecisionSnap[]
  removed: DecisionSnap[]
  moved: { row: DecisionSnap; from: DecisionKind; to: DecisionKind }[]
  edited: { row: DecisionSnap }[]
}

// 같은 항목 = 출처 + ID. 분류가 바뀌면 이동, 같은 분류에서 내용이 바뀌면 수정.
// 내용 비교는 잘린 표시값이 아니라 행 전체(sig)로 함. 분류 밖(other) 행의 추가·삭제는 표시하지 않고, 분류를 넘나든 것만 이동으로 셈
export function diffDecisions(before: DecisionSnap[], after: DecisionSnap[]): DecisionDiff {
  const key = (r: DecisionSnap) => `${r.source}\u0000${r.id}`
  const sigOf = (r: DecisionSnap) => r.sig ?? `${r.topic}\u0000${r.detail}`
  const was = new Map(before.map(r => [key(r), r]))
  const is = new Set(after.map(key))
  const out: DecisionDiff = { added: [], removed: before.filter(r => r.kind !== 'other' && !is.has(key(r))), moved: [], edited: [] }
  for (const row of after) {
    const old = was.get(key(row))
    if (!old) {
      if (row.kind !== 'other') {
        out.added.push(row)
      }
    } else if (old.kind !== row.kind) {
      out.moved.push({ row, from: old.kind, to: row.kind })
    } else if (row.kind !== 'other' && sigOf(old) !== sigOf(row)) {
      out.edited.push({ row })
    }
  }
  return out
}

// 읽기에 실패했거나 일부만 읽은 현황은 비교하지 않음 — 빠진 항목이 '삭제'로 보이는 오판 방지
function unreadableReason(board: BoardData | null): string | null {
  if (board === null) {
    return `설정 파일(${kConfigPath}) 없음`
  }
  if (board.error) {
    return `읽기 실패: ${board.error}`
  }
  if (board.warnings.length) {
    return `일부 소스를 읽지 못함: ${board.warnings.join(', ')}`
  }
  return null
}

// 소스 구성(이름 집합)이 바뀜 — 설정 변경·이름 변경
function sourceSetChanged(before: Record<string, number>, after: Record<string, number>): boolean {
  const names = (r: Record<string, number>) => Object.keys(r).sort().join('\u0000')
  return names(before) !== names(after)
}

// 행이 있던 소스가 0행이 됨 — 경고 없이 비는 경우(편집기가 파일을 비운 뒤 다시 쓰는 순간 등)
function emptiedSources(before: Record<string, number>, after: Record<string, number>): string[] {
  return Object.keys(before).filter(k => (before[k] ?? 0) > 0 && (after[k] ?? 0) === 0)
}

// 두 현황을 비교해도 되는지 — 안 되면 사유, 되면 null. 빈 항목이 '삭제'로, 돌아온 항목이 '추가'로 보이는 오판을 막음.
// 변경 탭(diffBoard)과 변화 알림(boardNotices·advanceNotices)이 같은 규칙을 씀
export function comparableReason(before: Pick<BoardData, 'sourceRows'>, after: BoardData | null): string | null {
  const reason = unreadableReason(after)
  if (after === null || reason !== null) {
    return `지금 현황을 읽지 못함 — ${reason}`
  }
  if (sourceSetChanged(before.sourceRows, after.sourceRows)) {
    return '읽는 소스 구성이 세션 중에 바뀜(설정 변경·이름 변경)'
  }
  const emptied = emptiedSources(before.sourceRows, after.sourceRows)
  return emptied.length ? `세션 시작 때 행이 있던 소스가 비었음: ${emptied.join(', ')}` : null
}

export function takeBaseline(board: BoardData | null, git: GitSnap, at: string): Baseline {
  const reason = unreadableReason(board)
  return {
    at,
    board: board && reason === null ? { items: board.items, decisions: snapshotDecisions(board), sourceRows: board.sourceRows } : null,
    boardReason: reason ?? '',
    git,
  }
}

export type BoardDiff = { kind: 'unavailable'; reason: string } | { kind: 'ok'; roadmap: RoadmapDiff; decisions: DecisionDiff }

export function diffBoard(baseline: Baseline | null, board: BoardData | null): BoardDiff {
  if (baseline === null) {
    return { kind: 'unavailable', reason: '세션 시작 기준을 잡지 못함' }
  }
  if (baseline.board === null) {
    return { kind: 'unavailable', reason: `세션 시작 때 현황을 읽지 못함 — ${baseline.boardReason}` }
  }
  const reason = comparableReason(baseline.board, board)
  if (board === null || reason !== null) {
    return { kind: 'unavailable', reason: reason ?? '' }
  }
  return {
    kind: 'ok',
    roadmap: diffRoadmap(baseline.board.items, board.items),
    decisions: diffDecisions(baseline.board.decisions, snapshotDecisions(board)),
  }
}

// ---- 변화 알림(toast) ----

const kMaxNotices = 3
const kMaxNoticeLength = 60

// 직전 현황 대비 알릴 만한 변화: 로드맵 상태 변경, 결정 필요(추가·이동), 결정됨(결정 필요 → 현재 결정).
// 비교할 수 없으면 빈 목록. 최대 3줄이고 넘치면 마지막 줄을 '외 N건' 으로 줄임
export function boardNotices(prev: BoardData, next: BoardData): string[] {
  if (unreadableReason(prev) !== null || comparableReason(prev, next) !== null) {
    return []
  }
  const changed = diffRoadmap(prev.items, next.items).statusChanged
  const roadmap = changed.length <= 2
    ? changed.map(c => `로드맵 ${c.id}: ${c.from} → ${c.to}`)
    : [`로드맵 상태 변경 ${changed.length}건 — 변경 탭 참고`]
  const d = diffDecisions(snapshotDecisions(prev), snapshotDecisions(next))
  const line = (label: string, r: DecisionSnap) => clip(`${label}: ${r.id} ${r.topic}`, kMaxNoticeLength)
  const pending = [...d.added.filter(r => r.kind === 'pending'), ...d.moved.filter(m => m.to === 'pending').map(m => m.row)]
  const decided = d.moved.filter(m => m.from === 'pending' && m.to === 'recent').map(m => m.row)
  const all = [...roadmap, ...pending.map(r => line('결정 필요', r)), ...decided.map(r => line('결정됨', r))]
  if (all.length <= kMaxNotices) {
    return all
  }
  return [...all.slice(0, kMaxNotices - 1), `외 ${all.length - (kMaxNotices - 1)}건 — 변경 탭 참고`]
}

// 알림 기준(ref)을 다음 현황으로 옮길지 정하고 알릴 줄을 돌려줌. last 는 직전에 읽은 현황(기준과 다를 수 있음).
// - 기준이 없으면: 읽은 현황이 기준이 되고 알리지 않음
// - 읽지 못했으면: 기준을 그대로 둠
// - 소스 구성이 바뀌었으면(설정 변경): 새 현황이 기준이 되고 알리지 않음(옛 기준에 고착하지 않음)
// - 행이 있던 소스가 비었으면: 처음 한 번은 기준을 그대로 둠(편집 중 잠깐 빈 것이 돌아왔을 때 전부 '추가' 로 알리지 않음).
//   직전 현황도 같은 소스가 비어 있었으면 정말로 비운 것 — 직전 대비 변화를 알리고 기준을 옮김(알림이 조용히 멈추지 않음)
export function advanceNotices(
  ref: BoardData | null,
  next: BoardData | null,
  last: BoardData | null = null,
): { ref: BoardData | null; lines: string[] } {
  if (next === null || unreadableReason(next) !== null) {
    return { ref, lines: [] }
  }
  if (ref === null || sourceSetChanged(ref.sourceRows, next.sourceRows)) {
    return { ref: next, lines: [] }
  }
  const emptied = emptiedSources(ref.sourceRows, next.sourceRows)
  if (emptied.length) {
    const stillEmpty = last !== null && unreadableReason(last) === null && !sourceSetChanged(last.sourceRows, next.sourceRows)
      && emptied.every(k => (last.sourceRows[k] ?? 0) === 0)
    return stillEmpty ? { ref: next, lines: boardNotices(last, next) } : { ref, lines: [] }
  }
  return { ref: next, lines: boardNotices(ref, next) }
}

// ---- git ----

export type GitRun = (argv: string[]) => Promise<{ exitCode: number; stdout: string; stderr: string; isStdoutTruncated?: boolean }>

const kGitBase = ['git', '--no-optional-locks', '-c', 'core.quotepath=false']

// `git status --porcelain=v1 -z` 출력에서 변경 경로를 뽑음(이름 바꾸기·복사의 원래 경로는 건너뜀, ._ 파일 제외)
export function parseStatusZ(out: string): string[] {
  const fields = out.split('\0')
  const paths = new Set<string>()
  for (let i = 0; i < fields.length; i++) {
    const entry = fields[i] ?? ''
    if (entry.length < 4) {
      continue
    }
    const xy = entry.slice(0, 2)
    if (/[RC]/.test(xy)) {
      i++
    }
    const path = entry.slice(3)
    if (!(path.split('/').pop() ?? '').startsWith('._')) {
      paths.add(path)
    }
  }
  return [...paths].sort()
}

function failure(stderr: string, exitCode: number): string {
  return stderr.trim().split('\n')[0] || `git 종료 코드 ${exitCode}`
}

// since 가 있으면 그 HEAD 이후의 새 커밋도 읽음(head null = 그때 커밋이 없었음). 던지지 않고 error 로 돌려줌
export async function readGit(run: GitRun, since: { head: string | null } | null): Promise<GitNow> {
  const fail = (message: string): GitNow => ({ snap: { kind: 'error', message }, commits: [] })
  try {
    const inside = await run([...kGitBase, 'rev-parse', '--is-inside-work-tree'])
    if (inside.exitCode !== 0) {
      return /not a git repository/i.test(inside.stderr) ? { snap: { kind: 'none' }, commits: [] } : fail(failure(inside.stderr, inside.exitCode))
    }
    if (inside.stdout.trim() !== 'true') {
      return { snap: { kind: 'none' }, commits: [] }
    }
    const headRun = await run([...kGitBase, 'rev-parse', '--verify', '--quiet', 'HEAD'])
    const head = headRun.exitCode === 0 ? headRun.stdout.trim() : null
    const status = await run([...kGitBase, 'status', '--porcelain=v1', '-z', '--untracked-files=all'])
    if (status.exitCode !== 0) {
      return fail(failure(status.stderr, status.exitCode))
    }
    if (status.isStdoutTruncated) {
      return fail('git status 출력이 너무 커서 일부가 잘림')
    }
    let commits: string[] = []
    if (since && head !== null && head !== since.head) {
      // 기준 HEAD 가 현재 HEAD 의 조상일 때만 그 이후 커밋으로 셈 — 브랜치 전환·rebase 로 조상이 아니면
      // `기준..HEAD` 가 다른 브랜치의 옛 커밋을 새 커밋으로 내놓음(headMoved 로 표시). 기준 커밋이 사라진 경우(128)도 같음
      let isAncestor = since.head === null
      if (since.head !== null) {
        const anc = await run([...kGitBase, 'merge-base', '--is-ancestor', since.head, 'HEAD'])
        if (anc.exitCode !== 0 && anc.exitCode !== 1 && anc.exitCode !== 128) {
          return fail(failure(anc.stderr, anc.exitCode))
        }
        isAncestor = anc.exitCode === 0
      }
      if (isAncestor) {
        const range = since.head === null ? 'HEAD' : `${since.head}..HEAD`
        const log = await run([...kGitBase, 'log', '-z', '--format=%h %s', range])
        if (log.exitCode !== 0) {
          return fail(failure(log.stderr, log.exitCode))
        }
        commits = log.stdout.split('\0').filter(Boolean)
      }
    }
    return { snap: { kind: 'ok', head, dirty: parseStatusZ(status.stdout) }, commits }
  } catch (err) {
    return fail(err instanceof Error ? err.message : String(err))
  }
}

export type FileDiff =
  | { kind: 'none' }
  | { kind: 'unavailable'; reason: string }
  | { kind: 'error'; message: string }
  | { kind: 'ok'; commits: string[]; newlyChanged: string[]; preexisting: string[]; cleared: string[]; headMoved: boolean }

export function diffFiles(baseline: Baseline | null, now: GitNow | null): FileDiff {
  if (baseline === null) {
    return { kind: 'unavailable', reason: '세션 시작 기준을 잡지 못함' }
  }
  if (baseline.git.kind === 'error') {
    return { kind: 'unavailable', reason: `세션 시작 때 git 을 읽지 못함 — ${baseline.git.message}` }
  }
  if (now === null) {
    return { kind: 'unavailable', reason: '아직 git 을 읽지 않음' }
  }
  if (now.snap.kind === 'error') {
    return { kind: 'error', message: now.snap.message }
  }
  if (baseline.git.kind === 'none') {
    return now.snap.kind === 'none' ? { kind: 'none' } : { kind: 'unavailable', reason: '세션 중에 git 저장소가 생겨 기준이 없음' }
  }
  if (now.snap.kind === 'none') {
    return { kind: 'error', message: 'git 저장소를 찾을 수 없게 됨' }
  }
  const was = new Set(baseline.git.dirty)
  const isDirty = new Set(now.snap.dirty)
  return {
    kind: 'ok',
    commits: now.commits,
    newlyChanged: now.snap.dirty.filter(f => !was.has(f)),
    preexisting: now.snap.dirty.filter(f => was.has(f)),
    // 시작 때 변경돼 있었는데 지금은 깨끗함 — 되돌렸거나 커밋함
    cleared: baseline.git.dirty.filter(f => !isDirty.has(f)),
    headMoved: now.snap.head !== baseline.git.head && now.commits.length === 0,
  }
}

// ---- 표시 ----

function capped<T>(list: T[], render: (t: T) => string): string {
  const shown = list.slice(0, kMaxRows).map(render)
  if (list.length > kMaxRows) {
    shown.push(`_외 ${list.length - kMaxRows}개_`)
  }
  return shown.join('\n')
}

function table(head: string[], rows: string[][]): string {
  return [
    `| ${head.join(' | ')} |`,
    `|${head.map(() => '---').join('|')}|`,
    capped(rows, r => `| ${r.map(cell).join(' | ')} |`),
  ].join('\n')
}

function boardMarkdown(d: BoardDiff): string {
  if (d.kind === 'unavailable') {
    return `_비교 불가: ${d.reason}_`
  }
  const { roadmap: r, decisions: ds } = d
  const roadmapRows = [
    ...r.statusChanged.map(c => [c.id, c.title, `${c.from} → ${c.to}`]),
    ...r.added.map(i => [i.id, i.title, `추가 (${i.status})`]),
    ...r.removed.map(i => [i.id, i.title, `삭제 (마지막 상태 ${i.status})`]),
  ]
  const decisionRows = [
    ...ds.added.map(x => [x.id, x.topic, x.source, `추가 (${kKindLabel[x.kind]})`]),
    ...ds.moved.map(m => [m.row.id, m.row.topic, m.row.source, `${kKindLabel[m.from]} → ${kKindLabel[m.to]}`]),
    ...ds.edited.map(e => [e.row.id, e.row.topic, e.row.source, '내용 변경']),
    ...ds.removed.map(x => [x.id, x.topic, x.source, `삭제 (마지막 분류 ${kKindLabel[x.kind]})`]),
  ]
  return [
    '#### 로드맵',
    roadmapRows.length ? table(['ID', '내용', '변화'], roadmapRows) : '_변화 없음_',
    '\n#### 결정',
    decisionRows.length ? table(['ID', '내용', '출처', '변화'], decisionRows) : '_변화 없음_',
  ].join('\n')
}

function fileList(files: string[]): string {
  return capped(files, f => `- \`${f}\``)
}

function filesMarkdown(d: FileDiff): string {
  if (d.kind === 'none') {
    return '_해당 없음 — git 저장소가 아님_'
  }
  if (d.kind === 'unavailable') {
    return `_비교 불가: ${d.reason}_`
  }
  if (d.kind === 'error') {
    return `**git 오류**: ${cell(d.message)} — 변경 여부를 알 수 없음`
  }
  const parts = [
    d.commits.length ? `**새 커밋 ${d.commits.length}개**\n${capped(d.commits, c => `- ${cell(c)}`)}` : '**새 커밋** 없음',
    d.headMoved ? '_HEAD 가 바뀌었으나 세션 시작 HEAD 이후의 새 커밋으로 셀 수 없음 (브랜치 전환·rebase·되감기·리셋 가능)_' : '',
    d.newlyChanged.length ? `**이번 세션 중 변경 ${d.newlyChanged.length}개** (작업 트리·미추적 포함)\n${fileList(d.newlyChanged)}` : '**이번 세션 중 변경된 파일** 없음',
    d.preexisting.length
      ? `**세션 시작 전부터 변경 ${d.preexisting.length}개** — 이후 추가로 수정했는지는 구분하지 못함\n${fileList(d.preexisting)}`
      : '',
    d.cleared.length
      ? `**세션 시작 때 변경돼 있다가 지금은 깨끗한 파일 ${d.cleared.length}개** — 되돌렸거나 커밋함\n${fileList(d.cleared)}`
      : '',
  ]
  return parts.filter(Boolean).join('\n\n')
}

export function changesMarkdown(baseline: Baseline | null, board: BoardData | null, git: GitNow | null): string {
  return [
    baseline ? `**기준: 이 대화 시작 ${baseline.at}** (/clear·세션 안 재개로 새 대화가 되면 그 시점이 새 기준)` : '**기준 없음** — 대화 시작 기준을 잡지 못함',
    '\n### 현황',
    boardMarkdown(diffBoard(baseline, board)),
    '\n### 파일 (git)',
    filesMarkdown(diffFiles(baseline, git)),
  ].join('\n')
}
