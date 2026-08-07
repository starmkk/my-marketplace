---
name: cpp-convention
description: >
  C++ 코딩 컨벤션 상세 레퍼런스 — C++17 동시성 패턴(std::async·future·atomic·condition_variable),
  Android NDK r25 전제 조건, CMake C++17 설정, include 순서, 에러 처리 규약을 다룬다.
  C++/C 코드를 작성·수정할 때, 스레드·비동기 처리를 구현할 때, CMakeLists.txt 를 수정할 때,
  "동시성", "std::thread", "std::async", "NDK", "C++17", "include 순서", "브레이스" 가 언급될 때
  사용하라. 브레이스 K&R 적용 예시도 이 스킬이 보유한다.
  들여쓰기·네이밍 같은 기본 규약은 전역 CLAUDE.md 에 있으며 이 스킬은 그 상세판이다.
---

# C++ 코딩 컨벤션 — 상세

전역 `~/.claude/CLAUDE.md` 의 C++ 섹션이 기본 규약(들여쓰기·네이밍·브레이스 원칙·언어별 함수명)을
정의함. 이 문서는 그 상세판이며 **브레이스 적용 예시·동시성·빌드 전제·구조 규약**을 다룸.

## 1. 동시성 — C++17 async 패턴 우선

raw thread 보다 modern C++17 비동기 패턴을 우선함.

- 비블로킹 태스크 실행 → `std::async(std::launch::async, ...)`
- 비동기 결과 처리 → `std::future` / `std::promise`
- `std::thread` 사용 시 **명시적 RAII join wrapper** 를 둠. `std::jthread`(C++20)는 사용 금지
- 중지·취소 신호 → `std::atomic<bool>` (예: `std::atomic<bool> m_stopRequested`)
- lock-free 상태 플래그 → `std::atomic<T>` (예: `std::atomic<bool> m_isRunning`)
- 공유 자원 보호 → `std::mutex` + `std::lock_guard` / `std::unique_lock`
- 생산자-소비자 패턴 → `std::condition_variable` (예: 오디오 버퍼 파이프라인)

### 금지 사항

- detached thread (`std::thread::detach()`) 금지 — joinable 생명주기 관리를 택함
- `std::launch::deferred` 는 지연 평가가 명시적으로 의도된 경우가 아니면 사용 금지

## 2. 동시성 사용 전제 조건 (사용 전 반드시 확인)

- Android NDK **r25 이상** 필요
- `CMakeLists.txt` 에 `set(CMAKE_CXX_STANDARD 17)` 필요
- **MNN 자체는 C++14 기반임.** C++17 동시성은 **앱 계층에만** 적용하고 MNN 내부에는 적용하지 않음
- `CMakeLists.txt` 를 수정할 때는 항상 NDK 버전 호환성을 확인함

## 3. 구조 규약

- `using namespace` **금지**. 전방 선언(forward declaration)을 우선함
- 에러 처리는 **반환값**으로 함. C++ 예외를 쓰지 않음
- include 순서: 짝 헤더 → 프로젝트 헤더 → 라이브러리 헤더 → 표준 라이브러리

## 4. 빌드 스크립트 — compile_commands.json (IMPORTANT)

`scripts/` 의 build 관련 bash 스크립트에서 `cmake -S ... -B ...` 를 호출할 때는
**반드시 `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`** 을 추가함.

- 목적: 컴파일 DB 생성 → Serena/clangd LSP 가 include 경로와 표준 라이브러리 경로를 인식해
  정확한 심볼 분석·진단을 수행
- 누락 시 증상: clangd 가 헤더를 찾지 못해 모든 타입을 `int` 로 추론하는 false-positive 진단이
  다발로 발생
- 생성 위치: 빌드 디렉터리(`build/`). clangd 가 프로젝트 루트에서 자동 탐지하지 못하면 루트에
  심볼릭 링크 추가 권장 — `ln -s build/compile_commands.json .`
- 적용 대상: 프로젝트 자체 소스 빌드는 물론 third_party(MNN 등) 라이브러리 빌드 configure 에도
  동일하게 추가

## 5. 브레이스 스타일 — K&R 적용 예시 (IMPORTANT)

여는 브레이스 `{` 는 **항상 같은 줄**에 둠. 새 줄로 내리지 않음. 구문별 적용 형태는 아래와 같음.

| 구문 | 적용 예시 |
| --- | --- |
| `namespace` | `namespace gemma4 {` |
| `struct` | `struct ManifestReadResult {` |
| `class` | `class LiteRtLmEngine {` |
| 함수 (C/C++) | `bool LiteRtLmEngine::reset_conversation() {` |
| `if` / `else` | `if (condition) {` / `} else {` |
| `for` | `for (int i = 0; i < n; ++i) {` |
| `while` | `while (condition) {` |

- **단일 문장 본문에도 브레이스를 생략하지 않음** — `{}` 를 항상 둠
- 원칙 서술은 전역 `~/.claude/CLAUDE.md` 의 C++ 섹션에 있으며, 이 절은 그 적용 예시임
