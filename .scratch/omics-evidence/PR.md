# PR: FlyVigilance 오믹스 근거 층 v1 (feat/omics-evidence → main)

## Summary

```
drug ──(FAERS PT)──► 용어 매핑 OLS/HPO/Mondo ──► 상위 용어(HP) ──► 장기 후보(GTEx 그룹 이름 단어 일치)
  │                                                                    │
  └──(Open Targets MoA)──► 표적 ──► L2 안전성 책임 ─┬─► api/_data/omics.json.gz ──► omics.py items / items_for_memo
                                  ├─► L3 GTEx v10 TPM ┘        │
                                  └─► L4 표적-질환 연관         ├─► /api/omics, /api/omics/drugs, /api/grade.omics
                                                                 ├─► flygate omics, chat /omics
                                                                 ├─► evidence.bundle catalog (omics: ID) ──► 메모 ──► 크리틱 R14
                                                                 └─► /#/omics 페이지, GradeCard 건수
```

설계: `docs/OMICS_DESIGN_v1.0.0.md` (+ `-en`). 스펙과 티켓 7개: `.scratch/omics-evidence/`. 역할 A만 들어갑니다(설명용 근거). 등급과 PV 분류는 바뀌지 않습니다.

## Evidence

- Before: 약물-반응 쌍에 기전 근거가 없고, 메모가 인용할 `omics:` ID 가 없음. 파일럿 PT 매핑 24.5%.
- After: `flygate omics NIRAPARIB "Thrombocytopenia" --memo` → L1 PARP1·PARP2(`safety: null`, 기록 없음), L3 Whole_Blood, L4 0.0125(문헌 제외 0.0, "literature co-mention only"). 매핑 45.4%(788/1,737). 추출 389,610바이트, 약 245종, 쌍 16,248개.
- 시연 쌍: 정직한 음성 NIRAPARIB|thrombocytopenia, 양성 PIMAVANSERIN|hallucination(HTR2A "hallucinations" HP_0000738, PMID 23197038, 28216264, 연관 0.486, 문헌 제외 0.484). 선택 스크립트 `pipeline/omics/pick_demo_pairs.py`.
- 테스트: `pytest -q pipeline/omics/tests tests` → 269 passed, 2 skipped (Python 3.10 venv, cpu-core). 웹: `tsc -b && vite build` 통과.
- 빌드 재현: `pipeline/omics/README.md` 의 명령. 캐시 재생 시험이 픽스처를 바이트 단위로 재현.

## Merge Danger

Door: two-way. 추출 파일과 코드 추가가 대부분이고 기존 동작 변경은 세 곳뿐입니다. `grade_pair` 의 `gaps` 에 한 줄 추가, `/api/grade` 응답에 `omics` 블록 추가, `OVERCLAIM_RULES` 에 R14 추가(크리틱 3단 프롬프트가 한 줄 길어짐).

Blast Radius: small.

- Vercel 번들에 390 KB 가 더해집니다(`includeFiles` 가 이미 `api/_data/**` 를 포함).
- 배너 "8 tools", 규칙 수 "14" 로 바뀐 문자열이 화면·README·스킬 문서에 걸쳐 있습니다. `tests/test_omics_bundle.py` 가 세 곳을 `OVERCLAIM_RULES` 길이와 대조합니다.
- `skills/pv-omics-evidence/skill-card.md` 는 손으로 썼고 NVIDIA 생성기 실행이 남아 있습니다.
- 브라우저에서 `/#/omics` 두 시연 쌍 확인은 배포 뒤 flygate.kr 에서 합니다.

## 남은 일 (v1 이후)

- 역할 B(점수 축)는 SIDER 파일럿 세트에서 귀무를 이긴 뒤에만. MedDRA SOC, UMLS, L5, L6 은 설계 문서 7절.
- 매핑 개선 후보: OLS·Mondo 응답에 동의어가 없음(동의어 일치는 모두 HPO), `rows: 5` 가 일부 정확 용어를 놓침(예: eosinophilia).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
