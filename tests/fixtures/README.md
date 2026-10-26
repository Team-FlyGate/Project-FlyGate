# tests/fixtures

## omics_fixture.json.gz

`tests/test_omics.py` 가 쓰는 오믹스 추출 파일입니다. 형식은 `api/_data/omics.json.gz` 와 같습니다
(설계 `docs/OMICS_DESIGN_v1.0.0-en.md` 4절, 여기에 `gtex_tissues` 표를 더했습니다). 내용은 `zcat` 으로 봅니다.

```bash
zcat tests/fixtures/omics_fixture.json.gz | python3 -m json.tool
```

직렬화는 `json.dumps(x, ensure_ascii=False, separators=(",", ":"))` 를 `gzip` (`mtime=0`, 파일명 빈칸)으로 감쌌습니다.
티켓 02 의 캐시 재생 테스트가 같은 방식으로 쓰면 바이트 단위로 같아집니다.

두 약물과 세 쌍을 담습니다.

| 쌍 | 보는 경우 |
|---|---|
| `NIRAPARIB\|thrombocytopenia` | 정직한 음성. 두 표적 모두 `safety: null`, 장기 후보 `Blood`, L4 는 문헌 동시 언급만 |
| `CLOZAPINE\|catalepsy` | L2 가 용어와 맞는 쌍(`relation: term`). 장기 후보가 없어 L3 는 TPM 상위 5개, L4 는 연관 행 없음 |
| `CLOZAPINE\|some unmapped term` | 매핑 실패(`match: none`). L4 없음, L2 는 모두 `none` |

### 실제 조회값

설계 문서 2절과 4절에 적힌, 2026-10-26 ToolUniverse 1.5.7 조회 결과입니다.

- NIRAPARIB `CHEMBL1094636`, 표적 PARP1 `ENSG00000143799`, PARP2 `ENSG00000129484`
- PARP1 기전 문자열 "Poly [ADP-ribose] polymerase-1 inhibitor"
- PARP1, PARP2 응답에 `safetyLiabilities` 필드가 없음(`safety: null`)
- DRD2 `ENSG00000149295` 의 "catalepsy" 항목: `EFO_0009845`, UBERON 조직 4개, Lynch et al. (2017), PMID 28216264
- thrombocytopenia 의 `HP_0001873` 과 조상 4개, `HP_0001871` 과 GTEx "Blood" 의 단어 일치
- L4 점수 0.0125 와 문헌 제외 점수 0.0 (파일럿)
- GTEx 조직 이름 `Whole_Blood`, `Liver`, `Brain_Cortex` 과 묶음 `Blood`, `Liver`, `Brain`

### 자리 표시 값 (조회하지 않음)

아래 값은 테스트용으로 넣었고 생물학 사실이 아닙니다. 티켓 02 빌드가 실제 값으로 바꿉니다.

| 위치 | 값 |
|---|---|
| `targets.*.gtex` | 모든 TPM 숫자 |
| `versions.opentargets` | `25.09` |
| `versions.ols_efo`, `hpo`, `mondo` | `placeholder` |
| `drugs.CLOZAPINE.chembl_id` | `placeholder` |
| PARP1 `moa` 의 `action` `INHIBITOR`, `dgidb` | 설계 예시를 따름 |
| PARP2, DRD2 `moa` 의 `action`, `mechanism`, `dgidb` | `placeholder`, `null` |
| DRD2 `safety[1]` | `event_id` 없는 항목을 보려고 넣은 가짜 책임("placeholder liability") |
| `terms.catalepsy` | `label`, `source`, `ancestors: []`, `organs: null` |
| `pairs.CLOZAPINE\|catalepsy.assoc` | `row_found: false`, 점수 `null` |

상한(5개), 복합제 키(`\`), 문헌 제외 점수가 0보다 큰 L4 는 `test_omics.py` 의 `synthetic()` 이 만드는 합성 추출로
봅니다. 그 안의 유전자·조직 이름(`GENE1`, `X1` 등)은 모두 가짜입니다.
