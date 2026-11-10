// 소스 파일이 바뀌었는지 판단하는 지문(stamp) — 바뀌지 않았으면 다시 파싱하지 않으려고 씀.
// 지문은 읽기 '전에' 찍는다: 찍은 뒤 읽기 전에 쓰기가 끼면 다음 번 지문이 달라져 다시 읽힘

// stat 이 실패한 경로(없는 파일 포함)의 지문 — 같다고 보지 않아 매번 다시 읽음(stat 실패로 옛 값에 고착하지 않음)
export const kUnknownStamp = '?'

export type StatFile = (path: string) => Promise<{ mtimeMs: number; size: number }>

export async function stampOf(stat: StatFile, path: string): Promise<string> {
  try {
    const s = await stat(path)
    return `${s.mtimeMs}:${s.size}`
  } catch {
    return kUnknownStamp
  }
}

// 경로 구성과 값이 모두 같고, 알 수 없는 지문이 없을 때만 true. 빈 지문은 읽은 적이 없다는 뜻이라 false
export function sameStamps(a: Record<string, string>, b: Record<string, string>): boolean {
  const keys = Object.keys(a)
  if (!keys.length || keys.length !== Object.keys(b).length) {
    return false
  }
  return keys.every(k => a[k] !== kUnknownStamp && a[k] === b[k])
}
