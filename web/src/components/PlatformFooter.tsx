import { t, useLang } from '../lib/i18n'
import './PlatformFooter.css'

export default function PlatformFooter({ compact }: { compact?: boolean }) {
  useLang()
  const notice = t('FlyGate는 연구와 판단을 돕는 도구이며 임상 진단이나 규제기관의 판정을 대신하지 않습니다.', 'FlyGate supports research and judgment. It does not replace clinical diagnosis or regulatory decisions.')
  if (compact) return <footer className="pf-footer pf-compact"><span>© {t('Team FlyGate', 'Team FlyGate')}</span><p>{notice}</p><a href="https://github.com/Team-FlyGate/Project-FlyGate" target="_blank" rel="noopener noreferrer">{t('GitHub ↗', 'GitHub ↗')}</a></footer>
  return <footer className="pf-footer">
    <div className="pf-grid">
      <div className="pf-brand"><strong>{t('Project FlyGate', 'Project FlyGate')}</strong><p>{t('분자에서 환자까지, 추론보다 근거가 먼저.', 'From molecules to patients, evidence before inference.')}</p></div>
      <nav aria-label={t('제품 링크', 'Product links')}><h2>{t('제품', 'Products')}</h2><a href="#/discovery">{t('FlyDiscovery', 'FlyDiscovery')}</a><a href="#/mission">{t('FlyVigilance', 'FlyVigilance')}</a><a href="#/cli">{t('Agent CLI', 'Agent CLI')}</a><a href="#/glossary">{t('용어 풀이', 'Glossary')}</a></nav>
      <nav aria-label={t('자료 링크', 'Resources')}><h2>{t('자료', 'Resources')}</h2><a href="https://github.com/Team-FlyGate/Project-FlyGate" target="_blank" rel="noopener noreferrer">{t('GitHub 저장소 ↗', 'GitHub repository ↗')}</a><a href="https://github.com/Team-FlyGate/Project-FlyGate/tree/main/docs" target="_blank" rel="noopener noreferrer">{t('문서 ↗', 'Documentation ↗')}</a><a href="https://github.com/Team-FlyGate/Project-FlyGate/issues" target="_blank" rel="noopener noreferrer">{t('이슈 · 제안 ↗', 'Issues & ideas ↗')}</a><a href="https://github.com/Team-FlyGate/Project-FlyGate/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">{t('Apache-2.0 라이선스 ↗', 'Apache-2.0 license ↗')}</a><a href="#/validation">{t('검증과 한계', 'Validation and limitations')}</a></nav>
      <div className="pf-sources"><h2>{t('데이터 출처', 'Data sources')}</h2><p>{t('FDA FAERS · 2012Q4–2026Q2', 'FDA FAERS · 2012Q4–2026Q2')}</p><p>{t('MaleCNS v1.0 · Janelia FlyEM · CC-BY 4.0', 'MaleCNS v1.0 · Janelia FlyEM · CC-BY 4.0')}</p><p>{t('RCSB PDB 4R6E · ChEMBL', 'RCSB PDB 4R6E · ChEMBL')}</p><p>{t('커넥텀은 에이전트 라우팅 위상의 시각화에 사용합니다.', 'The connectome visualizes agent routing topology.')}</p></div>
    </div>
    <div className="pf-legal"><p>{notice}</p><p>{t('NVIDIA Korea Agentic AI Hackathon 2026 우승작', 'NVIDIA Korea Agentic AI Hackathon 2026 Winner')}</p><span>© Team FlyGate · {t('Apache-2.0 라이선스로 공개한 오픈소스', 'Open source under the Apache-2.0 license')}</span></div>
  </footer>
}
