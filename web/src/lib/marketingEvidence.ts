import { t } from './i18n'

export interface Evidence {
  id: string
  product: 'discovery' | 'vigilance' | 'platform'
  value: string
  label(): string
  condition(): string
  href: string
  source: string
}

export const evidence = (): Evidence[] => [
  { id: 'structure', product: 'discovery', value: '1.0 Å', label: () => t('OpenFold3 구조 예측 CA RMSD', 'OpenFold3 structure CA RMSD'), condition: () => t('PARP1 4R6E chain A + 니라파립 · CA 350개를 결정 구조와 비교', 'PARP1 4R6E chain A + niraparib · 350 CA atoms compared with the crystal structure'), href: '#/discovery', source: 'fly_discovery/measurements/measurements.json → openfold3_msa.ca_rmsd_vs_4R6E, n_ca' },
  { id: 'affinity', product: 'discovery', value: '0.767', label: () => t('Boltz-2 · ChEMBL 순위 상관', 'Boltz-2 · ChEMBL rank correlation'), condition: () => t('PARP1 화합물 39종 · 예측과 실측의 Spearman 상관', '39 PARP1 compounds · Spearman correlation of predictions and measurements'), href: '#/discovery', source: 'fly_discovery/measurements/measurements.json → parp1_affinity_benchmark.spearman, n' },
  { id: 'critic', product: 'platform', value: '31/31 · 6/6', label: () => t('크리틱 주입 시험', 'Critic injection test'), condition: () => t('틀린 주장 31/31 반려 · 정상 대조 6/6 통과 · 저장된 시험', '31/31 incorrect claims rejected · 6/6 controls passed · saved test'), href: '#/overview', source: 'web/public/data/critic_probe.json → summary.p1–p4.correct/n, summary.ctrl.correct/n' },
  { id: 'faers', product: 'vigilance', value: '55', label: () => t('FAERS 데이터 분기', 'FAERS data quarters'), condition: () => t('2012Q4–2026Q2 · 저장소에 수록된 데이터 범위', '2012Q4–2026Q2 · data coverage stored in the repository'), href: '#/signals', source: 'web/public/data/faers/overview.json → quarters, first, asof' },
  { id: 'review', product: 'vigilance', value: '247/250', label: () => t('검토에 도달한 중대 사례', 'Serious cases reaching review'), condition: () => t('실제 FAERS 440건 · 결과 코드를 가린 트리아지 · 중대 사례 250건', '440 real FAERS cases · outcome codes hidden during triage · 250 serious cases'), href: '#/bench', source: 'web/public/data/bench.json → ablation_blind.serious − flyvigilance.routes_serious.close − monitor' },
  { id: 'latency', product: 'vigilance', value: '295.7 ms', label: () => t('반사 트리아지 지연 p50', 'Reflex triage latency p50'), condition: () => t('n=440 · 호출당 7문항 · 저장된 평가 실행', 'n=440 · 7 questions per call · saved evaluation run'), href: '#/bench', source: 'web/public/data/bench.json → jev_triage.latency_ms.p50, n; questions_per_call' },
  { id: 'auc', product: 'vigilance', value: '0.960 / 0.983', label: () => t('OMOP / EU-ADR 참조 세트 AUC', 'OMOP / EU-ADR reference-set AUC'), condition: () => t('n=387 / 93 · 약·반응 이름을 쓰는 지식 기반 판별 · 반올림', 'n=387 / 93 · knowledge-based discrimination using drug and event names · rounded'), href: '#/validation', source: 'web/public/data/validation.json → refsets.OMOP/EU-ADR.methods[key=raw_named].auc, n' },
  { id: 'sandbox', product: 'platform', value: '20/20', label: () => t('OpenShell 샌드박스 스모크', 'OpenShell sandbox smoke test'), condition: () => t('저장된 단일 실행 · 권한·네트워크 정책 등 20개 검사', 'One saved run · 20 checks including privileges and network policy'), href: '#/agent', source: 'web/public/data/agent.json → smoke.results[].pass' },
]
