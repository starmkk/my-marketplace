// 패널 밖 요약 — footer 라벨과 프롬프트 위 한 줄(패널을 닫은 상태)
import type { BoardData } from '../types'

const kMark = '▦'
const kOpenHint = '/project-board 로 열기'

// '▦ M3 · 7/12 · 미결 2' — 현재 단계 ID, 전체 트랙 완료/전체, 미결 수(없으면 그 칸을 뺌). 아무것도 없으면 제목
export function footerLabel(b: BoardData | null): string | null {
  if (b === null) {
    return null
  }
  if (b.error) {
    return `${kMark} ${b.title} · 읽기 실패`
  }
  const done = b.tracks.reduce((n, t) => n + t.done, 0)
  const total = b.tracks.reduce((n, t) => n + t.total, 0)
  const parts = [
    b.stages.find(s => s.isCurrent)?.id,
    total ? `${done}/${total}` : undefined,
    b.pending.length ? `미결 ${b.pending.length}` : undefined,
  ].filter((p): p is string => p !== undefined)
  return `${kMark} ${parts.length ? parts.join(' · ') : b.title}`
}

// 패널을 닫았을 때 프롬프트 위에 보이는 한 줄
export function bandLine(b: BoardData | null): string | null {
  if (b === null) {
    return null
  }
  if (b.error) {
    return `${kMark} ${b.title} · 읽기 실패: ${b.error} — ${kOpenHint}`
  }
  const parts = [b.title, b.currentStage]
  if (b.doing.length) {
    parts.push(`진행 중 ${b.doing.join(', ')}`)
  }
  parts.push(`미결 ${b.pending.length}`)
  return `${kMark} ${parts.join(' · ')} — ${kOpenHint}`
}
