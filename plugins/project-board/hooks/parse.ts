// 프로젝트 문서(HTML·Markdown·JSON)에서 패널 데이터를 뽑는 순수 함수 모음.
// 무엇을 어디서 읽을지는 프로젝트의 .claude/project-board.json(BoardConfig)이 정한다.
import type { BoardData, DecisionRow, ItemSnap, StageRow, Term, TrackRow } from '../types'

// ---- 설정 ----

export type RoadmapSource = {
  file: string
  // html-script: HTML 안 <script id="<id>"> 의 JSON / json: 파일 전체가 JSON
  format: 'html-script' | 'json'
  id?: string
  // 상태 이름(프로젝트 표기). 기본값은 한국어 5종
  statuses?: Partial<Record<'done' | 'doing' | 'waiting' | 'hold' | 'decision', string>>
  // 현재 단계를 고를 트랙 키. 비우면 전체 트랙
  stageTracks?: string[]
}

export type DecisionSource = {
  file: string
  label: string
  // html-table: <tr><td>ID</td>… 행 / md-table: | ID | … | 행
  format: 'html-table' | 'md-table'
  idPrefix: string
  // 0 기반 칸 번호(ID 칸 = 0). 음수는 뒤에서부터(-1 = 마지막 칸)
  topicColumn?: number
  detailColumn?: number
  statusColumn?: number
  // past: 모든 행이 지난 결정 / classify: decided·pending 정규식으로 상태 칸을 판정(어디에도 안 맞으면 제외)
  kind: 'past' | 'classify'
  decided?: string
  pending?: string
}

export type BoardConfig = {
  title?: string
  roadmap?: RoadmapSource
  decisions?: DecisionSource[]
  glossary?: Term[]
  includeDefaultGlossary?: boolean
}

// 로컬 시각 'YYYY-MM-DD HH:mm' (toISOString 은 UTC 라 쓰지 않음)
export function formatLocalTime(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

// /project-board 인자: '' 와 on = 열기, off = 닫기(대소문자·앞뒤 공백 허용), 그 밖은 null
export function parseBoardCommand(args: string | undefined): 'on' | 'off' | null {
  const a = (args ?? '').trim().toLowerCase()
  return a === '' || a === 'on' ? 'on' : a === 'off' ? 'off' : null
}

export const kConfigPath = '.claude/project-board.json'
export const kDefaultTitle = 'Project Board'

// 설정에 title 이 없을 때 쓰는 패널 제목 = 작업 폴더 이름
export function folderTitle(cwd: string): string {
  const name = cwd.replace(/[\\/]+$/, '').split(/[\\/]/).pop() ?? ''
  return name || kDefaultTitle
}

export type Roadmap = {
  as_of?: string
  tracks: { key: string; name: string }[]
  items: {
    id: string
    track: string
    parent: string | null
    title: string
    deps: string[]
    status: string
  }[]
}
type Item = Roadmap['items'][number]

const kDefaultStatuses = { done: '완료', doing: '진행', waiting: '대기', hold: '보류', decision: '결정 필요' }
const kMaxCell = 140

// 설정 파일 검사 — 잘못된 곳을 문장으로 돌려줌(빈 배열이면 정상)
export function validateConfig(raw: unknown): string[] {
  const errors: string[] = []
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return ['설정은 JSON 객체여야 함']
  }
  const c = raw as Record<string, unknown>
  const rm = c.roadmap as Record<string, unknown> | undefined
  if (rm !== undefined) {
    if (typeof rm.file !== 'string') {
      errors.push('roadmap.file 은 문자열')
    }
    if (rm.format !== 'html-script' && rm.format !== 'json') {
      errors.push('roadmap.format 은 html-script 또는 json')
    }
    if (rm.format === 'html-script' && typeof rm.id !== 'string') {
      errors.push('roadmap.format=html-script 이면 roadmap.id 필요')
    }
  }
  const ds = c.decisions
  if (ds !== undefined && !Array.isArray(ds)) {
    errors.push('decisions 는 배열')
  }
  ;(Array.isArray(ds) ? ds : []).forEach((d: Record<string, unknown>, i: number) => {
    for (const k of ['file', 'label', 'idPrefix']) {
      if (typeof d[k] !== 'string') {
        errors.push(`decisions[${i}].${k} 는 문자열`)
      }
    }
    if (d.format !== 'html-table' && d.format !== 'md-table') {
      errors.push(`decisions[${i}].format 은 html-table 또는 md-table`)
    }
    if (d.kind !== 'past' && d.kind !== 'classify') {
      errors.push(`decisions[${i}].kind 는 past 또는 classify`)
    }
    if (d.kind === 'classify' && typeof d.decided !== 'string' && typeof d.pending !== 'string') {
      errors.push(`decisions[${i}] classify 는 decided 나 pending 정규식이 필요`)
    }
    for (const k of ['decided', 'pending']) {
      if (typeof d[k] === 'string') {
        try {
          new RegExp(d[k] as string)
        } catch {
          errors.push(`decisions[${i}].${k} 정규식 오류`)
        }
      }
    }
  })
  const g = c.glossary
  if (g !== undefined && (!Array.isArray(g) || g.some(t => typeof t?.term !== 'string' || typeof t?.meaning !== 'string' || !Array.isArray(t?.match)))) {
    errors.push('glossary 는 { term, meaning, match[] } 배열')
  }
  return errors
}

// ---- 텍스트 도구 ----

export function plainText(html: string): string {
  return html
    .replace(/<[^>]*>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim()
}

export function clip(text: string, max = kMaxCell): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

export function cell(text: string): string {
  return text.replace(/(?<!\\)\|/g, '\\|').replace(/\n/g, ' ')
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function pick<T>(list: T[], index: number): T | undefined {
  return index < 0 ? list[list.length + index] : list[index]
}

// ---- 로드맵 ----

export function parseRoadmap(text: string, src: RoadmapSource): Roadmap {
  let json = text
  if (src.format === 'html-script') {
    const re = new RegExp(`<script[^>]*id="${escapeRe(src.id ?? '')}"[^>]*>([\\s\\S]*?)</script>`)
    const m = text.match(re)
    if (!m) {
      throw new Error(`${src.file} 에 <script id="${src.id}"> 없음`)
    }
    json = m[1] ?? ''
  }
  const rm = JSON.parse(json) as Roadmap
  if (!Array.isArray(rm.items) || !Array.isArray(rm.tracks)) {
    throw new Error('로드맵 JSON 에 tracks·items 배열이 없음')
  }
  return rm
}

// 하위 항목은 상위의 선행을 물려받음
function effectiveDeps(item: Item, byId: Map<string, Item>): string[] {
  const out = [...(item.deps ?? [])]
  let p = item.parent ? byId.get(item.parent) : undefined
  while (p) {
    for (const d of p.deps ?? []) {
      if (!out.includes(d)) {
        out.push(d)
      }
    }
    p = p.parent ? byId.get(p.parent) : undefined
  }
  return out
}

export function summarizeRoadmap(rm: Roadmap, src: Pick<RoadmapSource, 'statuses' | 'stageTracks'> = {}) {
  const st = { ...kDefaultStatuses, ...src.statuses }
  const byId = new Map(rm.items.map(i => [i.id, i]))
  const startable = (i: Item) => {
    if (i.status !== st.waiting) {
      return false
    }
    if (effectiveDeps(i, byId).some(d => byId.get(d)?.status !== st.done)) {
      return false
    }
    const p = i.parent ? byId.get(i.parent) : undefined
    return !(p && (p.status === st.hold || p.status === st.decision))
  }
  const parents = new Set(rm.items.filter(i => i.parent).map(i => i.parent as string))
  const leaves = rm.items.filter(i => !parents.has(i.id))
  const tracks: TrackRow[] = rm.tracks.map(t => {
    const lv = leaves.filter(i => i.track === t.key)
    return {
      name: t.name,
      done: lv.filter(i => i.status === st.done).length,
      total: lv.length,
      doing: rm.items.filter(i => i.track === t.key && !i.parent && i.status === st.doing).map(i => i.id),
    }
  })
  const doing = rm.items.filter(i => i.status === st.doing && !i.parent).map(i => i.id)
  const nextUp = rm.items
    .filter(i => startable(i) && (!i.parent || byId.get(i.parent)?.status === st.doing))
    .map(i => i.id)
  const keys = src.stageTracks?.length ? src.stageTracks : rm.tracks.map(t => t.key)
  const top = rm.items.filter(i => !i.parent && keys.includes(i.track))
  const current = top.find(i => i.status === st.doing) ?? top.find(startable)
  const stages: StageRow[] = rm.items
    .filter(i => !i.parent)
    .map(i => ({ id: i.id, title: clip(i.title, 70), status: i.status, isCurrent: i === current }))
  const currentStage = current
    ? `${current.id} ${current.status === st.doing ? '진행 중' : '착수 가능'} — ${clip(current.title, 60)}`
    : '착수 가능한 단계 없음'
  const items: ItemSnap[] = rm.items.map(i => ({ id: i.id, title: clip(i.title, 60), status: i.status, parent: i.parent ?? null }))
  return { asOf: rm.as_of ?? '-', tracks, stages, doing, nextUp, currentStage, items }
}

// ---- 결정 표 ----

export function tableRows(text: string, src: Pick<DecisionSource, 'format' | 'idPrefix'>): string[][] {
  const prefix = escapeRe(src.idPrefix)
  if (src.format === 'html-table') {
    const out: string[][] = []
    // 행 경계 안에서만 매칭 — `.*?` 가 뒤쪽 행으로 넘어가는 오탐 방지
    const re = new RegExp(`<tr>\\s*<td>${prefix}-\\d+</td>(?:(?!</tr>).)*?</tr>`, 'gs')
    for (const m of text.matchAll(re)) {
      out.push([...m[0].matchAll(/<td[^>]*>((?:(?!<\/td>).)*?)<\/td>/gs)].map(c => c[1] ?? ''))
    }
    return out
  }
  const out: string[][] = []
  const re = new RegExp(`^\\|\\s*${prefix}-\\d+\\s*\\|.*\\|\\s*$`)
  for (const line of text.split('\n')) {
    if (re.test(line)) {
      out.push(line.trim().slice(1, -1).split(/(?<!\\)\|/).map(c => c.trim()))
    }
  }
  return out
}

export function parseDecisions(text: string, src: DecisionSource): { decided: DecisionRow[]; pending: DecisionRow[]; past: DecisionRow[]; other: DecisionRow[] } {
  const res = { decided: [] as DecisionRow[], pending: [] as DecisionRow[], past: [] as DecisionRow[], other: [] as DecisionRow[] }
  const toText = (s: string) => (src.format === 'html-table' ? plainText(s) : s.replace(/\*\*/g, ''))
  const decided = src.decided ? new RegExp(src.decided) : null
  const pending = src.pending ? new RegExp(src.pending) : null
  for (const cells of tableRows(text, src)) {
    const row: DecisionRow = {
      id: toText(cells[0] ?? ''),
      topic: clip(toText(pick(cells, src.topicColumn ?? 1) ?? ''), 90),
      detail: clip(toText(pick(cells, src.detailColumn ?? -1) ?? '')),
      source: src.label,
      sig: cells.map(toText).join('\u0000'),
    }
    if (src.kind === 'past') {
      res.past.push(row)
      continue
    }
    const status = pick(cells, src.statusColumn ?? -1) ?? ''
    if (decided?.test(status)) {
      res.decided.push(row)
    } else if (pending ? pending.test(status) : true) {
      res.pending.push(row)
    } else {
      res.other.push(row)
    }
  }
  return res
}

// ---- 조립 ----

// 같은 term 은 프로젝트 쪽이 기본값을 덮어씀
export function mergeGlossary(defaults: Term[], project: Term[]): Term[] {
  const names = new Set(project.map(t => t.term))
  return [...defaults.filter(t => !names.has(t.term)), ...project]
}

export type ReadFile = (path: string) => Promise<string | null>

export async function buildBoard(
  config: BoardConfig,
  read: ReadFile,
  defaults: Term[],
  loadedAt: string,
  fallbackTitle = kDefaultTitle,
): Promise<BoardData> {
  const warnings: string[] = []
  const board: BoardData = {
    title: config.title ?? fallbackTitle,
    asOf: '-',
    currentStage: '로드맵 미설정',
    tracks: [],
    stages: [],
    doing: [],
    nextUp: [],
    recent: [],
    past: [],
    pending: [],
    unclassified: [],
    glossary: mergeGlossary(config.includeDefaultGlossary === false ? [] : defaults, config.glossary ?? []),
    sources: [],
    loadedAt,
    warnings,
    items: [],
    sourceRows: {},
  }
  const cache = new Map<string, string | null>()
  const load = async (file: string) => {
    if (!cache.has(file)) {
      cache.set(file, await read(file))
    }
    const text = cache.get(file) ?? null
    if (text === null) {
      warnings.push(`${file} 없음`)
    } else if (!board.sources.includes(file)) {
      board.sources.push(file)
    }
    return text
  }
  if (config.roadmap) {
    const text = await load(config.roadmap.file)
    if (text !== null) {
      try {
        Object.assign(board, summarizeRoadmap(parseRoadmap(text, config.roadmap), config.roadmap))
        board.sourceRows[`로드맵 ${config.roadmap.file}`] = board.items.length
      } catch (err) {
        warnings.push(err instanceof Error ? err.message : String(err))
      }
    }
  }
  for (const src of config.decisions ?? []) {
    const text = await load(src.file)
    if (text === null) {
      continue
    }
    const d = parseDecisions(text, src)
    board.recent.push(...d.decided)
    board.pending.push(...d.pending)
    board.past.push(...d.past)
    board.unclassified.push(...d.other)
    board.sourceRows[`${src.label} (${src.file})`] = d.decided.length + d.pending.length + d.past.length + d.other.length
  }
  return board
}
