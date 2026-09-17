# 암호 알고리즘 및 키 길이 이용 안내서 (KISA, 2018) — 원문 표 전체 복원

- **문서번호**: KISA-GD-2018-0034
- **발행**: 과학기술정보통신부 / 한국인터넷진흥원(KISA)
- **총 분량**: 16페이지 (표지·판권 포함, 본문 pp.03~14)
- 본 문서는 원본 안내서(스캔 PDF)를 페이지 단위로 직접 판독하여 복원한 것이며, **원문에 없는 내용은 포함하지 않았다.**

---

## 제·개정 이력 (p.02)

| 순번 | 제·개정일 | 제·개정 내역 |
|---|---|---|
| 1 | 2009. 04 | 암호 알고리즘 및 키 길이 이용 안내서 제정 |
| 2 | 2009. 10 | 기관명 변경 |
| 3 | 2013. 01 | 권고 대상 암호 알고리즘 추가 / RSA 공개키 암호 버전 설명 추가 / 해시함수 종류별 용도 설명 / 안전성 유지기간 관련 부가 설명 제시 / 개인정보 관련 암호 알고리즘 적용 예 추가 |
| 4 | 2018. 12 | 국외(NIST, CRYPTREC, ECRYPT)의 권고 대상 암호 알고리즘 업데이트 / 국내 권고 대상 암호 알고리즘 업데이트 / 안내서 활용 예 업데이트 |

문서 구성: 01. 배경 및 필요성 / 02. 보안강도별 권고 암호 알고리즘 / 03. 암호 알고리즘 및 키 길이 선택 기준 / 04. 활용 예

---

## 배경 및 필요성 — 원문 요지 (p.03)

> 정보보호제품 및 시스템에 암호 알고리즘을 탑재·적용하는 경우, 알고리즘의 종류나 키 길이 등은 해당 시스템의 안전성 수준을 만족할 수 있도록 선택해야 한다. 이를 위해 미국, 일본, 유럽 등에서는 암호 알고리즘 및 키 길이에 대한 가이드라인을 제시하고 있다. 그러나 국내의 경우, 국산 암호 알고리즘의 활용비율이 높지만, 국산 암호 알고리즘을 포함한 『암호 알고리즘 및 키 길이 선택』 기준이 없어 이에 대한 개발이 필요하다. 이에, 본 안내서에서는 SEED, HIGHT, ARIA, KCDSA 등의 국산 암호 알고리즘을 포함해 보안강도에 따라 선택 가능한 암호 알고리즘의 종류와 키 길이, 유효기간을 소개한다. **본 안내서에서는 112비트 이상의 안전성을 가지는 알고리즘의 사용을 권고한다.**

### 용어 정의 (p.03 각주 박스)

- **『안전성 수준』**: 시스템이 어느 정도의 보안강도를 만족해야 하는지를 의미함
- **『보안강도』**: 암호 알고리즘이나 시스템의 암호키 또는 해시함수의 취약성을 찾아내는 데 소요되는 작업량을 수치화한 것으로 **112, 128, 192, 256비트**로 정의
  - 112비트의 보안강도란 2^112번의 계산을 해야 암호키 또는 암호 알고리즘의 취약성을 알아낼 수 있음을 의미

### 해시함수 용도 구분 (p.06, p.08)

- **[메시지인증 / 키유도 / 난수생성]용 해시함수** (〈표 3〉 대상)
  - 메시지 인증용: 메시지의 위·변조를 확인하기 위해 해시함수 이용
  - 키유도/난수생성용: 안전한 키와 랜덤한 난수를 생성하기 위해 해시함수 이용
- **[단순해시 / 전자서명]용 해시함수** (〈표 4〉 대상)
  - 패스워드의 안전한 저장이나 효율적인 전자서명 생성을 위해 메시지 압축 시 해시함수 이용

---

## 〈표 1〉 국내외 권고 암호 알고리즘 (p.04~p.05)

| 분류 | | NIST(미국)<br>(2015) | CRYPTREC(일본)<br>(2013) | ECRYPT(유럽)<br>(2018) | 국내<sup>1)</sup><br>(2018) |
|---|---|---|---|---|---|
| **대칭키 암호 알고리즘 (블록암호)** | | AES<br>3TDEA<sup>2)</sup> | AES<br>Camellia | AES<br>Camellia<br>Serpent | **SEED<br>HIGHT<br>ARIA<br>LEA** |
| **해시함수** | | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512 | SHA-256<br>SHA-384<br>SHA-512 | SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/256<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>SHA3-shake128<sup>3)</sup><br>SHA3-shake256<sup>3)</sup><br>Whirlpool-512<br>BLAKE-256<br>BLAKE-384<br>BLAKE-512 | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>**LSH-224<br>LSH-256<br>LSH-384<br>LSH-512<br>LSH-512-224<br>LSH-512-256** |
| **공개키 암호 알고리즘** | 키 공유용 | DH<br>ECDH<br>MQV<br>ECMQV | DH<br>ECDH | ECIES-KEM<br>PSEC-KEM<br>RSA-KEM | DH<br>ECDH |
| | 암·복호화용 | RSA | RSA-OAEP | RSA-OAEP | **RSAES** |
| | 전자서명용 | RSA<br>DSA<br>ECDSA | RSA-PSS<br>RSASSA-PKCS1(v1.5)<br>DSA<br>ECDSA | RSA-PSS<br>ISO-9796-2 RSA-DS2<br>PV Signatures<br>Schnorr<br>ECSchnorr<br>KDSA<sup>4)</sup><br>ECKDSA<sup>4)</sup><br>XMSS | RSA-PSS<br>**KCDSA<br>ECDSA<br>EC-KCDSA** |

**표 각주 (p.05)**

> ※ 본 표에서는 국내외 암호 연구기관에서 발간하는 보고서에서 다루어지는 대표적인 암호 알고리즘들을 언급함
>
> 1) **국내**: 국내 암호 알고리즘은 '검증대상보호함수(IT보안인증사무국)' 국내 표준들을 기반으로 구성하며, 그 외의 암호 알고리즘을 사용할 경우, 국외 권고(안)을 참고하기를 권장함
> 2) **3TDEA**: 세 개의 키가 다른 TDEA(Triple Data Encryption Algorithm)
> 3) **SHA-3 shake128/256**: 가변적 출력 값을 가지며, 안전성이 최대 128/256bit인 SHA-3의 일종
> 4) **KDSA/ECKDSA**: ISO/IEC 14888-3 표준에 있는 KCDSA, EC-KCDSA를 KDSA, ECKDSA로 표기함

### 국산 vs 국제 알고리즘 구분 요약 (〈표 1〉 기반 정리)

| 구분 | 국산 암호 알고리즘 | 국제 암호 알고리즘 (국외 기관 권고) |
|---|---|---|
| 대칭키(블록암호) | SEED, HIGHT, ARIA, LEA | AES, Camellia, Serpent, 3TDEA |
| 해시함수 | LSH 계열(LSH-224/256/384/512, LSH-512-224, LSH-512-256), HAS-160(제한적) | SHA-2 계열, SHA-3 계열, SHA3-shake128/256, Whirlpool-512, BLAKE 계열 |
| 공개키 — 키 공유 | (국내 권고: DH, ECDH) | DH, ECDH, MQV, ECMQV, ECIES-KEM, PSEC-KEM, RSA-KEM |
| 공개키 — 암·복호화 | RSAES | RSA, RSA-OAEP |
| 공개키 — 전자서명 | KCDSA, EC-KCDSA (+ RSA-PSS, ECDSA) | RSA, DSA, ECDSA, RSA-PSS, RSASSA-PKCS1(v1.5), Schnorr, ECSchnorr, PV Signatures, ISO-9796-2 RSA-DS2, XMSS |

---

## 〈표 2〉 보안강도에 따른 대칭키 암호 알고리즘 분류 (p.05~p.06)

> "암호 알고리즘 및 키 길이 선택 안내서는 암호 알고리즘별 보안강도(112, 128, 192, 256비트)를 기반으로 한다." (p.05)

| 보안강도 | NIST(미국) | CRYPTREC(일본) | ECRYPT(유럽) | 국내 |
|---|---|---|---|---|
| **112 비트 이상** | AES-128<br>AES-192<br>AES-256<br>3TDEA | AES-128<br>AES-192<br>AES-256<br>Camellia-128<br>Camellia-192<br>Camellia-256 | AES-128<br>AES-192<br>AES-256<br>Camellia-128<br>Camellia-192<br>Camellia-256<br>Serpent-128<br>Serpent-192<br>Serpent-256 | SEED<br>HIGHT<br>ARIA-128<br>ARIA-192<br>ARIA-256<br>LEA-128<br>LEA-192<br>LEA-256 |
| **128 비트 이상** | AES-128<br>AES-192<br>AES-256 | AES-128<br>AES-192<br>AES-256<br>Camellia-128<br>Camellia-192<br>Camellia-256 | AES-128<br>AES-192<br>AES-256<br>Camellia-128<br>Camellia-192<br>Camellia-256<br>Serpent-128<br>Serpent-192<br>Serpent-256 | SEED<br>HIGHT<br>ARIA-128<br>ARIA-192<br>ARIA-256<br>LEA-128<br>LEA-192<br>LEA-256 |
| **192 비트 이상** | AES-192<br>AES-256 | AES-192<br>AES-256<br>Camellia-192<br>Camellia-256 | AES-192<br>AES-256<br>Camellia-192<br>Camellia-256<br>Serpent-192<br>Serpent-256 | ARIA-192<br>ARIA-256<br>LEA-192<br>LEA-256 |
| **256 비트 이상** | AES-256 | AES-256<br>Camellia-256 | AES-256<br>Camellia-256<br>Serpent-256 | ARIA-256<br>LEA-256 |

---

## 〈표 3〉 보안강도에 따른 메시지인증 / 키유도 / 난수생성용 해시함수 분류 (p.07~p.08)

| 보안강도 | NIST(미국) | CRYPTREC(일본) | ECRYPT(유럽) | 국내 |
|---|---|---|---|---|
| **112 비트 이상** | SHA-1<sup>1)</sup><br>SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512 | SHA-256<br>SHA-384<br>SHA-512 | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>SHA3-shake128<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-224<br>BLAKE-256<br>BLAKE-384<br>BLAKE-512 | HAS-160<sup>2)</sup><br>SHA-1<br>SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>LSH-224<br>LSH-256<br>LSH-384<br>LSH-512<br>LSH-512-224<br>LSH-512-256 |
| **128 비트 이상** | SHA-1<br>SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512 | SHA-256<br>SHA-384<br>SHA-512 | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>SHA3-shake128<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-224<br>BLAKE-256<br>BLAKE-384<br>BLAKE-512 | HAS-160<br>SHA-1<br>SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>LSH-224<br>LSH-256<br>LSH-384<br>LSH-512<br>LSH-512-224<br>LSH-512-256 |
| **192 비트 이상** | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512 | SHA-256<br>SHA-384<br>SHA-512 | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>SHA3-shake128<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-224<br>BLAKE-256<br>BLAKE-384<br>BLAKE-512 | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>LSH-224<br>LSH-256<br>LSH-384<br>LSH-512<br>LSH-512-224<br>LSH-512-256 |
| **256 비트 이상** | SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/256<br>SHA3-256<br>SHA3-384<br>SHA3-512 | SHA-256<br>SHA-384<br>SHA-512 | SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/256<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>SHA3-shake128<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-256<br>BLAKE-384<br>BLAKE-512 | SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/256<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>LSH-256<br>LSH-384<br>LSH-512<br>LSH-512-256 |

**표 3 각주 (p.07) — 사용 제한 알고리즘의 유일한 원문 근거**

> 1) **SHA-1**: 단순해시/전자서명용으로 만족해야 하는 안전성(충돌저항성)이 80비트 보안강도를 제공하지 못하므로(NIST SP 800-56 Rev.4) 사용 불가능하지만, 메시지/키유도/난수생성용으로는 사용 가능함
> 2) **HAS-160**: 단순해시/전자서명용으로 만족해야 하는 안전성(충돌저항성)이 112비트 보안강도를 제공하지 못하므로 사용 불가능하지만, 메시지/키유도/난수생성용으로는 사용 가능함

---

## 〈표 4〉 보안강도에 따른 단순해시 / 전자서명용 해시함수 분류 (p.08~p.09)

※ SHA-1, HAS-160은 이 표(단순해시/전자서명용)에 전혀 등장하지 않는다.

| 보안강도 | NIST(미국) | CRYPTREC(일본) | ECRYPT(유럽) | 국내 |
|---|---|---|---|---|
| **112 비트 이상** | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512 | SHA-256<br>SHA-384<br>SHA-512 | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>SHA3-shake128<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-224<br>BLAKE-256<br>BLAKE-384<br>BLAKE-512 | SHA-224<br>SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/224<br>SHA-512/256<br>SHA3-224<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>LSH-224<br>LSH-256<br>LSH-384<br>LSH-512<br>LSH-512-224<br>LSH-512-256 |
| **128 비트 이상** | SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/256<br>SHA3-256<br>SHA3-384<br>SHA3-512 | SHA-256<br>SHA-384<br>SHA-512 | SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/256<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>SHA3-shake128<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-256<br>BLAKE-384<br>BLAKE-512 | SHA-256<br>SHA-384<br>SHA-512<br>SHA-512/256<br>SHA3-256<br>SHA3-384<br>SHA3-512<br>LSH-256<br>LSH-384<br>LSH-512<br>LSH-512-256 |
| **192 비트 이상** | SHA-384<br>SHA-512<br>SHA3-384<br>SHA3-512 | SHA-384<br>SHA-512 | SHA-384<br>SHA-512<br>SHA3-384<br>SHA3-512<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-384<br>BLAKE-512 | SHA-384<br>SHA-512<br>SHA3-384<br>SHA3-512<br>LSH-384<br>LSH-512 |
| **256 비트 이상** | SHA-512<br>SHA3-512 | SHA-512 | SHA-512<br>SHA3-512<br>SHA3-shake256<br>Whirlpool-512<br>BLAKE-512 | SHA-512<br>SHA3-512<br>LSH-512 |

---

## 〈표 5〉 보안강도에 따른 공개키 암호 알고리즘 분류 (p.09)

### (5-1) 보안강도별 공개키 키 길이

| 보안강도 | 인수분해 문제(비트) | 이산대수 문제 — 공개키(비트) | 이산대수 문제 — 개인키(비트) | 타원곡선(비트) |
|---|---|---|---|---|
| 112 비트 | 2048 | 2048 | 224 | 224 |
| 128 비트 | 3072 | 3072 | 256 | 256 |
| 192 비트 | 7680 | 7680 | 384 | 384 |
| 256 비트 | 15360 | 15360 | 512 | 512 |

### (5-2) 수학적 기반별 알고리즘

| 기반 | NIST(미국) | CRYPTREC(일본) | ECRYPT(유럽) | 국내 |
|---|---|---|---|---|
| **인수분해 문제** | RSA(암,전) | RSA-OAEP(암)<br>RSASSA-PKCS1(v1.5)(전)<br>RSA-PSS(전) | RSA-KEM(키)<br>RSA-OAEP(암)<br>RSA-PSS(전)<br>ISO-9796-2 RSA-DS2(전) | RSAES(암)<br>RSA-PSS(전) |
| **이산대수 문제** | DH(키)<br>DSA(전)<br>MQV(키) | DH(키)<br>DSA(전) | ECIES-KEM(키)<br>Schnorr(전)<br>PV Signatures(전)<br>KDSA(전)<br>XMSS(전) | DH(키)<br>KCDSA(전) |
| **타원곡선** | ECDH(키)<br>ECDSA(전)<br>ECMQV(키) | ECDH(키)<br>ECDSA(전) | PSEC-KEM(키)<br>ECKDSA(전)<br>ECSchnorr(전) | ECDH(키)<br>ECDSA(전)<br>EC-KCDSA(전) |

> ※ 표기 약어 (p.09): **(암)** 메시지 암/복호화용, **(전)** 전자서명용, **(키)** 키 공유용
>
> ※ 타원곡선 기반의 권고 알고리즘 중 암/복호화용은 없음 (p.14 활용 예에서도 재확인)

---

## 〈표 6〉 보안강도별 암호 알고리즘 비교표 — 핵심 종합표 (p.10)

| 보안강도 | 대칭키 암호 알고리즘<br>(보안강도) | 해시함수<br>(보안강도) | 공개키 — 인수분해<br>(비트) | 공개키 — 이산대수<br>공개키(비트) | 공개키 — 이산대수<br>개인키(비트) | 공개키 — 타원곡선 암호<br>(비트) | 암호 알고리즘<br>안전성 유지기간(년도) |
|---|---|---|---|---|---|---|---|
| **112 비트** | 112 | 112 | 2048 | 2048 | 224 | 224 | **2011년에서 2030년까지** |
| **128 비트** | 128 | 128 | 3072 | 3072 | 256 | 256 | **2030년 이후** |
| **192 비트** | 192 | 192 | 7680 | 7680 | 384 | 384 | **2030년 이후** |
| **256 비트** | 256 | 256 | 15360 | 15360 | 512 | 512 | **2030년 이후** |

**안전성 유지기간 요약 (p.10)**

- 112비트 보안강도: 2011년에서 **2030년까지** 안전성 유지
- 128비트 / 192비트 / 256비트 보안강도: **2030년 이후**까지 안전성 유지

---

## 〈표 7〉 암호키 사용 유효기간 (NIST 권고안) (p.11)

**암호키 사용 유효기간 정의 (p.10~11 원문 요지)**

> 암호 알고리즘 키 사용 유효기간이란 암호키를 사용할 수 있는 기간을 말한다. 즉, 암호 알고리즘에 사용되는 키의 사용 유효기간은 송신자가 암호키를 사용하는 기간(예, 암호화 과정)과 수신자가 받은 메시지와 관련된 암호키를 사용하는(예, 복호화 과정) 기간을 포함한다. 〈표 7〉에서는 NIST<sup>1)</sup>의 키관리 권고안을 기반으로 암호키의 사용 유효기간을 제시한다.
>
> 1) NIST Special Publication 800-57, Recommendation for Key Management-Part 1: General(Revision 4)

| 키 종류 | | 사용 유효기간 — 송신자 사용기간 | 사용 유효기간 — 수신자 사용기간 |
|---|---|---|---|
| **대칭키 암호 알고리즘** | 비밀키 | 최대 2년 | 최대 5년<sup>2)</sup> |
| **공개키 암호 알고리즘** | 암호화 공개키 | 최대 2년 | 최대 2년 |
| | 복호화 개인키 | 최대 2년 | 최대 2년 |
| | 검증용 공개키 | 최소 2년 | 최소 2년 |
| | 서명용 개인키 | 최대 2년 | 최대 2년 |

> 2) 수신자의 경우 송신자가 전송한 암호화된 데이터를 수신 한 후 필요시에 복호화 할 수 있으므로 송신자보다 오랜 기간 동안 비밀키를 사용할 수 있음

---

## 활용 예 (4장, p.12~p.14)

### 활용 예 1 — 주민등록번호 및 계좌정보 등 금융정보를 저장하는 경우 (p.12)

| 단계 | 내용 |
|---|---|
| ① | 〈표 6〉에서 현재 2018년 기준으로 안전하게 사용할 수 있는 보안강도(비트) 확인 ⇒ 보안강도: **112비트 이상** |
| ② | 주민등록번호 및 계좌정보 암호화에 필요한 안전한 암호 알고리즘이란 데이터 암·복호화가 가능한 **양방향 암호 알고리즘인 대칭키 암호 알고리즘**이므로 〈표 2〉에서 보안강도 112비트 이상을 제공하는 알고리즘을 확인<br>⇒ AES, SEED, HIGHT, ARIA, LEA 등이 존재<br>⇒ 국내 암호 알고리즘을 고려한다면 SEED, HIGHT, ARIA, LEA 선택 가능 |
| ③ | 〈표 7〉을 참조하여 키 사용 유효기간을 설정(NIST 권고)<br>⇒ 송신자용 암/복호화 비밀키: 최대 2년<br>⇒ 수신자용 암/복호화 비밀키: 최대 5년 |

**[권고]** 보안강도 112비트 이상 대칭키 알고리즘 중 국내 알고리즘 사용 시 **SEED, HIGHT, ARIA, LEA** 중 선택. 비밀키 유효기간은 **송신자용 최대 2년, 수신자용 최대 5년**.

### 활용 예 2 — 비밀번호 정보를 저장하는 경우 (p.13)

| 단계 | 내용 |
|---|---|
| ① | 〈표 6〉에서 현재 2018년 기준으로 안전하게 사용할 수 있는 보안강도(비트) 확인 ⇒ 보안강도: **112비트 이상** |
| ② | 비밀번호 정보 암호화에 필요한 **일방향 암호 알고리즘은 단순해시/전자서명용 해시함수**이므로 〈표 4〉에서 보안강도 112비트 이상을 제공하는 알고리즘을 확인 ⇒ SHA-224, SHA-256, SHA-384, SHA-512 등이 존재하며, 이 중에서 선택 가능 |

**[권고]** 비밀번호 정보에 대해서는 보안강도 112비트 이상을 제공하는 해시함수 중 **SHA-224, SHA-256, SHA-384, SHA-512, SHA-512/224, SHA-512/256, SHA3-224, SHA3-256, SHA3-384, SHA3-512, LSH-224, LSH-256, LSH-384, LSH-512, LSH-512-224, LSH-512-256** 암호 알고리즘 중 선택.

### 활용 예 3 — 대칭키 암호 알고리즘을 적용하여 2025년까지 사용하고자 하는 경우 (p.13)

| 단계 | 내용 |
|---|---|
| ① | 〈표 6〉에서 2025년까지 안전하게 사용하기 위한 보안강도 확인 ⇒ **112비트 이상** |
| ② | 〈표 2〉에서 보안강도 112비트 이상을 제공하는 대칭키 암호 알고리즘 확인 ⇒ AES, SEED, HIGHT, ARIA, LEA 등 존재. 국내 알고리즘 고려 시 SEED, HIGHT, ARIA, LEA 선택 가능 |
| ③ | 〈표 7〉로 키 사용 유효기간 설정 ⇒ 송신자용 최대 2년 / 수신자용 최대 5년 |

**[권고]** 국내 암호 알고리즘 사용 시 **SEED, HIGHT, ARIA, LEA** 중 선택. 비밀키 유효기간 송신자용 최대 2년 / 수신자용 최대 5년.

### 활용 예 4 — 공개키 암호 알고리즘을 적용하여 2035년까지 사용하고자 하는 경우 (p.14)

| 단계 | 내용 |
|---|---|
| ① | 〈표 6〉에서 2035년까지 안전하게 사용하기 위한 보안강도 및 키 길이 확인<br>⇒ 보안강도: **128비트 이상**<br>⇒ 인수분해 기반: 공개키/개인키 **3072비트 이상**<br>⇒ 이산대수 기반: 공개키/개인키 **3072/256비트 이상**<br>⇒ 타원곡선 기반: 공개키/개인키 **256비트 이상** |
| ② | 〈표 5〉에서 공개키 암호 알고리즘 종류 확인<br>※ 타원곡선 기반의 권고 알고리즘 중, 암/복호화용은 없음<br>⇒ **RSAES** 선택 |
| ③ | 〈표 7〉로 키 사용기간 설정 ⇒ 송/수신자용 암/복호화 공개키/개인키: 최대 2년 |

**[권고]**
- 보안강도 **3072비트 이상을 제공하는 공개키/개인키를 갖는 RSAES 선택**
  - 사실, 2018년 기준으로 안전한 암호 알고리즘은 **2048비트 이상**이지만 향후 활용될 시기를 고려해서 **3072비트 이상의 보안강도를 제공하는 암호 알고리즘을 사용하기를 권장함**
- 공개키/개인키 유효기간은 **최대 2년**으로 설정하기를 권장

---

## 안내서 미기재 항목 정리 (진단 시 오용 방지)

| 항목 | 안내서 기재 여부 |
|---|---|
| DES/3DES/MD5/RC4 금지 목록 | **미기재** — 사용 제한 명시는 SHA-1, HAS-160 두 건뿐 (〈표 3〉 각주, p.07). 단, NIST 권고란에 3TDEA는 권고 알고리즘으로 언급됨 |
| 운영모드(ECB/CBC/CTR/GCM)/패딩/IV 주의사항 | **미기재** |
| KDF(PBKDF2, bcrypt, scrypt, Argon2 등) 명칭 | **미기재** — "키유도/난수생성용 해시함수" 용도 분류만 존재 |
| MAC 알고리즘(HMAC, CMAC 등) 명칭 | **미기재** — "메시지인증용 해시함수"로만 분류 |
| 난수 생성 알고리즘(DRBG 등) | **미기재** — "난수생성용 해시함수" 용도로만 언급 |

- p.15는 공백 페이지, p.16은 뒤표지(발행기관 연락처).
