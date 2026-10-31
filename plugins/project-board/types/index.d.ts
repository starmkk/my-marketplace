export type BoardTab = 'status' | 'terms' | 'decisions'

export type TrackRow = { name: string; done: number; total: number; doing: string[] }
export type StageRow = { id: string; title: string; status: string; isCurrent: boolean }
export type DecisionRow = { id: string; topic: string; detail: string; source: string }
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
  glossary: Term[]
  sources: string[]
  loadedAt: string
  warnings: string[]
  error?: string
}

declare module 'claude-code' {
  interface PluginState {
    'project-board': { tab: BoardTab; data: BoardData | null; seenTerms: string[] }
  }
}
