import { useEffect, useRef, useState, type ReactNode } from 'react'
import { BrainProvider } from './lib/brain'
import { api, type Health } from './lib/data'
import Landing from './pages/Landing'
import Overview from './pages/Overview'
import Discovery from './pages/Discovery'
import DiscoveryStep from './pages/DiscoveryStep'
import DiscoveryEvidence from './pages/DiscoveryEvidence'
import Agent from './pages/Agent'
import CliTutorial from './pages/CliTutorial'
import MissionControl from './pages/MissionControl'
import Architecture from './pages/Architecture'
import LiveTriage from './pages/LiveTriage'
import SignalLab from './pages/SignalLab'
import TimeMachine from './pages/TimeMachine'
import Warehouse from './pages/Warehouse'
import Benchmarks from './pages/Benchmarks'
import Problem from './pages/Problem'
import Skills from './pages/Skills'
import CallLog from './pages/CallLog'
import KoreanPV from './pages/KoreanPV'
import Validation from './pages/Validation'
import Glossary from './pages/Glossary'
import Term from './components/Term'
import ShowreelModal from './components/ShowreelModal'
import PlatformFooter from './components/PlatformFooter'
import { t, useLang } from './lib/i18n'

const I = (d: string) => (
  <svg className="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
)

interface Page { id: string; label: string; en: string; icon: ReactNode; el: () => ReactNode }
interface Section { title?: string; pages: Page[] }
type AreaId = 'discovery' | 'vigilance' | 'platform'
interface Area { id: AreaId; name: string; step: string; tagline: string; color: string; home: string; sections: Section[] }

// 제품 영역은 셋입니다: FlyDiscovery(시판 전) · FlyVigilance(시판 후) · 플랫폼(에이전트 · 거버넌스 · 문서).
// 사이드바에는 지금 들어와 있는 영역의 메뉴만 보입니다. 페이지 id(해시 주소)는 예전 그대로입니다.
// 언어에 따라 문구가 바뀌므로 렌더할 때마다 만듭니다.
const areas = (): Area[] => [
  { id: 'discovery', name: 'FlyDiscovery', step: t('STEP 1 · 시판 전', 'STEP 1 · Pre-market'), tagline: t('후보 물질의 표적 결합 근거', 'Target-binding evidence for candidates'), color: 'var(--c-sense)', home: 'discovery', sections: [
    { pages: [
      { id: 'discovery', label: t('전체 프로세스', 'Full pipeline'), en: t('Discovery · 약물 패널', 'Discovery · drug panel'), icon: I('M12 3l7.8 4.5v9L12 21l-7.8-4.5v-9ZM12 8.5l3 1.75v3.5L12 15.5l-3-1.75v-3.5Z'), el: () => <Discovery /> },
    ] },
    { title: t('파이프라인 단계', 'Pipeline stages'), pages: [
      { id: 'd-msa', label: '1. MSA-Search', en: t('닮은 단백질 서열 찾기', 'Find similar protein sequences'), icon: I('M4 6h16M4 10h10M4 14h16M4 18h7'), el: () => <DiscoveryStep key="msa" step="msa" /> },
      { id: 'd-of3', label: '2. OpenFold3', en: t('3차원 구조 예측', '3D structure prediction'), icon: I('M6 4c6 0 6 4 12 4M6 10c6 0 6 4 12 4M6 16c6 0 6 4 12 4'), el: () => <DiscoveryStep key="of3" step="of3" /> },
      { id: 'd-diffdock', label: '3. DiffDock', en: t('붙는 자리와 자세 찾기', 'Find the binding site and pose'), icon: I('M12 3a9 9 0 1 0 9 9M12 8a4 4 0 1 0 4 4M3 3l6 6'), el: () => <DiscoveryStep key="dd" step="dd" /> },
      { id: 'd-boltz', label: '4. Boltz-2', en: t('붙는 세기 예측 · 실측 대조', 'Binding strength vs. measured'), icon: I('M4 20 20 4M6 14l2 2M10 10l2 2M14 6l2 2'), el: () => <DiscoveryStep key="bz" step="bz" /> },
      { id: 'd-critic', label: t('5. 크리틱', '5. Critic'), en: t('근거를 넘는 결론 반려', 'Rejects conclusions beyond the evidence'), icon: I('M9 12l2 2 4-4M12 3 4 7v6c0 4 3.5 7 8 8 4.5-1 8-4 8-8V7l-8-4Z'), el: () => <DiscoveryStep key="critic" step="critic" /> },
      { id: 'd-evidence', label: t('6. 근거 검증', '6. Evidence check'), en: t('검증 → 선택성 → 후보 카드', 'Validation → selectivity → candidate card'), icon: I('M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14ZM21 21l-5-5M8 11l2 2 4-4'), el: () => <DiscoveryEvidence /> },
    ] },
  ] },
  { id: 'vigilance', name: 'FlyVigilance', step: t('STEP 2 · 시판 후', 'STEP 2 · Post-market'), tagline: t('허가 약물의 이상사례 감시', 'Adverse-event monitoring for marketed drugs'), color: 'var(--nvidia)', home: 'mission', sections: [
    { title: t('관제 · 사례', 'Operations · cases'), pages: [
      { id: 'mission', label: t('관제 센터', 'Mission Control'), en: t('Mission Control', 'Live overview'), icon: I('M12 3a9 9 0 1 0 9 9M12 7a5 5 0 1 0 5 5M12 11a1 1 0 1 0 1 1M21 3l-7.5 7.5'), el: () => <MissionControl /> },
      { id: 'triage', label: t('사례 분류 (트리아지)', 'Case Triage'), en: t('Live Triage · 보고 한 건', 'Live triage · one report'), icon: I('M3 12h4l3-8 4 16 3-8h4'), el: () => <LiveTriage /> },
      { id: 'korea', label: t('국내 보고 · 인과성', 'Korean Reports · Causality'), en: 'Korean PV Intake', icon: I('M4 4h16v16H4zM8 9h8M8 13h8M8 17h5'), el: () => <KoreanPV /> },
    ] },
    { title: t('신호 분석', 'Signal analysis'), pages: [
      { id: 'signals', label: t('부작용 신호 연구실', 'Signal Lab'), en: t('Signal Lab', 'Adverse-event signal statistics'), icon: I('M4 20V10M10 20V4M16 20v-7M22 20H2'), el: () => <SignalLab /> },
      { id: 'timemachine', label: t('부작용 신호 타임머신', 'Signal Time Machine'), en: t('Signal Time Machine', 'Signals before the label'), icon: I('M12 7v5l3 2M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5'), el: () => <TimeMachine /> },
    ] },
    { title: t('검증 · 데이터', 'Validation · data'), pages: [
      { id: 'validation', label: t('유의성 검증', 'Signal Validation'), en: 'Reference Validation', icon: I('M9 12l2 2 4-4M4 4h16v16H4z'), el: () => <Validation /> },
      { id: 'bench', label: t('유의성 벤치마크', 'Benchmarks'), en: 'Measured Performance', icon: I('M3 3v18h18M7 15l4-4 3 3 6-7'), el: () => <Benchmarks /> },
      { id: 'warehouse', label: t('데이터 웨어하우스', 'Data Warehouse'), en: 'PV Warehouse', icon: I('M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3ZM4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6'), el: () => <Warehouse /> },
    ] },
  ] },
  { id: 'platform', name: t('플랫폼', 'Platform'), step: t('에이전트 · 거버넌스', 'Agent · governance'), tagline: t('두 제품이 함께 쓰는 기반', 'The foundation both products share'), color: '#e2a74e', home: 'overview', sections: [
    { title: t('플랫폼', 'Platform'), pages: [
      { id: 'overview', label: t('플랫폼 개요', 'Platform overview'), en: 'Discovery → Vigilance', icon: I('M3 11 12 4l9 7M5 10v10h5v-6h4v6h5V10'), el: () => <Overview /> },
      { id: 'architecture', label: t('아키텍처 · 층 구성', 'Architecture · Layers'), en: 'Connectome-routed Architecture', icon: I('M4 6h6v6H4zM14 12h6v6h-6zM10 9h2a2 2 0 0 1 2 2v4M17 12V6h-3'), el: () => <Architecture /> },
    ] },
    { title: t('에이전트 · NVIDIA', 'Agent · NVIDIA'), pages: [
      { id: 'cli', label: 'FlyGate Agent CLI', en: t('한 줄 설치 · 실제 터미널 · 튜토리얼', 'One-line install · real terminal · tutorial'), icon: <span className="mono" aria-hidden="true">›_</span>, el: () => <CliTutorial /> },
      { id: 'agent', label: t('에이전트 구성', 'Agent Setup'), en: 'NemoClaw · OpenShell', icon: I('M12 3 4 7v10l8 4 8-4V7l-8-4ZM4 7l8 4 8-4M12 11v10'), el: () => <Agent /> },
      { id: 'skills', label: t('NVIDIA 스킬 · 거버넌스', 'NVIDIA Skills · Governance'), en: 'Skills & Guardrails', icon: I('M12 2 3 7v6c0 5 4 8 9 9 5-1 9-4 9-9V7l-9-5ZM9 12l2 2 4-4'), el: () => <Skills /> },
      { id: 'calls', label: t('NVIDIA 호출 로그', 'NVIDIA Call Log'), en: t('API call log · 요청 ID · 증거 대응표', 'API call log · request IDs · evidence map'), icon: I('M4 5h16M4 10h16M4 15h10M4 20h7M17 15l2 2 3-4'), el: () => <CallLog /> },
    ] },
    { title: t('문서', 'Documentation'), pages: [
      { id: 'problem', label: t('문제 정의', 'Problem'), en: 'Why it matters', icon: I('M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z'), el: () => <Problem /> },
      { id: 'glossary', label: t('용어 풀이', 'Glossary'), en: t('Glossary · 약어와 전문 용어', 'Acronyms & technical terms'), icon: I('M4 19.5V5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2Zm0 0a2 2 0 0 0 2 2h13M9 8h6M9 12h4'), el: () => <Glossary /> },
    ] },
  ] },
]

// 빈 해시 · '#/' · '#/home' 은 대문입니다. 그 밖의 주소는 페이지 id 로 읽고, '?' 뒤는 각 페이지가 직접 읽습니다.
function useHashPage() {
  const get = () => (location.hash.replace(/^#\/?/, '').split('?')[0] || 'home')
  const [page, setPage] = useState(get)
  useEffect(() => {
    const on = () => setPage(get())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return page
}

function NotFound({ page }: { page: string }) {
  return (
    <div className="notfound">
      <div className="eyebrow">404</div>
      <h1 className="title">{t('찾는 화면이 없습니다', 'This page does not exist')}</h1>
      <p className="lede">{t(<>주소 <span className="mono">#/{page}</span> 에 해당하는 화면이 없습니다. 주소를 다시 확인하거나 아래에서 이동하세요.</>,
        <>There is no screen at <span className="mono">#/{page}</span>. Check the address, or continue from one of the links below.</>)}</p>
      <div className="row wrap" style={{ gap: 10, justifyContent: 'center' }}>
        <a className="btn primary" href="#/">{t('대문으로', 'Home')}</a>
        <a className="btn ghost" href="#/discovery">FlyDiscovery</a>
        <a className="btn ghost" href="#/mission">FlyVigilance</a>
      </div>
    </div>
  )
}

export default function App() {
  const page = useHashPage()
  const { lang, setLang } = useLang()
  const AREAS = areas()
  const area = AREAS.find((a) => a.sections.some((s) => s.pages.some((p) => p.id === page)))
  const cur = area?.sections.flatMap((s) => s.pages).find((p) => p.id === page)
  const isHome = page === 'home'
  const [health, setHealth] = useState<Health | null>(null)
  const [healthErr, setHealthErr] = useState(false)
  const [reel, setReel] = useState(false)
  // 폰에서는 사이드바가 서랍으로 열립니다. 화면을 옮기거나 Esc 를 누르면 닫습니다
  const [menu, setMenu] = useState(false)
  const mainRef = useRef<HTMLElement>(null)
  useEffect(() => { api<Health>('/api/health').then(setHealth).catch(() => setHealthErr(true)) }, [])
  useEffect(() => {
    if (!menu) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setMenu(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [menu])
  useEffect(() => {
    setMenu(false)
    document.querySelector('.main')?.scrollTo({ top: 0 })
    document.querySelector('.landing-scroll')?.scrollTo({ top: 0 })
    window.scrollTo({ top: 0 })
  }, [page])
  useEffect(() => {
    document.title = isHome ? t('FlyGate · 분자에서 환자까지, 추론보다 근거가 먼저.', 'FlyGate · From molecule to patient, evidence before inference.')
      : cur ? `${cur.label} · ${area!.name} · FlyGate` : t('찾는 화면이 없습니다 · FlyGate', 'Page not found · FlyGate')
  }, [isHome, cur, area, lang])
  const live = (on: boolean | undefined) => (on ? t('설정됨', 'configured') : healthErr ? t('연결 안 됨', 'unreachable') : '…')
  const asof = health?.signals_asof ?? '2026Q2'
  const other = area && area.id !== 'platform' ? AREAS.find((a) => a.id === (area.id === 'discovery' ? 'vigilance' : 'discovery')) : undefined

  return (
    <BrainProvider>
      <div className="app-bg" />
      <div className={`app ${isHome ? 'is-home' : ''}`}>
        <header className="topbar">
          <button type="button" className="skip-link" onClick={() => mainRef.current?.focus()}>{t('본문으로 건너뛰기', 'Skip to content')}</button>
          <a className="topbar-brand" href="#/" aria-label={t('FlyGate 대문으로', 'FlyGate home')}>
            <img src="/brand/flygate-logo-192_v1.0.0.png" alt="" width="28" height="28" />
            <span>FlyGate</span>
          </a>
          <nav className="topbar-tabs" aria-label={t('제품', 'Products')}>
            {AREAS.map((a) => (
              <a key={a.id} href={`#/${a.home}`} className={a.id === area?.id ? 'on' : ''} aria-current={a.id === area?.id ? 'true' : undefined} style={{ ['--tab' as string]: a.color }}>
                <b>{a.name}</b><small>{a.step}</small>
              </a>
            ))}
          </nav>
          <div className="topbar-right">
            <button type="button" className="topbar-reel" onClick={() => setReel(true)}>
              <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="m8 5 12 7-12 7V5Z" fill="currentColor" /></svg>
              <span>{t('영상', 'Film')}</span>
            </button>
            {/* 폰에서는 자리가 좁아 KO | EN 두 칸 대신 바꿀 언어 하나만 보여 줍니다 */}
            <button type="button" className="lang-one" onClick={() => setLang(lang === 'ko' ? 'en' : 'ko')} aria-label={t('영어로 보기', '한국어로 보기')} lang={lang === 'ko' ? 'en' : 'ko'}>{lang === 'ko' ? 'EN' : 'KO'}</button>
            <div className="lang-toggle" role="group" aria-label={t('언어 선택', 'Language')}>
              <button type="button" className={lang === 'ko' ? 'on' : ''} aria-pressed={lang === 'ko'} onClick={() => setLang('ko')} lang="ko" title="한국어">KO</button>
              <button type="button" className={lang === 'en' ? 'on' : ''} aria-pressed={lang === 'en'} onClick={() => setLang('en')} lang="en" title="English">EN</button>
            </div>
          </div>
        </header>

        {isHome ? (
          <main className="landing-scroll" ref={mainRef} tabIndex={-1}>
            <Landing onOpenShowreel={() => setReel(true)} />
          </main>
        ) : !area || !cur ? (
          <main className="landing-scroll" ref={mainRef} tabIndex={-1}><NotFound page={page} /></main>
        ) : (
          <div className="shell">
            <button type="button" className="nav-toggle" onClick={() => setMenu(true)} aria-expanded={menu} aria-controls="side-nav" style={{ ['--area' as string]: area.color }}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" /></svg>
              <span className="nav-toggle-label"><small>{area.name}</small><b>{cur.label}</b></span>
              <span className="nav-toggle-more">{t('메뉴', 'Menu')}</span>
            </button>
            {menu && <button type="button" className="nav-backdrop" aria-label={t('메뉴 닫기', 'Close menu')} onClick={() => setMenu(false)} />}
            <nav id="side-nav" className={`nav ${menu ? 'open' : ''}`} aria-label={area.name} style={{ ['--area' as string]: area.color }}>
              <button type="button" className="nav-close" onClick={() => setMenu(false)}>{t('닫기', 'Close')} ✕</button>
              <div className="nav-area">
                <span>{area.step}</span>
                <b>{area.name}</b>
                <small>{area.tagline}</small>
              </div>
              {area.sections.map((s, si) => (
                <div key={si} style={{ display: 'contents' }}>
                  {s.title && <div className="nav-sec">{s.title}</div>}
                  {s.pages.map((p) => (
                    <a key={p.id} href={`#/${p.id}`} onClick={() => setMenu(false)} className={`nav-item ${p.id === cur.id ? 'active' : ''}`} aria-current={p.id === cur.id ? 'page' : undefined}>
                      {p.icon}
                      <span className="lbl">{p.label}<small>{p.en}</small></span>
                    </a>
                  ))}
                </div>
              ))}
              {other && (
                <a className="nav-cross" href={`#/${other.home}`} style={{ ['--area' as string]: other.color }}>
                  <span>{other.step}</span>
                  <b>{other.name} →</b>
                  <small>{area.id === 'discovery' ? t('같은 약의 시판 후 보고로 이어 보기', 'Follow the same drug into post-market reports') : t('같은 약의 시판 전 근거 보기', 'See the pre-market evidence for the same drug')}</small>
                </a>
              )}
              <div className="nav-foot">
                <div className="status-row"><span className={`dot ${health?.jev ? 'on' : healthErr ? 'off' : ''}`} /><Term k="NAR">{t('비자기회귀 판단 모델', 'Non-autoregressive judgment model')}</Term> {live(health?.jev)}</div>
                <div className="status-row"><span className={`dot ${health?.nim ? 'on' : healthErr ? 'off' : ''}`} />NVIDIA <Term k="NIM" /> {live(health?.nim)}</div>
                <a className="status-row status-link" href="#/agent"><span className="dot" style={{ background: '#e2a74e' }} />{t('OpenShell 정책 →', 'OpenShell policy →')}</a>
                <div className="status-row"><span className="dot on" /><Term k="MaleCNS">MaleCNS v1.0</Term> · <Term k="FAERS" /> {asof}</div>
              </div>
            </nav>
            <main className="main" ref={mainRef} tabIndex={-1}>
              {cur.el()}
              <PlatformFooter compact />
            </main>
          </div>
        )}
      </div>
      <ShowreelModal open={reel} onClose={() => setReel(false)} />
    </BrainProvider>
  )
}
