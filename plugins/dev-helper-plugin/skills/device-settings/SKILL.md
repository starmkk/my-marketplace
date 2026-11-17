---
name: device-settings
description: >
  Android 단말 테스트 전에 바꿀 설정(font_scale·애니메이션 배율·화면 꺼짐 시간 등)을 기록하고 끝나면 반드시
  복원하는 스킬 — scripts/device_settings.sh save·restore·diff. 단말에서 UI·성능·접근성 테스트를 하거나
  `adb shell settings put` 으로 설정을 바꾸기 직전, 단말 테스트가 끝났을 때, "단말 설정 복원", "font_scale",
  "애니메이션 끄기", "기기 설정 원복" 이 언급될 때 사용하라.
---

# device-settings — 단말 설정 기록·복원

설정을 바꾸는 테스트는 반드시 **기록 → 변경 → 복원** 순서로 하고, 보고에 복원 확인 줄을 넣는다.

```bash
S="${CLAUDE_PLUGIN_ROOT}/skills/device-settings/scripts/device_settings.sh"
bash "$S" save    -s <serial>      # 테스트 전 1회 (이미 기록이 있으면 덮지 않음, --force 로 갱신)
bash "$S" diff    -s <serial>      # 기록 대비 바뀐 키
bash "$S" restore -s <serial>      # 끝나면 복원 → "restored N/N" 확인 (기록은 .restored 로 보관)
```

- Bash 도구 호출은 호출마다 셸이 따로임 — `trap ... EXIT` 를 save 와 같은 호출에 두면 **그 호출이 끝나자마자 복원**됨.
  trap 은 테스트 전체를 한 스크립트로 실행할 때만 그 스크립트 안에 둔다:
  `trap 'bash "$S" restore -s <serial> || exit 5' EXIT` (복원 실패가 종료 코드로 드러나게)
- 여러 호출에 걸친 테스트는 마지막에 restore 를 직접 호출하고, 실패·중단으로 끝나도 보고 전에 restore 를 실행한다

- 대상 키: `system font_scale` · `global animator_duration_scale` · `global transition_animation_scale` ·
  `global window_animation_scale` · `global stay_on_while_plugged_in` · `system screen_off_timeout` ·
  `system accelerometer_rotation` · `system user_rotation`. 추가 키는 `DEVICE_SETTINGS_EXTRA="ns:key ns:key"`
- 기록 위치: `${XDG_STATE_HOME:-~/.local/state}/device-settings/<serial>.txt` — 원래 값이 `null` 이면 복원 시 삭제
- 단말 지정: `-s` 가 없으면 `ANDROID_SERIAL`, 둘 다 없고 단말이 여러 대면 중단(다른 세션의 단말을 건드리지 않음)
- 복원 결과가 N/N 이 아니면 남은 키와 현재 값을 보고하고 완료로 보고하지 않는다
- 앱 내부 설정(SharedPreferences 등)은 대상이 아님 — 테스트 코드가 직접 원복
