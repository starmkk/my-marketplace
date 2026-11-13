---
name: macos-file-pitfalls
description: >
  macOS 유래 파일 함정 상세 — AppleDouble(`._<filename>`) 파일 제외의 C++·Python·Shell 코드 조각과
  .gitignore·CMake glob 제외, macOS(NFD) ↔ Linux(NFC) 한글 파일 경로 정규화와 glob.glob() 회피를
  다룬다.
  디렉터리를 순회·glob·스캔하는 코드를 작성할 때, 파일 목록(manifest)을 읽어 경로를 여는 코드를
  작성할 때, .gitignore 나 CMakeLists.txt glob 을 고칠 때, 디코딩 실패·파일 개수 불일치·"ls 에는
  보이는데 os.path.exists() 가 False" 증상이 나올 때, "AppleDouble", "._ 파일", "NFD", "NFC",
  "한글 경로", "한글 파일명" 이 언급될 때 사용하라.
  `._*` 제외와 NFC 정규화 원칙은 전역 CLAUDE.md 에 있으며 이 스킬은 그 상세판이다.
---

# macOS 파일 함정 (AppleDouble · NFD/NFC) — 상세

- 전역 `~/.claude/CLAUDE.md` 의 해당 절 원문을 그대로 옮긴 상세판임. 전역 CLAUDE.md 에는
  매 턴 지켜야 할 핵심 규칙과 이 스킬로의 트리거만 남아 있음
- 전역 요약과 어긋나면 이 스킬이 기준임

## macOS AppleDouble Files

Always exclude `._<filename>` files when iterating, globbing, or scanning (symptom: decoding failure
or file count mismatch, never named "AppleDouble").

- C++ → `if (entry.path().filename().string().rfind("._", 0) == 0) continue;`
- Python → `files = [f for f in files if not os.path.basename(f).startswith("._")]`
- Shell → `find . -name "*.wav" ! -name "._*"`
- Add `._*` exclusions to `.gitignore` and to `CMakeLists.txt` glob expressions

## macOS ↔ Linux Korean File Paths (NFD/NFC)

- macOS-generated file lists store Korean names as NFD; on Linux `os.path.exists()` returns False
  although `ls` shows the file → **always apply `unicodedata.normalize('NFC', path)`** (IMPORTANT)
- Avoid `glob.glob()` for such paths (`[]` special characters); use `os.path.exists()` / `os.stat()`
