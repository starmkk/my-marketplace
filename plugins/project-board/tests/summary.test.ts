import { describe, expect, test } from 'claude-code/testing'

import { advanceNotices, boardNotices, comparableReason } from '../hooks/changes'
import { kUnknownStamp, sameStamps, stampOf } from '../hooks/freshness'
import { bandLine, footerLabel } from '../hooks/summary'
import type { BoardData, DecisionRow, ItemSnap } from '../types'

const kBoard = (over: Partial<BoardData> = {}): BoardData => ({
  title: '데모', asOf: '-', currentStage: '-', tracks: [], stages: [], doing: [], nextUp: [],
  recent: [], past: [], pending: [], unclassified: [], glossary: [], sources: [], loadedAt: 'x', warnings: [], items: [],
  sourceRows: { 로드맵: 1, 결정: 1 }, ...over,
})
const item = (id: string, status: string, parent: string | null = null): ItemSnap => ({ id, title: `${id} 제목`, status, parent })
const row = (id: string, topic = `${id} 주제`): DecisionRow => ({ id, topic, detail: '내용', source: '결정' })

describe('footer 라벨', () => {
  test('현재 단계 ID · 전체 진행률 · 미결 수', () => {
    const b = kBoard({
      tracks: [{ name: 'a', done: 3, total: 5, doing: [] }, { name: 'b', done: 4, total: 7, doing: [] }],
      stages: [{ id: 'M0', title: '', status: '완료', isCurrent: false }, { id: 'M3', title: '', status: '진행', isCurrent: true }],
      pending: [row('Q-1'), row('Q-2')],
    })
    expect(footerLabel(b)).toBe('▦ M3 · 7/12 · 미결 2')
  })
  test('로드맵이 없고 미결도 없으면 제목만', () => {
    expect(footerLabel(kBoard())).toBe('▦ 데모')
  })
  test('보드가 없으면 null, 읽기 실패면 실패를 표시', () => {
    expect(footerLabel(null)).toBeNull()
    expect(footerLabel(kBoard({ error: '깨짐' }))).toBe('▦ 데모 · 읽기 실패')
  })
})

describe('밴드 한 줄', () => {
  test('제목·현재 단계·진행 중·미결 수와 여는 방법', () => {
    const line = bandLine(kBoard({ currentStage: 'M3 진행 중 — 접속', doing: ['M3', 'C-B'], pending: [row('Q-1')] }))
    expect(line).toBe('▦ 데모 · M3 진행 중 — 접속 · 진행 중 M3, C-B · 미결 1 — /project-board 로 열기')
  })
  test('진행 중이 없으면 그 칸을 뺌', () => {
    expect(bandLine(kBoard({ currentStage: '로드맵 미설정' }))).toBe('▦ 데모 · 로드맵 미설정 · 미결 0 — /project-board 로 열기')
  })
  test('보드가 없으면 null, 읽기 실패면 실패를 표시', () => {
    expect(bandLine(null)).toBeNull()
    expect(bandLine(kBoard({ error: '깨짐' }))).toBe('▦ 데모 · 읽기 실패: 깨짐 — /project-board 로 열기')
  })
})

describe('변경 감지 지문', () => {
  test('stampOf 는 mtime 과 크기, stat 실패는 알 수 없음', async () => {
    expect(await stampOf(async () => ({ mtimeMs: 10, size: 3 }), 'a')).toBe('10:3')
    expect(await stampOf(async () => { throw new Error('ENOENT') }, 'a')).toBe(kUnknownStamp)
  })
  test('같은 경로·같은 값이면 같음', () => {
    expect(sameStamps({ a: '1:2', b: '3:4' }, { b: '3:4', a: '1:2' })).toBe(true)
  })
  test('값이 다르거나 경로 구성이 다르면 다름', () => {
    expect(sameStamps({ a: '1:2' }, { a: '1:3' })).toBe(false)
    expect(sameStamps({ a: '1:2' }, { a: '1:2', b: '3:4' })).toBe(false)
    expect(sameStamps({ a: '1:2', b: '3:4' }, { a: '1:2' })).toBe(false)
  })
  test('알 수 없는 지문이 하나라도 있으면 같다고 보지 않음(stat 실패로 고착하지 않음)', () => {
    expect(sameStamps({ a: kUnknownStamp }, { a: kUnknownStamp })).toBe(false)
  })
  test('비어 있는 지문은 같다고 보지 않음', () => {
    expect(sameStamps({}, {})).toBe(false)
  })
})

describe('비교 가능 판단', () => {
  test('읽기 실패·경고·소스 구성 변경·행이 있던 소스가 빔은 비교 불가', () => {
    const ok = kBoard()
    expect(comparableReason(ok, ok)).toBeNull()
    expect(comparableReason(ok, null)).toContain('설정 파일')
    expect(comparableReason(ok, kBoard({ error: 'x' }))).toContain('읽기 실패')
    expect(comparableReason(ok, kBoard({ warnings: ['a 없음'] }))).toContain('일부 소스')
    expect(comparableReason(ok, kBoard({ sourceRows: { 로드맵: 1 } }))).toContain('구성')
    expect(comparableReason(ok, kBoard({ sourceRows: { 로드맵: 1, 결정: 0 } }))).toContain('비었음')
  })
})

describe('변화 알림', () => {
  test('상태 변경 2건은 각각', () => {
    const prev = kBoard({ items: [item('M0', '대기'), item('M1', '대기')] })
    const next = kBoard({ items: [item('M0', '완료'), item('M1', '진행')] })
    expect(boardNotices(prev, next)).toEqual(['로드맵 M0: 대기 → 완료', '로드맵 M1: 대기 → 진행'])
  })
  test('상태 변경 3건 이상은 한 줄 요약', () => {
    const prev = kBoard({ items: [item('A', '대기'), item('B', '대기'), item('C', '대기')] })
    const next = kBoard({ items: [item('A', '완료'), item('B', '완료'), item('C', '완료')] })
    expect(boardNotices(prev, next)).toEqual(['로드맵 상태 변경 3건 — 변경 탭 참고'])
  })
  test('결정 필요 추가·이동과 결정됨', () => {
    const prev = kBoard({ pending: [row('Q-1')], recent: [row('Q-3')] })
    const next = kBoard({ pending: [row('Q-2'), row('Q-3')], recent: [row('Q-1')] })
    expect(boardNotices(prev, next)).toEqual(['결정 필요: Q-2 Q-2 주제', '결정 필요: Q-3 Q-3 주제', '결정됨: Q-1 Q-1 주제'])
  })
  test('지난 결정 추가·내용 수정·삭제는 알리지 않음', () => {
    const prev = kBoard({ pending: [row('Q-1')], past: [row('D-1')] })
    const next = kBoard({ pending: [row('Q-1', '바뀐 주제')], past: [row('D-2')] })
    expect(boardNotices(prev, next)).toEqual([])
  })
  test('넘치면 세 줄째를 외 N건으로', () => {
    const prev = kBoard()
    const next = kBoard({ pending: ['Q-1', 'Q-2', 'Q-3', 'Q-4', 'Q-5'].map(id => row(id)) })
    expect(boardNotices(prev, next)).toEqual(['결정 필요: Q-1 Q-1 주제', '결정 필요: Q-2 Q-2 주제', '외 3건 — 변경 탭 참고'])
  })
  test('주제는 한 줄로 자름', () => {
    const next = kBoard({ pending: [row('Q-1', '가'.repeat(80))] })
    const [line] = boardNotices(kBoard(), next)
    expect(line!.length).toBeLessThanOrEqual(60)
  })
  test('비교할 수 없으면 알리지 않음', () => {
    const prev = kBoard({ pending: [row('Q-1')] })
    expect(boardNotices(prev, kBoard({ pending: [row('Q-1'), row('Q-2')], warnings: ['x 없음'] }))).toEqual([])
    expect(boardNotices(kBoard({ error: 'x' }), kBoard({ pending: [row('Q-2')] }))).toEqual([])
  })
})

describe('알림 기준 이동', () => {
  test('처음 읽은 보드는 알리지 않고 기준이 됨, 읽지 못한 보드는 기준이 되지 않음', () => {
    const first = kBoard({ pending: [row('Q-1')] })
    expect(advanceNotices(null, first)).toEqual({ ref: first, lines: [] })
    expect(advanceNotices(null, kBoard({ error: 'x' }))).toEqual({ ref: null, lines: [] })
    expect(advanceNotices(null, null)).toEqual({ ref: null, lines: [] })
  })
  test('비교할 수 있으면 알리고 기준을 옮김', () => {
    const ref = kBoard()
    const next = kBoard({ pending: [row('Q-1')] })
    expect(advanceNotices(ref, next)).toEqual({ ref: next, lines: ['결정 필요: Q-1 Q-1 주제'] })
  })
  test('소스 구성이 바뀌면(설정 변경) 알리지 않고 새 현황이 기준이 됨 — 옛 기준에 고착하지 않음', () => {
    const ref = kBoard()
    const reconfigured = kBoard({ pending: [row('Q-1')], sourceRows: { 로드맵: 1, 새소스: 1 } })
    expect(advanceNotices(ref, reconfigured)).toEqual({ ref: reconfigured, lines: [] })
    const later = kBoard({ pending: [row('Q-1'), row('Q-2')], sourceRows: { 로드맵: 1, 새소스: 2 } })
    expect(advanceNotices(reconfigured, later).lines).toEqual(['결정 필요: Q-2 Q-2 주제'])
  })
  test('읽지 못한 현황은 기준을 바꾸지 않음', () => {
    const ref = kBoard()
    expect(advanceNotices(ref, kBoard({ warnings: ['x 없음'] }))).toEqual({ ref, lines: [] })
  })
  test('비운 상태가 유지되면 그 뒤 변화는 직전 대비로 알림(알림이 조용히 멈추지 않음)', () => {
    const full = kBoard({ items: [item('M0', '대기')], pending: [row('Q-1')], sourceRows: { 로드맵: 1, 결정: 1 } })
    const emptied = kBoard({ items: [item('M0', '대기')], sourceRows: { 로드맵: 1, 결정: 0 } })
    const step1 = advanceNotices(full, emptied, full)
    expect(step1).toEqual({ ref: full, lines: [] })
    const moved = kBoard({ items: [item('M0', '진행')], sourceRows: { 로드맵: 1, 결정: 0 } })
    const step2 = advanceNotices(step1.ref, moved, emptied)
    expect(step2).toEqual({ ref: moved, lines: ['로드맵 M0: 대기 → 진행'] })
  })
  test('소스가 잠깐 비었다가 돌아와도 알림이 쏟아지지 않음(기준을 옮기지 않음)', () => {
    const full = kBoard({ pending: [row('Q-1'), row('Q-2')], sourceRows: { 로드맵: 1, 결정: 2 } })
    const emptied = kBoard({ sourceRows: { 로드맵: 1, 결정: 0 } })
    const step1 = advanceNotices(full, emptied, full)
    expect(step1).toEqual({ ref: full, lines: [] })
    const step2 = advanceNotices(step1.ref, full, emptied)
    expect(step2.lines).toEqual([])
  })
})
