# FlyVigilance 오믹스 근거 층 설계

판: v1.0.0 · 작성일: 2026-10-26 · 상태: 검토 대기 · 영어판은 [OMICS_DESIGN_v1.0.0-en.md](OMICS_DESIGN_v1.0.0-en.md)

FlyVigilance는 지금 "보고되었는가"(FAERS 불균형 지표), "라벨에 적혀 있는가"(openFDA), "문헌에 있는가"(PubMed) 세 축으로 약물-이상반응 쌍을 평가합니다. 이 문서는 네 번째 축 "생물학적으로 그럴 수 있는가"를 더하는 설계입니다. 약의 작용 표적 유전자를 거쳐 표적 안전성, 조직 발현, 표적-질환 연관을 공개 오믹스 데이터베이스에서 조회하고 그 결과를 기존 근거 ID 체계에 `omics:` 접두사로 넣습니다. 숙고 층(System-2) 메모는 이 항목을 인용하고, 크리틱은 이를 검사하며, 대시보드는 표로 보여 줍니다. 근거 등급과 PV 분류에는 넣지 않으며 그 이유는 1절에 적은 지난 파일럿 결과에 있습니다.

## 1. 왜 지금, 왜 이렇게

2026-09-28 파일럿([EVALUATION.md 7절](EVALUATION.md))은 Open Targets 표적-질환 연관 점수 하나로 SIDER 라벨 기재 쌍을 가려 보았습니다. 결과는 AUC 0.559, 귀무 0.532였고 같은 행에서 PRR 0.570, ROR 하한 0.625, IC025 0.638, 카이제곱 0.679였습니다. 점수가 0인 행이 68.4%였고 0이 아닌 행 가운데 절반 이상은 문헌 동시 언급만으로 점수를 받았습니다. PT 3,929개 가운데 963개(24.5%)만 온톨로지 용어로 매핑되었습니다.

이 결과로 세 가지를 정했습니다.

1. 오믹스 점수 하나로 신호의 순위를 매기지 않습니다. v1은 설명용 근거이고 점수 축(역할 B)은 참조 세트에서 귀무를 이긴 뒤에만 넣습니다.
2. 층을 넷으로 나눕니다. 파일럿의 연관 점수 외에 표적 안전성 책임(target safety liabilities)과 GTEx 조직 발현을 더합니다. 문헌만으로 점수를 받는 행을 따로 표시합니다.
3. 이름 정확 일치 대신 동의어 검색을 써서 PT 매핑 적용 범위를 먼저 넓힙니다.

발표 마감은 2026-10-29이고 시연은 2026-11-10 flygate.kr입니다. v1은 마감 안에 측정할 수 있는 것만 담습니다.

## 2. 무엇이 어디서 오는가

네 층 모두 ToolUniverse 1.5.7(`uvx --from tooluniverse==1.5.7 tu run`)로 2026-10-26에 컴퓨트 노드에서 조회해 응답 모양을 확인했습니다. 이때의 응답은 캐시하지 않았고, 빌드가 같은 질의를 다시 보내 `$OMICS_DIR` 아래에 캐시합니다. 도구 이름은 ToolUniverse 등록 이름 그대로입니다.

| 층 | 묻는 것 | 도구 | 응답에서 쓰는 것 | 근거 ID |
|---|---|---|---|---|
| L1 표적 | 이 약은 어떤 유전자에 작용하는가 | `OpenTargets_get_drug_chembId_by_generic_name` → `OpenTargets_get_drug_mechanisms_of_action_by_chemblId`. `DGIdb_get_drug_gene_interactions`로 교차 확인 | `targets[].id`(Ensembl), `approvedSymbol`, `actionType`, `mechanismOfAction`, `references[]` | `omics:target:<DRUG>:<SYMBOL>@OT<ver>` |
| L2 표적 안전성 | 이 표적을 건드리면 어떤 이상이 알려져 있는가 | `OpenTargets_get_target_safety_profile_by_ensemblID` | `safetyLiabilities[].event`, `eventId`(HP/EFO/MONDO), `biosamples[].tissueId`(UBERON), `effects[]`, `datasource`, `literature`(PMID) | `omics:safety:<SYMBOL>:<eventId 또는 slug>@OT<ver>` |
| L3 조직 발현 | 이 표적은 반응이 생기는 조직에서 얼마나 발현되는가 | `GTEx_get_median_gene_expression`(`dataset_id="gtex_v10"`), 조직 목록은 `GTEx_get_tissue_sites` | `median`(TPM), `tissueSiteDetailId`, `tissueSite`, `ontologyId`(UBERON). 54 세부 조직, 30 조직 그룹 | `omics:gtex:<SYMBOL>:<tissueSiteDetailId>@gtex_v10` |
| L4 표적-질환 연관 | 이 표적과 이 반응 용어 사이에 연관 근거가 있는가 | 파일럿의 Open Targets GraphQL(`associatedDiseases`, 문헌 제외 별칭 포함)을 그대로 이식 | `score`, `score_no_literature`, `datatypeScores[]` | `omics:assoc:<DRUG>:<termId>@OT<ver>` |
| 용어 매핑 | 이 PT는 어떤 온톨로지 용어인가 | `ols_search_efo_terms`, `HPO_search_terms`, `Mondo_search_disease`, `OpenTargets_get_disease_ancestors_parents_by_efoId`, `HPO_get_term_hierarchy`, `HPO_get_term` | `obo_id`/`id`, `label`/`name`, `synonyms`, `ancestors` | 근거 ID 없음. `terms` 표에 출처와 일치 종류를 기록 |

확인한 응답을 예로 들면 니라파립은 `CHEMBL1094636`, 작용 기전 표적은 PARP1(`ENSG00000143799`, "Poly [ADP-ribose] polymerase-1 inhibitor")과 PARP2(`ENSG00000129484`)입니다. PARP1과 PARP2 모두 응답에 `safetyLiabilities` 필드가 없었습니다. 빌드는 이를 "Open Targets에 기록 없음"으로 적고 0과 구별합니다. DRD2(`ENSG00000149295`)는 "catalepsy"(`EFO_0009845`, 조직 UBERON 4개, 출처 Lynch et al. 2017, PMID 28216264)처럼 이벤트 ID와 조직 ID가 붙은 항목을 돌려줍니다. GTEx v10의 PARP1 중앙값은 Whole_Blood를 포함한 54개 조직의 TPM 값으로 돌아옵니다. OLS에서 "Thrombocytopenia"는 첫 결과가 `HP_0001873`, 라벨 정확 일치입니다. `OpenTargets_get_disease_ancestors_parents_by_efoId`가 준 상위 용어는 `HP_0011875`, `HP_0001871`, `HP_0000118`, `EFO_0000651`입니다.

HPA(`HPA_get_gene_basic_info_by_ensembl_id`)는 PARP1에 대해 조직 특이 nTPM을 `null`로 돌려주었습니다. 단백체 층(L6)은 v1에서 뺍니다.

## 3. PT 매핑 규칙

MedDRA는 사용권이 필요하고 이 저장소에는 PT 이름만 있습니다(`api/_fv/labeltext.py`의 철자, 어순, 동의어 사전 `EQUIV`가 전부입니다). 그래서 매핑은 공개 온톨로지 검색으로 합니다.

1. `labeltext.is_nonclinical`인 PT(예: drug ineffective)는 건너뜁니다.
2. PT를 소문자로 정규화하고 `labeltext.equivalents()`가 주는 변형(미국식 철자, 어순 뒤집기, `EQUIV` 동의어)을 만듭니다.
3. `ols_search_efo_terms`(rows 5), `HPO_search_terms`(5), `Mondo_search_disease`(5)를 순서대로 부릅니다. 어떤 결과의 `label` 또는 `synonyms`가 변형 중 하나와 대소문자 무시로 같으면 그 용어를 쓰고 일치 종류를 `label`, `synonym`으로 적습니다.
4. 셋 다 실패하면 `match: none`이고 첫 결과는 참고로만 남깁니다. 질환 용어와 표현형 용어를 한 척도로 섞는 문제를 먼저 재야 하므로 매핑이 안 된 PT를 상위 용어로 올려 잡는 규칙은 v1에서 쓰지 않습니다.
5. 매핑된 용어의 상위 용어를 `OpenTargets_get_disease_ancestors_parents_by_efoId`로 받습니다. 그 용어가 Open Targets 질환 색인에 없으면 `HPO_get_term_hierarchy`(`direction: "parents"`, HP 용어일 때)를 뿌리까지 되풀이해 받고, 둘 다 없으면 `ancestors: null`에 오류를 적습니다. 이 경우 L4도 `null`입니다.

조직 발현(L3)에는 PT가 어느 장기에서 생기는지가 필요합니다. 이 값은 모델이 판단하지 않고 온톨로지에서 가져옵니다.

- 용어의 상위 용어 가운데 HP 용어의 라벨과 동의어를 `HPO_get_term`으로 받습니다(상위 용어 조회는 ID만 주기 때문입니다). HPO는 `HP_0000118`(Phenotypic abnormality) 바로 아래가 장기 계통 가지입니다. 예를 들어 `HP_0001871`의 라벨은 "Abnormality of blood and blood-forming tissues"이고 동의어에 "Hematological abnormality"가 있습니다(2026-10-26 조회).
- `GTEx_get_tissue_sites`가 돌려준 30개 조직 그룹 이름(`tissueSite`: Blood, Liver, Brain 등)의 단어가 모두 상위 용어의 라벨이나 동의어에 대소문자 무시로 들어 있으면 그 그룹을 조직 후보로 둡니다. "blood" 하나로는 Blood만 잡히고 Blood Vessel은 잡히지 않습니다. 위 예에서는 "blood"가 겹쳐 Blood가 후보가 됩니다. 규칙은 단어 집합 교집합 하나이고 예외 표는 두지 않습니다.
- 겹치는 그룹이 없으면 `organs: null`이고 L3은 조직 후보 없이 54개 조직 가운데 TPM 상위 5개만 냅니다.
- 방법을 `hpo_ancestor_label`로 적고, 어느 상위 용어와 어느 단어가 겹쳤는지 함께 저장합니다. 빌드가 끝나면 조직 후보가 생긴 PT 비율을 README에 적습니다.

이 규칙은 거칠지만 모든 단계가 조회 결과에서 나오고 사람이 따라 확인할 수 있습니다. MedDRA SOC 계층이 들어오면 이 규칙을 SOC 표로 바꿉니다(7절).

## 4. 데이터 모양

산출물은 `api/_data/omics.json.gz` 한 파일입니다. 사실은 `drugs`, `targets`, `terms` 세 표에 한 번씩만 두고, `pairs` 표는 그 표를 가리키는 키와 쌍에서만 정해지는 값만 둡니다. 근거 항목은 `api/_fv/omics.py`의 순수 함수 `items(pair)`가 요청 때 표를 읽어 만듭니다. 그래서 같은 표적의 L1, L2, L3 문장이 쌍 80개마다 되풀이되지 않고, 파일 크기는 약과 표적과 용어 수에 비례합니다.

```json
{
  "asof": "2026-10-27",
  "versions": {"tooluniverse": "1.5.7", "opentargets": "<meta로 기록>", "gtex": "gtex_v10",
               "ols_efo": "<조회 시 기록>", "hpo": "<조회 시 기록>", "mondo": "<조회 시 기록>"},
  "drugs": {
    "NIRAPARIB": {"chembl_id": "CHEMBL1094636", "match": "name_exact",
                  "targets": ["ENSG00000143799", "ENSG00000129484"]}
  },
  "targets": {
    "ENSG00000143799": {
      "symbol": "PARP1",
      "moa": [{"drug": "NIRAPARIB", "action": "INHIBITOR",
               "mechanism": "Poly [ADP-ribose] polymerase-1 inhibitor", "dgidb": true}],
      "safety": null,
      "gtex": {"Whole_Blood": 0.0, "Liver": 0.0}
    }
  },
  "terms": {
    "thrombocytopenia": {"id": "HP_0001873", "label": "Thrombocytopenia", "match": "label", "source": "ols_efo",
                         "ancestors": ["HP_0011875", "HP_0001871", "HP_0000118", "EFO_0000651"],
                         "organs": {"sites": ["Blood"], "method": "hpo_ancestor_label",
                                    "evidence": [{"ancestor": "HP_0001871", "word": "blood"}]}}
  },
  "pairs": {
    "NIRAPARIB|thrombocytopenia": {
      "term": "thrombocytopenia",
      "safety_match": [],
      "assoc": {"score": 0.0125, "score_no_literature": 0.0, "row_found": true}
    }
  },
  "errors": []
}
```

티켓 01이 구현하며 정한 세부는 다음과 같습니다. 최상위에 `gtex_tissues` 표(`tissueSiteDetailId` → `tissueSite`)를 두어 조직 그룹을 세부 조직으로 풉니다. `safety_match` 항목은 `{"target": <ENSG>, "index", "relation"}`이며 표적이 여럿인 약에서 인덱스만으로는 모호하기 때문입니다. 안전성 책임 한 건은 `{"event", "event_id", "tissue_ids", "datasource", "pmid"}`이고 같은 `event_id`가 두 출처에서 오면 빌드가 한 건으로 합칩니다. `pair()`는 `{drug, pt, term, mapping, safety_match, assoc, safety_recorded}`를 돌려주고 `safety_recorded`는 표적 가운데 하나라도 `safety`가 `null`이 아닐 때 참입니다. L1의 `n`은 `{"liabilities": null | 개수}`, L2의 `n`은 `null`, L3의 `n`은 `{"median_tpm", "rank_of_54"}`(순위는 값이 있는 조직 가운데, 1이 최고), L4의 `n`은 `{"score", "score_no_literature"}`입니다. `row_found`가 거짓이면 L4 항목 하나가 "no association row ... nothing recorded, not a zero score"를 적고 점수는 `null`입니다. 이벤트 ID가 없는 책임은 사건명을 소문자 slug로 바꿔 ID에 씁니다. 직렬화는 `ensure_ascii=False`, 구분자 `(",", ":")`, gzip `mtime=0`에 빈 파일명이며 재생 시험이 바이트 단위로 같아지도록 빌드도 같은 설정을 씁니다.

위 예시에서 실제 조회값은 CHEMBL ID, Ensembl ID, 기전 문장, 상위 용어 목록, 연관 점수 0.0125(파일럿)입니다. `gtex` 값 0.0과 `organs`는 자리 표시입니다. `safety: null`은 필드 없음, `[]`는 필드는 있으나 비어 있음입니다.

규칙은 아래와 같습니다.

- 쌍 키는 `<DRUG>|<pt 소문자>`이고 DRUG는 `signals.json.gz`의 키 그대로입니다(`drug.upper()`, 복합제의 `\` 유지). `evidence.id_drug`의 `+` 치환은 근거 ID 안에서만 씁니다. `omics.pair(drug, pt)`는 입력을 `upper()`와 `lower()`로만 정규화합니다.
- `pairs[].safety_match`는 표적의 안전성 책임 항목의 인덱스 목록으로, `eventId`가 용어 ID와 같거나(`term`) 용어의 상위 용어 가운데 하나인(`ancestor`) 항목만 담습니다. 이는 PT 매핑을 올려 잡는 것이 아니라 이미 매핑된 용어와 이벤트 ID의 관계를 적는 것입니다. 조직 ID끼리의 계층 비교는 v1에서 하지 않습니다.
- `items(pair)`가 만드는 근거 항목은 `{"id", "layer", "what", "n"}`입니다. L1은 표적마다 하나, L2는 표적의 안전성 책임마다 하나(`match` 필드에 `term`, `ancestor`, `none`), L3은 조직 후보에 속한 세부 조직마다 하나(후보가 없으면 TPM 상위 5개), L4는 하나입니다. L3의 `n`은 중앙값 TPM과 54개 조직 가운데 순위입니다. 문턱값은 측정 없이 정할 수 없으므로 "발현됨" 같은 판정은 넣지 않습니다.
- L4는 파일럿과 같은 두 점수를 냅니다. `score > 0`이고 `score_no_literature == 0`일 때만 `what`에 "literature co-mention only"를 적습니다.
- 매핑이 `none`이면 `safety_match`와 `assoc`는 `null`입니다. `items`는 L1 전부, L2 전부(`match: none`), L3 상위 5개를 내고 L4는 내지 않습니다.
- 메트포르민처럼 표적이 51개인 약이 Nemotron 프롬프트를 넘치게 하지 않도록 숙고 메모에 들어가는 묶음은 `items_for_memo(pair)`가 따로 자릅니다. L1 최대 5개, L2는 `match`가 `term` 또는 `ancestor`인 것만, L3은 조직 후보 안의 세부 조직 최대 5개, L4 하나입니다. 대시보드와 CLI는 `items` 전부를 보여 줍니다.
- 쌍 수준 판정(지지, 부분, 없음) 없이 층별 개수만 둡니다. 판정 규칙은 역할 B의 측정 뒤에 정합니다.
- 조회에 실패한 값은 0으로 채우지 않고 `null`로 두며 오류를 `errors[]`에 남깁니다.

`what` 문장은 영어로 쓰고 쌍과 무관하게 사실만 적습니다. 그래서 같은 ID의 `what`은 어느 묶음에서나 같고, `evidence.bundle`의 `ids` 집합에서 중복이 안전하게 합쳐집니다. 모든 `what` 끝에 "Population-level mechanistic context; not evidence that the drug caused this reaction in this case."를 붙입니다.

크리틱 2단의 숫자 허용 오차는 `max(0.011, |y| * 0.011)`입니다(`api/_fv/assess.py:92`). L4 점수 0.0125와 0.0은 이 오차 안에 있어 2단이 가르지 못합니다. v1은 이 한계를 적어 두고 그대로 둡니다. 메모가 L4 숫자를 인용하는 일이 드물고, 오차 규칙을 바꾸면 기존 측정(`docs/EVALUATION.md`의 크리틱 31/31)을 다시 해야 하기 때문입니다.

## 5. 어디에 붙는가

| 자리 | 바뀌는 것 | 파일 |
|---|---|---|
| 적재 | `_omics()` 캐시 로더, `pair(drug, pt)`, `drug_pairs(drug)`, `drugs()`, `items(pair)`, `items_for_memo(pair)`. 파일이 없으면 빈 구조 | 새 `api/_fv/omics.py` |
| 근거 묶음 | `bundle()`이 이미 고른 반응 목록 `pts`(`evidence.py:246`)마다 `items_for_memo`를 `catalog`에 덧붙이고 `ids`에 포함. 모듈 docstring에 `omics:` 접두사 4종 설명 추가 | `api/_fv/evidence.py:242-296` |
| 숙고 메모 | `OVERCLAIM_RULES`에 R14 추가 | `api/_fv/assess.py:17-31` |
| R14를 적은 다른 곳 | 규칙 목록, "13 rules" 문구, 크리틱 스킬 문서 | `web/src/pages/Skills.tsx:13-22`, `web/src/lib/glossary.ts:377,814`, `skills/pv-critic/SKILL.md:45,48` |
| 등급 | `grade.py`는 바꾸지 않음. `/api/grade` 응답에 `omics: {"count": n, "mapping": ...}`를 더함. `gaps`에 한국어 한 줄 "오믹스 근거는 등급에 반영하지 않음"을 넣고 `GAP_EN`에 영어 짝을 추가 | `api/index.py:145-161`, `web/src/components/GradeCard.tsx:43-57` |
| API | `GET /api/omics?drug=&pt=`(쌍 하나), `GET /api/omics?drug=`(약의 쌍 목록), `GET /api/omics/drugs`(약 목록). 경로 변수를 쓰지 않는 이유는 PT 13개가 `/`를 품기 때문. 없으면 404. `LIMIT`에 `omics` 키 추가. docstring의 엔드포인트 목록 갱신 | `api/index.py:39-45`, `index.py:1-14` |
| CLI | `flygate omics <DRUG> "<PT>"`. 출력은 `items` 전부와 `evidence_ids`. 추출에 없는 약이나 쌍이면 `{"found": false, "evidence_ids": []}`와 사유를 내고 종료 코드 0. `ALLOWED`, `HELP`, `SYSTEM` 명령 목록, 배너의 도구 수(`'7 tools'` → `'8 tools'`), `TOOLS.md` 갱신 | `agent/flygate.py`, `agent/chat.py:18-56`, `agent/banner.py:82`, `agent/workspace/TOOLS.md` |
| 대시보드 | `/#/omics` 페이지. `/api/omics/drugs`로 약 선택 → 쌍 목록 → 층별 표. `GradeCard`는 `/api/grade` 응답의 `omics.count`로 "오믹스 근거 n건" 링크 표시 | `web/src/pages/Omics.tsx`, `web/src/App.tsx:49-58`, `web/src/components/GradeCard.tsx` |
| 정책 | 바꾸지 않음. 조회는 빌드 시점에만 하고 런타임은 추출 파일만 읽음 | `agent/policy/flygate.yaml` |
| 스킬 | `skills/pv-omics-evidence/SKILL.md`. 프런트매터는 `skills/README.md:26`의 필수 필드(`name`, `title`, `version`, `description`, `license`, `compatibility`, `metadata.author/domain/tags/layer/model`)를 모두 채움. skill-card는 NVIDIA `skill-card-generator` 스크립트가 있을 때 만들고, 없으면 PR에 미완으로 적음. README의 스킬 수(11 → 12)와 `pipeline/build_skills.py` 재실행 | `skills/`, `skills/README.md:3-4,10` |

R14 문안입니다.

> R14: Mechanistic evidence (target safety liabilities, tissue expression, target-disease association) shows biological plausibility at the population level. It never establishes that the drug caused the reaction in this case, and absence of mechanistic evidence is not evidence against the association.

크리틱 1단(근거 ID 존재)과 2단(숫자 오차)은 그대로 `omics:` 항목에 적용됩니다. 3단은 R14를 규칙 목록에서 읽습니다.

## 6. 빌드

코드는 `pipeline/omics/`에 둡니다. 파일럿 `scripts/omics_plausibility.py`(구 저장소 `korea-agentic-hackathon-2026`, 브랜치 `omics-plausibility`)의 `Fetcher`(sha1 캐시, 재시도, dry-run)와 참조 세트 묶음 조회를 이식합니다. 호스트마다 `evidence._Spacer`와 같은 0.2초 간격을 둡니다.

| 파일 | 하는 일 |
|---|---|
| `fetch.py` | ToolUniverse SDK(`ToolUniverse().run_one_function`)와 Open Targets GraphQL을 같은 캐시 규칙으로 감쌈. 캐시는 `$OMICS_DIR/<source>/<sha1>.json` |
| `terms.py` | 3절의 PT 매핑과 조직 후보 |
| `layers.py` | L1부터 L4까지 조회 |
| `build.py` | `--drugs <파일>`, `--pairs <파일>`, `--pts-per-drug 80`, `--out api/_data/omics.json.gz`, `--dry-run`, `--limit N`. 끝에 적용 범위 표를 출력 |
| `README.md` | 실행법과 버전 기록 |

실행은 컴퓨트 노드에서 저장소 루트를 기준으로 합니다. ToolUniverse는 빌드 의존성이고 `requirements.txt`와 `api/`에는 들어가지 않습니다. `build.py`는 `agent/flygate.py`처럼 `api/`를 `sys.path`에 넣어 `labeltext`를 씁니다.

```bash
export OMICS_DIR=/data/hps/assoc/private/rsc/user/ybae/tmp/omics-cache
export UV_CACHE_DIR=/data/hps/assoc/private/rsc/user/ybae/.cache/uv
cd /data/hps/assoc/private/rsc/user/ybae/RSC/Project-FlyGate
srun -A rsc -p cpu-core -c 2 --mem=15000M -t 06:00:00 \
  uv run --no-project --with tooluniverse==1.5.7 python -m pipeline.omics.build \
    --drugs pipeline/omics/drugs_v1.txt --pairs pipeline/omics/pairs_v1.txt \
    --out api/_data/omics.json.gz
```

약 집합 `drugs_v1.txt`는 SIDER 파일럿 31종, SignalLab 프리셋 11종, CLI 감시 목록 3종, Time Machine 9종, 시연 사례 440건의 주 의심약 224종의 합집합입니다. 쌍은 세 곳의 합집합입니다. 약마다 `signals.json.gz` 상위 80개 PT, 시연 사례의 주 의심약과 반응 상위 3개, 그리고 `pairs_v1.txt`에 적은 감시 목록과 Time Machine 쌍입니다. 마지막 둘이 필요한 이유는 감시 목록 10쌍 가운데 3쌍과 Time Machine 9쌍 가운데 5쌍이 상위 80개 밖에 있기 때문입니다. 그 밖의 약이나 쌍은 API가 404를 내고 화면은 "추출에 없음"을 보입니다.

호출 수는 빌드 전에 `--dry-run`으로 셉니다. 대략 PT마다 온톨로지 검색 3회와 상위 용어 1회, 표적마다 안전성 1회와 GTEx 1회와 연관 목록 1회, 약마다 ID 1회와 기전 1회와 DGIdb 1회입니다. 간격 0.2초에 PT 5,000개면 검색만 약 50분입니다. 빌드가 끝나면 약 수, 표적 수, PT 수, 매핑 비율, 조직 후보 비율, 호출 수, 실패 수를 README에 적습니다.

## 7. v1에서 빼는 것과 다음 단계

| 항목 | 상태 | 조건 |
|---|---|---|
| 역할 B: 오믹스 점수를 등급에 반영 | 미룸 | `pilot_sider_2026-09-28.json.gz` 64,796쌍에서 층별 AUC와 귀무를 재고 불균형 지표를 넘는 층만 넣음. 그 뒤 OMOP, EU-ADR로 재확인 |
| MedDRA SOC 계층 | 미룸 | 팀에 MSSO 구독이 있으면 PT → SOC 표로 3절의 조직 후보 규칙을 대체. 원본 파일은 저장소에 넣지 않음 |
| UMLS 교차참조 | 미룸 | UTS API 키 확보 뒤 MedDRA 어휘 사용 제한 확인. `umls_search_concepts`는 `UMLS_API_KEY`가 있어야 열림 |
| Mondo의 MedDRA 교차참조 | 측정 필요 | 파일럿은 Open Targets의 EFO·MONDO·HP 응답에서 MedDRA 교차참조를 찾지 못했습니다(EVALUATION 7절). Mondo 자체 API(`Mondo_search_disease`)의 `xref`에는 `MedDRA:10053176`(cyclic neutropenia) 같은 코드가 있었습니다. 전체 PT에서 얼마나 나오는지 세어 볼 것 |
| 상위 용어 올림 | 미룸 | 질환 용어와 표현형 용어의 점수 척도 차이를 먼저 잴 것 |
| L5 표현형-유전자(HPO) | 미룸 | `HPO_get_genes_by_phenotype`로 용어의 유전자 집합과 표적 교집합 |
| L6 단백체(HPA) | 미룸 | `HPA_get_gene_tsv_data_by_ensembl_id`가 조직 nTPM을 주는지 확인 |
| 크리틱 2단 오차 바닥 0.011 | 미룸 | 작은 L4 점수를 가르려면 오차 규칙을 바꾸고 크리틱 측정을 다시 해야 함 |
| 초파리 상동 유전자 | 넣지 않음 | 연결체 화면은 은유이고 임상 근거가 아님 |
| 개별 사례 인과 | 넣지 않음 | R14 |

## 8. 검증

- `tests/test_omics.py`: 파일이 없을 때 로더가 빈 구조를 돌려주는지, `pair` 조회와 404, 근거 ID 형식(접두사 4종), `items`와 `items_for_memo`의 자르기 규칙, `bundle`의 catalog 병합(네트워크 함수는 `test_label_facts.py` 방식으로 패치), R14가 `OVERCLAIM_RULES`에 있음, `flygate omics`가 없는 약에 `found: false`를 내는지.
- `tests/test_agent.py:130-133`의 서브커맨드 집합에 `omics` 추가.
- `tests/test_chat.py:74`의 `'7 tools'`를 `'8 tools'`로. `test_direct_slash_tools`는 스텁 러너라 새 명령을 실행하지 않으므로 `test_omics.py`가 CLI를 직접 부릅니다.
- `pipeline/omics/tests/`: 캐시 재생으로 네트워크 없이 매핑 규칙, 조직 후보 규칙, 항목 생성을 시험(파일럿 `tests/test_omics_plausibility.py` 방식).
- 빌드 뒤 실제 산출물로 확인: 니라파립-혈소판감소증 쌍이 PARP1과 PARP2 모두 `safety: null`, L4 문헌 제외 0으로 나오는지(정직한 음성). 두 번째 시연 쌍은 데이터에서 고릅니다.
- 작업 단위마다 `.venv/bin/python -m pytest -q tests`를 통과시킵니다.

## 9. 출처

- ToolUniverse 1.5.7, 도구 이름과 매개변수는 2026-10-26에 `tu info`로 확인. 등록된 도구 646개(키 없이), SDK 적재 2,719개.
- Open Targets Platform: `OpenTargets_*` 도구 응답. 데이터 버전은 빌드마다 `meta`로 기록.
- GTEx v10: `GTEx_get_tissue_sites`(54 세부 조직, 30 그룹, UBERON ID), `GTEx_get_median_gene_expression`.
- OLS v4(EFO), HPO(JAX), Mondo: 용어 검색 도구 응답.
- 파일럿: 구 저장소 `docs/notes/omics-plausibility-2026-09-28.md`, 결과 `eval/results/omics_plausibility_refset_2026-09-28.json.gz`, 참조 세트 `eval/refsets/pilot_sider_2026-09-28.json.gz`(SIDER 4.1, MedDRA 16.1 PT 이름, 약 31종, 쌍 64,796).
- 이 저장소: `api/_fv/evidence.py`, `assess.py`, `grade.py`, `labeltext.py`, `api/index.py`, `agent/flygate.py`, `agent/chat.py`, `agent/banner.py`, `web/src/pages/SignalLab.tsx`, `web/src/components/GradeCard.tsx`, `tests/test_agent.py`, `tests/test_chat.py`.
