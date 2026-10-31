// 기본 개발용어 사전(프로젝트와 무관한 것만). 프로젝트 용어는 .claude/project-board.json 의 glossary 에 둔다.
// match 는 대화 답변에서 찾을 표기(영문은 단어 경계·대소문자 무시, 한글은 포함 여부)
import type { Term } from '../types'

export const kDefaultGlossary: Term[] = [
  { term: 'lint(린트)', meaning: '코드를 실행하지 않고 규칙 위반·실수를 찾는 검사', match: ['lint', '린트'] },
  { term: 'TDD', meaning: '시험을 먼저 써서 실패(RED)를 확인한 뒤 구현해 통과(GREEN)시키는 개발 방식', match: ['TDD'] },
  { term: '단위 시험', meaning: '함수·모듈 하나를 떼어 정상·경계·오류 입력으로 확인하는 시험', match: ['단위 시험', 'unit test', 'unittest'] },
  { term: '음성 시험', meaning: '일부러 위반을 심어 두고 검사기가 그것을 잡아내는지 보는 시험', match: ['음성 시험', '심어 둔 위반'] },
  { term: 'Fake / Mock', meaning: '진짜 대신 쓰는 가짜 구현. 외부 시스템 없이 흐름을 시험할 때 씀', match: ['Fake', 'Mock'] },
  { term: '계약(contract)', meaning: '모듈이 서로 지키기로 한 이름·입출력·오류 규칙', match: ['계약'] },
  { term: '마일스톤', meaning: '개발 단계 묶음. 완료 기준을 함께 둠', match: ['마일스톤', 'milestone'] },
  { term: '게이트', meaning: '다음 단계로 가기 전에 통과해야 하는 검증 관문', match: ['게이트', 'gate'] },
  { term: '스파이크', meaning: '본 개발 전에 기술이 되는지 짧게 실험해 보는 작업', match: ['스파이크', 'spike'] },
  { term: '로드맵', meaning: '단계·작업·선행 관계와 진행 상태를 담은 계획표. 이 패널의 개발 현황 원본', match: ['로드맵', 'roadmap'] },
  { term: 'git 브랜치 / 커밋 / 병합', meaning: '작업 갈래 / 변경 저장 단위 / 갈래를 합치는 일', match: ['브랜치', '커밋', '병합', 'merge', 'commit'] },
  { term: '빨리 감기(fast-forward)', meaning: '갈라진 적 없는 브랜치를 병합 커밋 없이 앞으로 옮기는 병합', match: ['빨리 감기', 'ff-only', 'fast-forward'] },
  { term: 'push', meaning: '로컬 커밋을 원격 저장소(GitHub 등)로 올리는 일', match: ['push', '푸시'] },
  { term: 'git worktree', meaning: '한 저장소에서 여러 작업 폴더를 동시에 쓰는 기능. 작업끼리 섞이지 않게 함', match: ['worktree', '워크트리'] },
  { term: 'handoff(인계 문서)', meaning: '다음 세션이 이 파일 하나만 읽고 이어서 일할 수 있게 쓴 문서', match: ['handoff', '인계'] },
  { term: '서브에이전트', meaning: '메인 대화가 일을 맡기는 별도 AI 작업자', match: ['서브에이전트', 'subagent'] },
  { term: 'dev-log', meaning: '날짜별 개발 기록. 결정·실수·재현 명령을 남김', match: ['dev-log', '개발 로그'] },
  { term: '리팩터링', meaning: '동작은 그대로 두고 코드 구조만 고치는 일', match: ['리팩터링', 'refactor'] },
  { term: '의존성', meaning: '코드가 쓰는 다른 모듈·라이브러리. 방향 규칙을 어기면 구조가 엉킴', match: ['의존성', 'dependency', '의존 규칙'] },
  { term: '빌드', meaning: '소스를 실행 가능한 앱·라이브러리로 만드는 과정', match: ['빌드', 'build'] },
  { term: 'CI', meaning: '변경마다 빌드·시험을 자동으로 돌리는 체계', match: ['CI'] },
  { term: '실기기 / 시뮬레이터', meaning: '진짜 기기 / 컴퓨터에서 흉내 내는 가상 기기', match: ['실기기', '시뮬레이터', 'simulator'] },
  { term: '오픈소스 라이선스 고지', meaning: '쓰는 오픈소스의 라이선스 전문을 제품에 표시하는 의무', match: ['라이선스', '고지', 'license'] },
  { term: '플러그인 / mod', meaning: 'Claude Code 에 기능·패널을 더하는 확장. 이 패널 자체', match: ['플러그인', 'plugin', 'mod'] },
]

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function findTerms(text: string, glossary: Term[]): string[] {
  const found: string[] = []
  for (const t of glossary) {
    const hit = t.match.some(w => {
      const isLatin = /^[\x20-\x7e]+$/.test(w)
      const re = isLatin ? new RegExp(`(^|[^A-Za-z0-9_])${escapeRe(w)}([^A-Za-z0-9_]|$)`, 'i') : new RegExp(escapeRe(w))
      return re.test(text)
    })
    if (hit && !found.includes(t.term)) {
      found.push(t.term)
    }
  }
  return found
}

// 새로 나온 용어를 앞에 두고 중복 제거, 최대 limit 개
export function mergeSeen(prev: string[], found: string[], limit = 40): string[] {
  return [...found, ...prev.filter(t => !found.includes(t))].slice(0, limit)
}
