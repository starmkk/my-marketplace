export type BoardTab = 'status' | 'terms' | 'decisions' | 'changes'

export type TrackRow = { name: string; done: number; total: number; doing: string[] }
export type StageRow = { id: string; title: string; status: string; isCurrent: boolean }
// sig: 표시용으로 자르기 전의 행 전체(모든 칸) — 변경 탭이 내용 변경을 잘린 값에 기대지 않고 비교하는 데 씀
export type DecisionRow = { id: string; topic: string; detail: string; source: string; sig?: string }
// 변경 탭 — 세션 시작 대비 비교용 스냅샷
export type ItemSnap = { id: string; title: string; status: string; parent: string | null }
// other: 분류 규칙(decided·pending) 밖이라 어느 목록에도 안 나오는 행 — 삭제와 구분하려고 비교에만 씀
export type DecisionKind = 'recent' | 'pending' | 'past' | 'other'
export type DecisionSnap = DecisionRow & { kind: DecisionKind }
// ok: 저장소 / none: git 저장소가 아님 / error: git 실행 실패(변경 없음과 구분)
export type GitSnap = { kind: 'ok'; head: string | null; dirty: string[] } | { kind: 'none' } | { kind: 'error'; message: string }
export type GitNow = { snap: GitSnap; commits: string[] }
// board 가 null 이면 현황을 기준으로 삼지 못한 것(사유는 boardReason)
export type Baseline = {
  at: string
  board: { items: ItemSnap[]; decisions: DecisionSnap[]; sourceRows: Record<string, number> } | null
  boardReason: string
  git: GitSnap
}

export type Term = { term: string; meaning: string; match: string[] }

export type BoardData = {
  title: string
  asOf: string
  currentStage: string
  tracks: TrackRow[]
  stages: StageRow[]
  doing: string[]
  nextUp: string[]
  recent: DecisionRow[]
  past: DecisionRow[]
  pending: DecisionRow[]
  // 분류 규칙 밖의 결정 행(표시하지 않음, 변경 탭 비교용)
  unclassified: DecisionRow[]
  glossary: Term[]
  sources: string[]
  loadedAt: string
  warnings: string[]
  // 로드맵 전 항목(하위 포함) — 변경 탭 비교용
  items: ItemSnap[]
  // 읽은 소스별 행 수(로드맵은 항목 수, 결정은 표 행 수) — 소스가 비거나 구성이 바뀐 것을 삭제로 오판하지 않으려는 변경 탭 비교용
  sourceRows: Record<string, number>
  error?: string
}

declare module 'claude-code' {
  interface PluginState {
    'project-board': {
      tab: BoardTab
      data: BoardData | null
      seenTerms: string[]
      baseline: Baseline | null
      git: GitNow | null
      isOff: boolean
      stamps: Record<string, string> | null
      noticeRef: BoardData | null
    }
  }
}
