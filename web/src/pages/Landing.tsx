import { useEffect, useRef, useState } from 'react'
import { t, useLang } from '../lib/i18n'
import { evidence } from '../lib/marketingEvidence'
import PlatformFooter from '../components/PlatformFooter'
import './Landing.css'

type DataConnection = EventTarget & { saveData?: boolean }

function Background() {
  const video = useRef<HTMLVideoElement>(null)
  const [allowed, setAllowed] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
    const connection = (navigator as Navigator & { connection?: DataConnection }).connection
    const update = () => setAllowed(!motion.matches && !connection?.saveData)
    update()
    motion.addEventListener('change', update)
    connection?.addEventListener('change', update)
    return () => { motion.removeEventListener('change', update); connection?.removeEventListener('change', update) }
  }, [])
  useEffect(() => {
    if (allowed && !failed) void video.current?.play().catch(() => setFailed(true))
  }, [allowed, failed])
  return <>
    <div className="lp-backdrop" aria-hidden="true">{/* 움직임 줄이기 · 데이터 절약 설정이면 자동재생하지 않고, 아래 버튼을 눌렀을 때만 내려받아 재생합니다 */}{!failed && <video ref={video} autoPlay={allowed} muted loop playsInline preload={allowed ? 'metadata' : 'none'} poster="/showreel/FlyGate_bg_poster_v1.1.0.jpg" src="/showreel/FlyGate_bg_loop_v1.1.0.mp4" onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onError={() => setFailed(true)} />}</div>
    {!failed && <button className="lp-motion" type="button" onClick={() => { const node = video.current; if (!node) return; if (node.paused) void node.play().catch(() => setFailed(true)); else node.pause() }} aria-label={playing ? t('배경 영상 일시정지', 'Pause background video') : t('배경 영상 재생', 'Play background video')}>{playing ? t('배경 일시정지', 'Pause background') : t('배경 재생', 'Play background')}</button>}
  </>
}

const REPO = 'https://github.com/Team-FlyGate/Project-FlyGate'
const INSTALL = `git clone ${REPO} && cd Project-FlyGate && ./scripts/install_flygate.sh`

function Command({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    void navigator.clipboard?.writeText(text).then(() => { setCopied(true); window.setTimeout(() => setCopied(false), 1600) }).catch(() => {})
  }
  return <div className="lp-cmd">
    {label && <span className="lp-cmd-label">{label}</span>}
    <code><i aria-hidden="true">$ </i>{text}</code>
    <button type="button" onClick={copy} aria-label={t('명령 복사', 'Copy command')}>{copied ? t('복사됨', 'Copied') : t('복사', 'Copy')}</button>
  </div>
}

export default function Landing({ onOpenShowreel }: { onOpenShowreel: () => void }) {
  useLang()
  const metrics = evidence()
  const go = (id: string) => (event: { preventDefault: () => void }) => { event.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'instant' }) }
  const steps = [
    { href: '#/discovery', title: t('구조와 결합', 'Structure & binding'), text: t('PARP1 · 니라파립', 'PARP1 · niraparib') },
    { href: '#/discovery', title: t('실측과 비교', 'Compare measurements'), text: t('ChEMBL 친화도 근거', 'ChEMBL affinity evidence') },
    { href: '#/signals', title: t('안전성 신호', 'Safety signals'), text: t('FAERS 보고 탐색', 'Explore FAERS reports') },
    { href: '#/triage', title: t('사례 검토', 'Case review'), text: t('근거와 검토 경로', 'Evidence & review routes') },
    { href: '#/korea', title: t('사람의 판단', 'Human judgment'), text: t('국내 인과성 평가 지원', 'Korean causality assessment support') },
  ]
  // 명령은 README 의 'flygate CLI' 절에 있는 것만 씁니다.
  const uses = [
    { cmd: 'flygate discover parp1', href: '#/discovery', title: t('표적 결합 평가', 'Target-binding evaluation'), text: t('구조 예측 · 도킹 · 친화도 예측을 돌리고, 근거를 넘는 해석은 크리틱이 반려합니다.', 'Runs structure prediction, docking and affinity prediction; the critic rejects readings that go beyond the evidence.') },
    { cmd: 'flygate triage agent/examples/case_niraparib.json', href: '#/triage', title: t('이상사례 분류', 'Adverse-event triage'), text: t('보고 한 건을 7문항으로 판단해 종결 · 모니터링 · 검토 · 사람 우선으로 나눕니다.', 'Judges one report on seven questions and routes it to close, monitor, review or human-first.') },
    { cmd: 'flygate grade NIRAPARIB thrombocytopenia', href: '#/signals', title: t('신호 근거 등급', 'Signal evidence grading'), text: t('라벨 · 불균형 통계 · 문헌을 모아 약물-반응 쌍의 근거 등급을 냅니다.', 'Combines label text, disproportionality statistics and literature into an evidence grade for a drug–event pair.') },
    { cmd: 'flygate critic agent/examples/claims_niraparib.json', href: '#/d-critic', title: t('주장 검증', 'Claim checking'), text: t('주장마다 근거 ID와 숫자를 대조하고 과잉해석을 걸러 냅니다.', 'Checks each claim against evidence IDs and numbers, and filters over-interpretation.') },
    { cmd: 'flygate kr-causality agent/examples/kr_report.txt --route', href: '#/korea', title: t('국내 보고 · 인과성', 'Korean reports · causality'), text: t('국내 보고 서식을 구조화하고 한국형 인과성 평가를 돕습니다.', 'Structures Korean report forms and supports the Korean causality assessment.') },
    { cmd: 'flygate watch', href: '#/cli', title: t('정기 점검', 'Scheduled checks'), text: t('예약 실행으로 검토 대기열을 만듭니다. 제출은 하지 않습니다.', 'Builds a review queue on a schedule. It never submits anything.') },
  ]
  return <div className="lp-root">
    <section className="lp-hero" aria-labelledby="lp-title">
      <Background />
      <div className="lp-hero-grid">
        <div className="lp-intro">
          <p className="lp-badge"><span>{t('오픈소스', 'Open source')}</span><span>Apache-2.0</span><span>{t('무료', 'Free')}</span></p>
          <h1 id="lp-title">Project FlyGate</h1>
          <p className="lp-tagline">{t('분자에서 환자까지, 추론보다 근거가 먼저.', 'From molecules to patients, evidence before inference.')}</p>
          <p className="lp-intro-note">{t('신약 후보 결합 예측부터 시판 후 부작용 검토까지 근거를 검증하는 오픈소스 AI 에이전트입니다. 숫자가 맞아도, 근거를 넘는 결론은 반려합니다.', 'An open-source AI agent that verifies the evidence, from binding prediction for drug candidates to post-market adverse-event review. Even when the numbers are right, a conclusion that outruns the evidence is rejected.')}</p>
          <div className="lp-actions">
            <a className="btn primary" href="#lp-start" onClick={go('lp-start')}>{t('시작하기', 'Get started')}</a>
            <a className="btn ghost" href={REPO} target="_blank" rel="noopener noreferrer">GitHub <span aria-hidden="true">↗</span></a>
            <button type="button" className="btn ghost" onClick={onOpenShowreel}>{t('영상 보기', 'Watch the film')}</button>
          </div>
          <Command text={INSTALL} />
          <p className="lp-req">{t('Mac · Linux · Windows WSL · NVIDIA API 키 필요', 'Mac · Linux · Windows WSL · NVIDIA API key required')}</p>
        </div>
        <a className="lp-product lp-discovery" href="#/discovery"><span className="lp-step">{t('STEP 1 · 시판 전', 'STEP 1 · Pre-market')}</span><span className="lp-product-glyph" aria-hidden="true">01</span><h2>FlyDiscovery</h2><p>{t('약 출시 전, 신약 후보 물질이 목표 단백질에 붙는지 예측합니다.', 'Before launch: predicts whether a drug candidate binds its target protein.')}</p><dl><div><dt>{t('구조 CA RMSD', 'Structure CA RMSD')}</dt><dd>1.0 Å</dd></div><div><dt>{t('친화도 순위 상관 · 39종', 'Affinity rank correlation · n=39')}</dt><dd>0.767</dd></div></dl><span className="lp-open">{t('FlyDiscovery 열기 →', 'Open FlyDiscovery →')}</span></a>
        <a className="lp-product lp-vigilance" href="#/mission"><span className="lp-step">{t('STEP 2 · 시판 후', 'STEP 2 · Post-market')}</span><span className="lp-product-glyph" aria-hidden="true">02</span><h2>FlyVigilance</h2><p>{t('약 출시 후, 부작용 보고 중 사람이 먼저 볼 사례를 고릅니다.', 'After launch: picks the adverse-event reports a person should see first.')}</p><dl><div><dt>{t('FAERS 수록 분기', 'FAERS quarters covered')}</dt><dd>55</dd></div><div><dt>{t('블라인드 시험 · 중대 사례 검토 도달', 'Blind test · serious cases reaching review')}</dt><dd>247/250</dd></div></dl><span className="lp-open">{t('FlyVigilance 열기 →', 'Open FlyVigilance →')}</span></a>
      </div>
      <div className="lp-hero-bottom"><span>{t('NVIDIA Korea Agentic AI Hackathon 2026 우승작', 'Winner · NVIDIA Korea Agentic AI Hackathon 2026')}</span><a href="#lp-start" onClick={go('lp-start')}>{t('빠른 시작 ↓', 'Quick start ↓')}</a></div>
    </section>

    <section className="lp-section" id="lp-start">
      <p className="lp-eyebrow">{t('빠른 시작', 'Quick start')}</p>
      <h2>{t('세 단계로 시작합니다', 'Up and running in three steps')}</h2>
      <p className="lp-section-intro">{t('FlyGate는 Apache-2.0 라이선스의 무료 오픈소스입니다. 저장소를 받아 설치하면 터미널에서 바로 씁니다.', 'FlyGate is free and open source under the Apache-2.0 license. Clone the repository, install, and use it from your terminal.')}</p>
      <ol className="lp-start">
        <li><span className="lp-step">01</span><h3>{t('설치', 'Install')}</h3><p>{t('저장소를 받아 설치 스크립트를 실행합니다.', 'Clone the repository and run the install script.')}</p><Command text={INSTALL} /></li>
        <li><span className="lp-step">02</span><h3>{t('NVIDIA API 키 연결', 'Connect your NVIDIA API key')}</h3><p>{t('flygate 를 실행하고 /login 을 입력하면 키를 숨김 입력으로 받아 저장합니다. 또는 .env.example 을 .env 로 복사해 아래 한 줄을 채웁니다.', 'Run flygate and type /login to enter the key with hidden input. Or copy .env.example to .env and fill in the line below.')}</p><Command text="NVIDIA_API_KEY=nvapi-..." label=".env" /></li>
        <li><span className="lp-step">03</span><h3>{t('실행', 'Run')}</h3><p>{t('대화형 CLI를 열거나, 명령을 바로 실행해 JSON 결과를 받습니다.', 'Open the interactive CLI, or run a command directly and get JSON back.')}</p><Command text="flygate" /><Command text="flygate discover parp1" /></li>
      </ol>
      <a className="lp-more" href="#/cli">{t('CLI 튜토리얼 전체 보기 →', 'Read the full CLI tutorial →')}</a>
    </section>

    <section className="lp-section">
      <p className="lp-eyebrow">{t('할 수 있는 일', 'What you can do')}</p>
      <h2>{t('명령 하나에 작업 하나', 'One command, one job')}</h2>
      <p className="lp-section-intro">{t('모든 결과에는 근거 ID가 붙고, 보고와 인과성의 최종 판정은 사람이 합니다.', 'Every result carries evidence IDs, and people make the final reporting and causality decisions.')}</p>
      <div className="lp-uses">{uses.map((u) => <a key={u.cmd} href={u.href}><h3>{u.title}</h3><p>{u.text}</p><code><i aria-hidden="true">$ </i>{u.cmd}</code></a>)}</div>
    </section>

    <section className="lp-section" id="lp-journey"><p className="lp-eyebrow">{t('연결된 워크플로', 'Connected workflow')}</p><h2>{t('하나의 약물, 두 단계', 'One drug, two stages')}</h2><p className="lp-section-intro">{t('예시 약물 니라파립(PARP1 억제제)을 따라, 시판 전 탐색에서 시판 후 사례 검토로 이어집니다.', 'Follow the example drug niraparib, a PARP1 inhibitor, from pre-market exploration to post-market case review.')}</p><ol className="lp-flow">{steps.map((step, index) => <li key={step.title}><a href={step.href}><span className="lp-step">{String(index + 1).padStart(2, '0')} <span aria-hidden="true">→</span></span><h3>{step.title}</h3><p>{step.text}</p></a></li>)}</ol></section>

    <section className="lp-section"><p className="lp-eyebrow">{t('평가와 한계', 'Evaluation & limitations')}</p><h2>{t('측정된 근거', 'Measured evidence')}</h2><p className="lp-section-intro">{t('저장소에 있는 평가 결과를 조건과 함께 공개합니다. 각 수치는 해당 시험 범위에서 해석해야 합니다.', 'Evaluation results from the repository, with their conditions. Each metric should be interpreted within the scope of its test.')}</p><div className="lp-delta"><div><strong>302 <i aria-hidden="true">→</i> 138</strong><h3>{t('사람이 먼저 볼 사례', 'Cases a person sees first')}</h3><p>{t('440건 중 사람에게 우선 배정된 사례가 절반 아래로 줄었습니다.', 'Of 440 cases, those assigned to a person first fell by more than half.')}</p></div><div><strong>68 <i aria-hidden="true">→</i> 3</strong><h3>{t('중대하지 않은데 사람에게 올린 사례', 'Non-serious cases sent to a person')}</h3><p>{t('비중대 190건 중 불필요하게 넘긴 사례입니다.', 'Out of 190 non-serious cases, those escalated unnecessarily.')}</p></div><div><strong>16 <i aria-hidden="true">→</i> 3</strong><h3>{t('검토 경로에 오르지 못한 중대 사례', 'Serious cases left without a review path')}</h3><p>{t('중대 250건 중 자동 큐에 남은 사례입니다.', 'Out of 250 serious cases, those left in the automatic queue.')}</p></div><p className="lp-delta-note">{t('미국 FDA 실제 부작용 보고 440건 · 결과 표시를 가린 조건 · 같은 판단 모델에 한 번만 묻는 방식(왼쪽)과 FlyVigilance(오른쪽) 비교', '440 real FDA adverse-event reports · outcome codes hidden · the same judgment model asked once (left) vs. FlyVigilance (right)')} · <a href="#/bench">{t('자세히 보기 →', 'View details →')}</a></p></div><div className="lp-evidence-grid">{metrics.map((item) => <article className={`lp-evidence lp-evidence-${item.product}`} key={item.id}><strong className="lp-value">{item.value}</strong><h3>{item.label()}</h3><p>{item.condition()}</p><a href={item.href}>{t('자세히 보기 →', 'View details →')}</a><details><summary>{t('원본 위치', 'Source location')}</summary><code>{item.source}</code></details></article>)}</div></section>

    <section className="lp-section">
      <p className="lp-eyebrow">{t('오픈소스', 'Open source')}</p>
      <h2>{t('코드도, 평가도 열려 있습니다', 'The code and the evaluations are open')}</h2>
      <div className="lp-tools">
        <a href={REPO} target="_blank" rel="noopener noreferrer"><span className="lp-step">Apache-2.0</span><h3>{t('소스 코드', 'Source code')}</h3><p>{t('에이전트, 파이프라인, 평가 스크립트, 이 웹사이트까지 한 저장소에 있습니다.', 'The agent, pipelines, evaluation scripts and this website live in one repository.')}</p><span className="lp-open">{t('GitHub 저장소 ↗', 'GitHub repository ↗')}</span></a>
        <a href="#/skills"><span className="lp-step">{t('정책과 경계', 'Policies & boundaries')}</span><h3>{t('스킬 · 거버넌스', 'Skills & governance')}</h3><p>{t('능력마다 입출력 계약과 허용 호스트를 적은 스킬, 샌드박스 정책을 확인합니다.', 'Inspect skills that declare input/output contracts and allowed hosts, plus the sandbox policy.')}</p><span className="lp-open">{t('스킬 살펴보기 →', 'Explore skills →')}</span></a>
        <a href={`${REPO}/issues`} target="_blank" rel="noopener noreferrer"><span className="lp-step">{t('참여', 'Get involved')}</span><h3>{t('이슈 · 제안', 'Issues & ideas')}</h3><p>{t('버그 제보와 기능 제안은 GitHub 이슈로 받습니다.', 'Bug reports and feature requests are welcome as GitHub issues.')}</p><span className="lp-open">{t('이슈 열기 ↗', 'Open an issue ↗')}</span></a>
      </div>
    </section>

    <section className="lp-section lp-scope"><h2>{t('이 사이트에서 보는 것', 'What this site shows')}</h2><p>{t('이 사이트는 같은 코드를 저장된 평가 결과와 함께 돌려 보는 화면입니다. 관제 스트림은 저장된 사례의 리플레이이며 실시간 환자 감시가 아닙니다. FlyGate는 연구와 판단을 돕는 도구이고, 보고와 인과성의 최종 판정은 사람이 합니다.', 'This site runs the same code against stored evaluation results. The operations stream replays stored cases; it is not live patient monitoring. FlyGate supports research and judgment, and people make the final reporting and causality decisions.')}</p><a href="#/validation">{t('평가 조건과 한계 읽기 →', 'Read evaluation conditions and limitations →')}</a></section>
    <PlatformFooter />
  </div>
}