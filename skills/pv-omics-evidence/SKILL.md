---
name: "pv-omics-evidence"
title: "PV Omics Evidence"
version: "1.0.0"
description: "Use when a drug-reaction pair needs mechanistic plausibility context: the drug's mechanism-of-action targets, the safety liabilities recorded for those targets, their GTEx tissue expression in the organ where the reaction occurs, and the Open Targets target-disease association score, each returned as a citable omics: evidence ID read from an offline extract. The output is explanatory population-level context only. Do not use it as a causality verdict, to change the evidence grade, or to argue that a reaction is unlikely because nothing was recorded; absence of mechanistic evidence is not evidence against the association (critic rule R14)."
license: "Apache-2.0"
compatibility: "Reads the offline extract api/_data/omics.json.gz, built from Open Targets, GTEx v10, OLS (EFO), HPO and Mondo queried through ToolUniverse 1.5.7. No network call and no model at runtime; a missing file gives an empty extract. Python 3.11+."
metadata:
  version: "1.0.0"
  author: "Team FlyGate"
  layer: "memory (mushroom body)"
  model: "none (offline extract; no model at runtime)"
  endpoint: "GET /api/omics?drug=<DRUG>&pt=<pt> · GET /api/omics/drugs"
  domain: "pharmacovigilance"
  tags:
    - pharmacovigilance
    - omics
    - mechanistic-plausibility
    - open-targets
    - gtex
    - evidence-ids
---

# 오믹스 근거 (FlyVigilance Omics Evidence v1)

약물-이상반응 쌍 하나에 대해 "이 약의 표적은 무엇이고, 그 표적에 알려진 안전성 책임이 있으며, 반응이 일어나는 장기에서 얼마나 발현되고, 표적과 그 반응 용어 사이에 연관 근거가 있는가"를 네 층의 근거 항목으로 돌려줍니다.
모든 값은 빌드 시점에 공개 DB 에서 뽑아 둔 추출 파일에서 읽으며, 실행 중에는 네트워크도 모델도 쓰지 않습니다.

## When to Use

- System-2 메모가 기전 쪽 맥락을 인용해야 할 때 씁니다. `pv-signal-memory` 의 근거 묶음(`api/_fv/evidence.py::bundle`)이 반응마다 `omics.items_for_memo` 를 붙이므로, 메모가 인용할 수 있는 `omics:` ID 는 그 묶음에 든 것뿐입니다.
- 검토자가 한 쌍의 기전 근거를 층별로 전부 보고 싶을 때 씁니다(`flygate omics`, `GET /api/omics`).

## Do Not Use

- 이 사례의 인과 판단에는 쓰지 않습니다. 기전 근거는 집단 수준의 생물학적 개연성입니다(크리틱 R14).
- 근거 등급을 바꾸는 데 쓰지 않습니다. `api/_fv/grade.py` 는 오믹스를 읽지 않으며, `/api/grade` 응답의 `gaps` 에 "오믹스 근거는 등급에 반영하지 않음"이 붙습니다.
- "기록 없음"을 0 이나 "관련 없음"으로 읽지 않습니다. 기전 근거가 없다는 것은 연관에 반하는 근거가 아닙니다.

## Requirements

자격 증명이 필요 없습니다. 런타임은 `api/_data/omics.json.gz` 만 읽고, 파일이 없으면 빈 구조를 돌려줍니다(모든 쌍이 `found: false`). 추출 파일은 `pipeline/omics/` 의 빌드가 ToolUniverse 로 조회해 만듭니다.

## 네 층과 근거 ID

| 층 | 묻는 것 | 출처 | 근거 ID |
| --- | --- | --- | --- |
| L1 표적 | 약물이 작용하는 유전자 | Open Targets 작용 기전, DGIdb 교차 확인 | `omics:target:<DRUG>:<SYMBOL>@OT<ver>` |
| L2 표적 안전성 | 그 표적을 건드릴 때 알려진 안전성 책임 | Open Targets `safetyLiabilities` | `omics:safety:<SYMBOL>:<eventId or slug>@OT<ver>` |
| L3 조직 발현 | 반응이 일어나는 조직에서의 발현 중앙값(TPM) | GTEx v10 | `omics:gtex:<SYMBOL>:<tissueSiteDetailId>@gtex_v10` |
| L4 표적-질환 연관 | 표적과 그 반응 용어 사이의 연관 점수 | Open Targets 연관 점수와 문헌 제외 점수 | `omics:assoc:<DRUG>:<termId>@OT<ver>` |

- `<DRUG>` 는 `evidence.id_drug` 형태입니다(복합제의 `\` 를 `+` 로 바꿉니다). 쌍 키는 `signals.json.gz` 형태 그대로 `<DRUG>|<pt 소문자>` 입니다.
- 사건 ID 가 없는 안전성 책임은 사건명을 소문자 slug 로 바꿔 ID 에 씁니다.
- 항목은 `{"id", "layer", "what", "n"}` 이고 L2 에는 `match`(`term`, `ancestor`, `none`)가 더 붙습니다. `what` 은 쌍과 무관한 사실만 영어로 적어 같은 ID 는 어느 묶음에서나 같은 문장이며, 모두 "Population-level mechanistic context; not evidence that the drug caused this reaction in this case." 로 끝납니다.
- 쌍 단위 판정(지지, 부분, 없음)은 내지 않습니다. 층별 항목만 냅니다.

## 용어 매핑과 장기 후보 (모델 미사용)

MedDRA 는 라이선스가 필요해 공개 온톨로지 검색으로 PT 를 매핑합니다. 전체 규칙은 `docs/OMICS_DESIGN_v1.0.0-en.md` 3절에 있습니다.

1. `labeltext.is_nonclinical` 인 PT 는 건너뜁니다.
2. PT 를 소문자로 바꾸고 `labeltext.equivalents()` 로 변형을 만든 뒤 OLS(EFO), HPO, Mondo 순서로 검색합니다. 결과의 `label` 이나 `synonyms` 가 변형 하나와 대소문자 무시로 같으면 그 용어를 씁니다(`match: label` 또는 `synonym`).
3. 셋 다 실패하면 `match: none` 입니다. 상위 용어로 올려 붙이지 않습니다. 이때 L2 는 모두 `match: none`, L3 는 TPM 상위 5개, L4 는 없습니다.
4. 장기 후보는 매핑된 용어의 HPO 조상 라벨·동의어의 단어와 GTEx 조직 묶음(`tissueSite`) 이름의 단어가 겹치는지로만 정합니다. 예외 표는 없고, 방법은 `hpo_ancestor_label` 로 어느 조상의 어느 단어가 맞았는지와 함께 기록합니다. 후보가 없으면 L3 는 후보 필터 없이 TPM 상위 5개를 냅니다.
5. L2 의 `match` 는 표적 안전성 책임의 `eventId` 가 매핑된 용어와 같으면 `term`, 그 조상 중 하나이면 `ancestor` 입니다.

## 메모에 들어가는 몫

`items` 는 L1-L4 전부이고 대시보드와 CLI 가 씁니다. `items_for_memo` 는 System-2 메모에 넣는 몫으로 L1 최대 5개, `match` 가 `term` 또는 `ancestor` 인 L2, 장기 후보 안의 L3 중 TPM 상위 5개, L4 1개입니다. 표적이 많은 약물이 프롬프트를 채우지 않게 하려는 상한입니다.

## 하지 않는 일

- R14 를 넘지 않습니다. "기전 근거(표적 안전성 책임, 조직 발현, 표적-질환 연관)는 집단 수준의 생물학적 개연성입니다. 이 사례의 인과를 확립하지 않고, 기전 근거가 없다는 것이 연관에 반하는 근거도 아닙니다." 규칙 원문은 `api/_fv/assess.py::OVERCLAIM_RULES` 의 R14 입니다.
- 등급을 바꾸지 않습니다. `/api/grade` 응답에는 `omics: {"count", "memo_count", "mapping", "found"}` 만 더해집니다.
- 기록 없음과 0 을 섞지 않습니다. 표적 응답에 `safetyLiabilities` 필드가 없으면 `safety: null` 이고 L1 문장은 "nothing recorded, not zero" 라고 적습니다. 빈 목록 `[]` 은 필드가 있고 비어 있다는 뜻입니다. 연관 행이 없으면 L4 점수는 `null` 이고 "nothing recorded, not a zero score" 라고 적습니다. 조회가 실패하면 `null` 과 `errors[]` 항목을 남기며 0 으로 채우지 않습니다.
- L4 에서 `score > 0` 이고 `score_no_literature == 0` 이면 "literature co-mention only" 를 붙입니다. 문헌에 함께 언급된 것 말고는 연관 근거가 없다는 뜻입니다.
- 크리틱 2단의 숫자 허용 오차(`api/_fv/assess.py::tier2_oracle`, 최소 0.011)는 0.0125 와 0.0 을 구별하지 못합니다. v1 은 이 한계를 기록만 하고 고치지 않습니다.

## 정직한 음성 예: 니라파립-혈소판감소증

시험용 추출(`tests/fixtures/omics_fixture.json.gz`)의 `NIRAPARIB|thrombocytopenia` 쌍입니다.

- L1 은 PARP1(`ENSG00000143799`)과 PARP2(`ENSG00000129484`) 두 항목입니다. 두 표적 모두 Open Targets 응답에 안전성 책임 필드가 없어 `n.liabilities` 가 `null` 입니다.
- L2 는 0개입니다. 책임이 "없다"가 아니라 "기록되지 않았다"입니다.
- PT 는 `HP_0001873`(label 일치)으로 매핑되고, 조상 `HP_0001871` 의 단어 "blood" 가 GTEx 묶음 Blood 와 맞습니다. L3 는 Blood 묶음 안의 조직만 내며, 시험용 추출에서는 `Whole_Blood` 하나입니다(TPM 값은 자리 표시입니다).
- L4 는 점수 0.0125, 문헌 제외 점수 0.0 이라 "literature co-mention only" 가 붙습니다.

이 쌍에서 오믹스 층이 주는 것은 적습니다. 메모는 이것을 "기전 근거가 연관을 지지하지 않는다"로 쓰면 안 되고(R14), 라벨과 FAERS 근거는 `pv-signal-memory` 묶음의 다른 ID 로 따로 인용합니다.

## 실행 계약

- CLI `flygate omics <DRUG> "<PT>" [--memo]` (`agent/flygate.py::cmd_omics`). 출력은 `items` 전부(또는 `--memo` 이면 `items_for_memo`)와 `evidence_ids` 입니다. 추출에 없는 약물이나 쌍은 사유와 함께 `{"found": false, "evidence_ids": []}` 를 내고 종료 코드 0 입니다.
- `GET /api/omics?drug=<DRUG>&pt=<pt>` 는 `{drug, pt, asof, pair, items, memo_items}` 를, `GET /api/omics?drug=<DRUG>` 는 그 약물의 쌍 목록을 돌려줍니다. PT 에 `/` 가 들어가는 경우가 있어 경로 변수 대신 쿼리 값을 씁니다. 없으면 404 입니다(`api/index.py::omics_query`).
- `GET /api/omics/drugs` 는 `{asof, drugs}` 입니다(`api/index.py::omics_drugs`).
- 모듈 `api/_fv/omics.py` 의 `pair(drug, pt)`, `drug_pairs(drug)`, `drugs()`, `items(pair)`, `items_for_memo(pair)` 입니다. `pair` 는 입력을 `upper()` 와 `lower()` 로만 정규화합니다.
- 테스트 `tests/test_omics.py`, `tests/test_omics_api.py`, `tests/test_omics_bundle.py` 입니다.

## 자료 출처와 버전

추출 파일의 `versions` 블록이 빌드마다 출처 버전을 기록하고, 근거 ID 의 `@OT<ver>` 와 `@gtex_v10` 가 그 값을 씁니다.

| 키 | 출처 | 값 |
| --- | --- | --- |
| `tooluniverse` | ToolUniverse (`uvx --from tooluniverse==1.5.7 tu run`) | 1.5.7 |
| `opentargets` | Open Targets Platform (`OpenTargets_*` 도구) | 빌드 시 `meta` 에서 기록 |
| `gtex` | GTEx 조직 54개, 묶음 30개 (`GTEx_get_median_gene_expression`, `GTEx_get_tissue_sites`) | `gtex_v10` |
| `ols_efo`, `hpo`, `mondo` | OLS v4 (EFO), HPO (JAX), Mondo 검색 도구 | 조회 시점에 기록 |

시험용 추출의 `opentargets` 값 `25.09` 와 `ols_efo`, `hpo`, `mondo` 의 `placeholder` 는 조회하지 않은 자리 표시입니다(`tests/fixtures/README.md`). 도구 이름과 조회 예시는 `docs/OMICS_DESIGN_v1.0.0-en.md` 2절과 9절에 있습니다.
