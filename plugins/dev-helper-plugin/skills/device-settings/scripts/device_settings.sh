#!/usr/bin/env bash
# Android 단말 설정 기록·복원 — save | restore | diff  [-s SERIAL] [--file PATH] [--force]
set -euo pipefail

usage() { echo "usage: $0 save|restore|diff [-s SERIAL] [--file PATH] [--force]" >&2; exit 2; }
[[ $# -ge 1 ]] || usage
cmd="$1"; shift
serial="${ANDROID_SERIAL:-}"
file=""
force=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -s) serial="$2"; shift 2 ;;
    --file) file="$2"; shift 2 ;;
    --force) force=1; shift ;;
    *) usage ;;
  esac
done
ADB="${ADB:-adb}"
if [[ -z "${serial}" ]]; then
  mapfile -t devices < <("${ADB}" devices | awk 'NR > 1 && $2 == "device" {print $1}')
  [[ "${#devices[@]}" -eq 1 ]] || { echo "단말 ${#devices[@]}대 — -s 또는 ANDROID_SERIAL 지정 필요" >&2; exit 3; }
  serial="${devices[0]}"
fi
file="${file:-${XDG_STATE_HOME:-${HOME}/.local/state}/device-settings/${serial}.txt}"
read -r -a keys <<< "system:font_scale global:animator_duration_scale global:transition_animation_scale \
global:window_animation_scale global:stay_on_while_plugged_in system:screen_off_timeout \
system:accelerometer_rotation system:user_rotation ${DEVICE_SETTINGS_EXTRA:-}"

get() { "${ADB}" -s "${serial}" shell settings get "$1" "$2" | tr -d '\r'; }

case "${cmd}" in
  save)
    if [[ -f "${file}" && "${force}" -eq 0 ]]; then
      echo "기록 유지(이미 있음): ${file} — 이전 테스트가 복원하지 않았을 수 있음, 먼저 diff 확인"; exit 0
    fi
    mkdir -p "$(dirname "${file}")"
    tmp="${file}.tmp"
    : > "${tmp}"
    for entry in "${keys[@]}"; do
      ns="${entry%%:*}"; key="${entry#*:}"
      value="$(get "${ns}" "${key}")"  # 대입이라 adb 실패 시 set -e 로 중단됨
      if [[ -z "${value}" ]]; then
        rm -f "${tmp}"; echo "읽기 실패: ${ns} ${key} — 기록하지 않음" >&2; exit 6
      fi
      printf '%s %s %s\n' "${ns}" "${key}" "${value}" >> "${tmp}"
    done
    mv "${tmp}" "${file}"
    echo "saved ${#keys[@]} keys → ${file}"
    ;;
  diff|restore)
    [[ -f "${file}" ]] || { echo "기록 없음: ${file}" >&2; exit 4; }
    total=0; ok=0
    while read -r ns key value; do
      total=$((total + 1))
      current="$(get "${ns}" "${key}")"
      if [[ "${cmd}" == "diff" ]]; then
        [[ "${current}" == "${value}" ]] || echo "${ns} ${key}: ${value} → ${current}"
        continue
      fi
      if [[ "${current}" != "${value}" ]]; then
        if [[ "${value}" == "null" ]]; then
          "${ADB}" -s "${serial}" shell settings delete "${ns}" "${key}" > /dev/null
        else
          # adb shell 은 인자를 공백으로 이어 단말 셸이 다시 해석함 — ;·공백이 든 값
          # (enabled_input_methods 등)이 잘리거나 명령으로 실행되지 않게 값을 인용해 넘김
          "${ADB}" -s "${serial}" shell settings put "${ns}" "${key}" "$(printf '%q' "${value}")"
        fi
      fi
      if [[ "$(get "${ns}" "${key}")" == "${value}" ]]; then ok=$((ok + 1)); else
        echo "복원 실패: ${ns} ${key} (기록 ${value}, 현재 $(get "${ns}" "${key}"))" >&2
      fi
    done < "${file}"
    if [[ "${cmd}" == "restore" ]]; then
      echo "restored ${ok}/${total} (${serial})"
      [[ "${ok}" -eq "${total}" ]] || exit 5
      mv "${file}" "${file}.restored"  # 지우지 않고 보관 — 잘못된 복원 시점이어도 원래 값을 되찾을 수 있게
    fi
    ;;
  *) usage ;;
esac
