#!/usr/bin/env bash
# device_settings.sh 시나리오 테스트 — adb stub(설정을 파일에 보관)으로 save → 변경 → diff → restore
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
store="${tmp}/settings"
printf 'system font_scale 1.0\nglobal animator_duration_scale 1.0\n' > "${store}"
cat > "${tmp}/adb" <<STUB
#!/usr/bin/env bash
# adb stub: devices | -s S shell settings get|put|delete ns key [value]
store="${store}"
if [[ "\$1" == "devices" ]]; then printf 'List of devices attached\nSER1\tdevice\n'; exit 0; fi
shift 3            # -s S shell
eval "set -- \$*"  # 실제 adb 처럼 인자를 공백으로 이어 붙여 단말 셸이 다시 해석
shift              # settings
op="\$1" ns="\$2" key="\$3" val="\${4:-}"
case "\$op" in
  get) v="\$(awk -v n="\$ns" -v k="\$key" '\$1 == n && \$2 == k {print \$3}' "\$store")"; echo "\${v:-null}" ;;
  put) grep -v "^\$ns \$key " "\$store" > "\$store.t"; echo "\$ns \$key \$val" >> "\$store.t"; mv "\$store.t" "\$store" ;;
  delete) grep -v "^\$ns \$key " "\$store" > "\$store.t"; mv "\$store.t" "\$store" ;;
esac
STUB
chmod +x "${tmp}/adb"
export ADB="${tmp}/adb" XDG_STATE_HOME="${tmp}/state"
S="${DIR}/device_settings.sh"
pass=0; fail=0
ok() { pass=$((pass + 1)); }
bad() { echo "FAIL $1"; fail=$((fail + 1)); }
bash "${S}" save > /dev/null
if [[ -f "${tmp}/state/device-settings/SER1.txt" ]]; then ok; else bad "save 파일 생성"; fi
"${ADB}" -s SER1 shell settings put system font_scale 1.3
"${ADB}" -s SER1 shell settings put global window_animation_scale 0
out="$(bash "${S}" diff)"
if [[ "${out}" == *"font_scale: 1.0 → 1.3"* && "${out}" == *"window_animation_scale: null → 0"* ]]; then ok; else bad "diff 가 바뀐 키 표시"; fi
out="$(bash "${S}" save)"
if [[ "${out}" == *"기록 유지"* ]]; then ok; else bad "save 는 기존 기록을 덮지 않음"; fi
out="$(bash "${S}" restore)"; rc=$?
if [[ "${rc}" -eq 0 && "${out}" == "restored 8/8 (SER1)" ]]; then ok; else bad "restore 전부 성공"; fi
expected="$(printf 'global animator_duration_scale 1.0\nsystem font_scale 1.0\n' | sort)"
if [[ "$(sort "${store}")" == "${expected}" ]]; then ok; else bad "원래 값 복원·null 키 삭제"; fi
if [[ ! -f "${tmp}/state/device-settings/SER1.txt" && -f "${tmp}/state/device-settings/SER1.txt.restored" ]]; then ok; else bad "복원 후 기록은 .restored 로 보관"; fi
printf '#!/usr/bin/env bash\nexit 1\n' > "${tmp}/adb-broken"; chmod +x "${tmp}/adb-broken"
if ADB="${tmp}/adb-broken" bash "${S}" save -s SER1 --force > /dev/null 2>&1; then bad "adb 실패 시 save 실패"; else ok; fi
# 값에 ; 가 든 키(enabled_input_methods) — 단말 셸 재해석을 거쳐도 값 전체가 복원되는지
ime='com.a/.Ime;1:com.b/.Svc'
printf 'secure enabled_input_methods %s\n' "${ime}" >> "${store}"
f="${tmp}/ime.txt"
export DEVICE_SETTINGS_EXTRA="secure:enabled_input_methods"
bash "${S}" save --file "${f}" > /dev/null
"${ADB}" -s SER1 shell settings put secure enabled_input_methods com.x/.Other
if bash "${S}" restore --file "${f}" > /dev/null 2>&1 \
  && grep -qxF "secure enabled_input_methods ${ime}" "${store}"; then ok; else bad "; 가 든 값 복원"; fi
unset DEVICE_SETTINGS_EXTRA
echo "passed=${pass} failed=${fail}"
[[ "${fail}" -eq 0 ]]
