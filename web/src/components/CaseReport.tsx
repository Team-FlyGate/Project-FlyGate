import { useEffect, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { fmt, OCCP_LABEL, OUTCOME_LABEL, type Answer, type AssessResult, type Case, type TriageResult } from '../lib/data'
import { ACTION_META } from '../pages/MissionControl'
import { t } from '../lib/i18n'
import './CaseReport.css'

// 사례 분류 화면에서 방금 실행한 결과(반사 판단 · 숙고 · 크리틱)를 '이상사례 개별보고(ICSR) 초기 평가 보고서' 서식으로 묶어 보여 줍니다.
// 화면에 있는 값만 옮겨 적고 새 문장이나 수치를 만들지 않습니다. 검토 · 승인 칸은 비워 두며, 인쇄(PDF 저장)는 브라우저 인쇄를 씁니다.

const n2 = (v: number | null | undefined, d = 2) => (v === null || v === undefined || Number.isNaN(v) ? '–' : v.toFixed(d))
const noul = (a: Answer | undefined) => (a && a.type === 'noul' ? a.noul : null)
const choice = (a: Answer | undefined) => (a && a.type === 'choice' ? a : null)
const score = (a: Answer | undefined) => (a && a.type === 'score' ? a : null)
const top2 = (p: Record<string, number>) => Object.entries(p).sort((x, y) => y[1] - x[1]).slice(0, 2)
const ROLE = (): Record<string, string> => ({ PS: t('주의심 (PS)', 'Primary suspect (PS)'), SS: t('부의심 (SS)', 'Secondary suspect (SS)'), C: t('병용 (C)', 'Concomitant (C)'), I: t('상호작용 (I)', 'Interacting (I)') })

function Bar({ label, lo, hi, value, max = 1, ticks = [0.5] }: { label: string; lo: string; hi: string; value: number | null; max?: number; ticks?: number[] }) {
  if (value === null) return null
  const on = value / max >= 0.5
  return (
    <div className="cr-bar">
      <span className="cr-bar-label">{label}</span>
      <span className={`cr-bar-end ${on ? '' : 'on'}`}>{lo}</span>
      <span className="cr-bar-track">
        {ticks.map((x) => <i key={x} style={{ left: `${(x / max) * 100}%` }} />)}
        <b style={{ left: `${Math.max(0, Math.min(1, value / max)) * 100}%` }} />
        <em style={{ left: `${Math.max(0, Math.min(1, value / max)) * 100}%` }}>{n2(value)}</em>
      </span>
      <span className={`cr-bar-end ${on ? 'on' : ''}`}>{hi}</span>
    </div>
  )
}

const Sec = ({ title, children }: { title: ReactNode; children: ReactNode }) => <section className="cr-sec"><h3>{title}</h3>{children}</section>
const KV = ({ k, children }: { k: string; children: ReactNode }) => <div className="cr-kv"><span>{k}</span><b>{children}</b></div>

export default function CaseReport({ c, tri, asr, timings, onClose }: {
  c: Case; tri: TriageResult; asr: AssessResult | null; timings: Record<string, number>; onClose: () => void
}) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const stamp = useRef(new Date())
  useEffect(() => {
    const prev = document.activeElement instanceof HTMLElement ? document.activeElement : null
    closeRef.current?.focus()
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('keydown', onKey); if (prev?.isConnected) prev.focus() }
  }, [onClose])

  const a = tri.jev.answers
  const ps = c.drugs.find((d) => d.role === 'PS') ?? c.drugs[0]
  const count = (role: string) => c.drugs.filter((d) => d.role === role).length
  const serious = noul(a.serious), expected = noul(a.expected), deep = noul(a.deep)
  const pri = score(a.priority), caus = choice(a.causality), route = choice(a.route), special = choice(a.special)
  const dec = tri.decision, am = ACTION_META[dec.action]
  const sexLabel = c.sex === 'M' ? t('남성', 'Male') : c.sex === 'F' ? t('여성', 'Female') : t('미상', 'Unknown')
  const who = `${c.age === null ? t('연령 미상', 'age unknown') : t(`${c.age}세`, `${c.age} y`)} · ${sexLabel}`
  const outcomes = c.outcomes.length ? c.outcomes.map((o) => OUTCOME_LABEL[o] ?? o).join(' · ') : t('중대 결과 표시 없음', 'No serious outcome code')
  const docNo = `FG-PV-TRI-${stamp.current.getFullYear()}-${c.primaryid}`
  const when = stamp.current.toLocaleString(t('ko-KR', 'en-US'), { hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  const valid = tri.validity ? Object.values(tri.validity.checks) : []
  const last = asr?.rounds[asr.rounds.length - 1]
  const issues = last?.issues ?? []
  const claims = asr?.memo.claims ?? []
  const memoOk = claims.length > 0
  const dc = (v: string | undefined) => (v === 'Y' ? t('예', 'Yes') : v === 'N' ? t('아니오', 'No') : v === 'D' ? t('해당 없음', 'Does not apply') : t('미상', 'Unknown'))
  const passed = claims.filter((cl) => !issues.some((i) => i.claim === cl.id)).length
  const listed = (pt: string): boolean | undefined => asr?.evidence.label.listed?.[pt] ?? (tri.grounding?.label.by_pt?.[pt] ? tri.grounding.label.by_pt[pt].sections.length > 0 : undefined)
  const sdr = (pt: string) => asr?.evidence.faers.find((r) => r.pt === pt)
  const grades = asr?.evidence.grades ?? []
  const unlisted = c.reactions.filter((r) => listed(r) === false), inLabel = c.reactions.filter((r) => listed(r) === true), unknown = c.reactions.filter((r) => listed(r) === undefined)
  const yes = t('기재', 'Listed'), no = t('미기재', 'Not listed'), na = t('미평가', 'Not assessed')
  const TIMING: [string, string, string][] = [
    ['intake', 'Intake', t('FAERS ICSR 입력', 'FAERS ICSR intake')], ['rule', 'Rule gate', t('ICH 최소 4요소 확인', 'ICH minimum four elements')],
    ['reflex', 'Reflex', t('판단 모델 7문항 판단', 'Judgment model, 7 questions')], ['route', 'Router', t('결정 정책 적용 (허가사항 조회 포함)', 'Decision policy (incl. label lookup)')],
    ['evidence', 'Memory', t('FAERS 통계 · 허가사항 · 문헌 · 근거 등급 수집', 'FAERS statistics · label · literature · evidence grades')],
    ['deliberate', 'Deliberate', t('NVIDIA Nemotron 평가 메모 작성', 'NVIDIA Nemotron assessment memo')], ['critic', 'Critic ×3', t('규칙 · 숫자 오라클 · 과잉해석 판정', 'Rules · number oracle · overclaim judgment')],
    ['action', 'Action', t('담당자 검토 큐 전달', 'Hand-off to the reviewer queue')],
  ]

  return createPortal(
    <div className="cr-overlay" role="dialog" aria-modal="true" aria-labelledby="cr-title">
      <div className="cr-toolbar">
        <span className="mono">{docNo}</span>
        <span className="cr-toolbar-right">
          <button type="button" className="btn primary" onClick={() => window.print()}>{t('인쇄 · PDF로 저장', 'Print · Save as PDF')}</button>
          <button type="button" className="btn ghost" ref={closeRef} onClick={onClose}>{t('닫기 · Esc', 'Close · Esc')}</button>
        </span>
      </div>

      <article className="cr-paper">
        <header className="cr-head">
          <div><div className="cr-brand">Fly<b>Vigilance</b></div><div className="cr-sub" id="cr-title">{t('이상사례 개별보고(ICSR) 초기 평가 보고서', 'Individual case safety report (ICSR) · initial assessment')}</div></div>
          <div className="cr-head-right"><b>{ps?.drug ?? '–'} · {who}</b><span>Case ID: {c.primaryid}</span></div>
        </header>

        <div className="cr-cols">
          <aside className="cr-side">
            <h4>{t('환자', 'Patient')}</h4>
            <KV k={t('연령 · 성별', 'Age · sex')}>{who}</KV>
            {special && <KV k={t('특수 집단', 'Special population')}>{special.choice}</KV>}
            {ps?.indication && <KV k={t('적응증 (보고 기재)', 'Indication (as reported)')}>{ps.indication}</KV>}
            <KV k={t('결과', 'Outcome')}><span className={c.outcomes.includes('DE') ? 'cr-red' : ''}>{outcomes}</span></KV>
            <h4>{t('보고 정보', 'Report')}</h4>
            <KV k={t('보고 출처', 'Source')}>FDA FAERS</KV>
            <KV k="Primary ID">{c.primaryid}</KV>
            <KV k="Case ID">{c.caseid}</KV>
            {c.rept_cod && <KV k={t('보고 유형', 'Report type')}>{c.rept_cod}</KV>}
            <KV k={t('FDA 접수일', 'FDA received')}>{c.fda_dt}</KV>
            <KV k={t('발생 국가', 'Country')}>{c.country ?? t('미상', 'Unknown')}</KV>
            <KV k={t('보고자 유형', 'Reporter')}>{c.occp_cod ? OCCP_LABEL[c.occp_cod] ?? c.occp_cod : t('미상', 'Unknown')}</KV>
            <h4>{t('의약품', 'Drugs')}</h4>
            <KV k={ROLE().PS}>{ps?.drug ?? '–'}</KV>
            <KV k={ROLE().SS}>{t(`${count('SS')}종`, `${count('SS')}`)}</KV>
            <KV k={ROLE().C}>{t(`${count('C')}종`, `${count('C')}`)}</KV>
            <h4>{t('평가 정보', 'Assessment')}</h4>
            <KV k={t('평가 방법', 'Method')}>{asr ? t('반사 판단 + Nemotron 숙고 + 3단 크리틱', 'Reflex triage + Nemotron deliberation + 3-tier critic') : t('반사 판단', 'Reflex triage')}</KV>
            <KV k={t('실행일시', 'Run at')}>{when}</KV>
            {valid.length > 0 && <KV k={t('최소 요건', 'Minimum criteria')}>ICH E2D {valid.filter(Boolean).length}/{valid.length}</KV>}
            {asr && <KV k={t('크리틱', 'Critic')}>{memoOk ? t(`${passed} / ${claims.length} 주장 통과`, `${passed} / ${claims.length} claims passed`) : t('메모가 작성되지 않음', 'No memo was written')}</KV>}
            <KV k={t('자료원', 'Data')}>FAERS {c.quarter}</KV>
            <h4>{t('검토 · 승인', 'Review · approval')}</h4>
            <div className="cr-sign"><span>{t('검토', 'Reviewed by')}</span><i /></div>
            <div className="cr-sign"><span>{t('승인', 'Approved by')}</span><i /></div>
          </aside>

          <div className="cr-summary">
            <h2>SUMMARY</h2>
            <Sec title={t('A. 평가 결론', 'A. Conclusion')}>
              <p className="cr-verdict">{am?.label ?? dec.action}</p>
              <p>{t(`판단 모델의 중대성 확률은 ${n2(serious)}, 허가사항 기재 확률은 ${n2(expected)}입니다. 결정 정책이 이 값과 허가사항 조회 결과로 처리 경로를 정했습니다.`,
                `The judgment model gives seriousness ${n2(serious)} and label-listed ${n2(expected)}. The decision policy set the route from these values and the label lookup.`)}</p>
              <div className="cr-table3">
                <span>{t('처리 경로', 'Route')}</span><b>{am?.label ?? dec.action}</b><span>{dec.report15 ? t('15일 보고 검토', '15-day reporting review') : dec.deadline ?? `tier ${dec.tier}`}</span>
                {caus && <><span>{t('인과성 (WHO-UMC)', 'Causality (WHO-UMC)')}</span><b>{caus.choice}</b><span>{top2(caus.probabilities).map(([k, v]) => `${k} ${n2(v)}`).join(' · ')}</span></>}
                <span>{t('전문가 심층 검토', 'Expert deliberation')}</span><b>{!asr ? t('실행하지 않음', 'Not run') : memoOk ? t('Nemotron 평가 메모 작성', 'Nemotron memo written') : t('메모가 작성되지 않음', 'No memo was written')}</b><span>{!asr ? '–' : !memoOk ? t('다시 실행 필요', 'Run again') : asr.verdict === 'pass' ? t('크리틱 통과', 'Critic passed') : t('크리틱 반려', 'Critic returned')}</span>
              </div>
              {dec.reasons.length > 0 && <ul className="cr-reasons">{dec.reasons.map((r) => <li key={r}>{r}</li>)}</ul>}
            </Sec>
            <Sec title={t('B. 판정 지표', 'B. Indicators')}>
              <Bar label={t('중대성 (ICH E2A)', 'Seriousness (ICH E2A)')} lo={t('비중대', 'Non-serious')} hi={t('중대', 'Serious')} value={serious} />
              <Bar label={t('허가사항 기재', 'Listed in label')} lo={no} hi={yes} value={expected} />
              <Bar label={t('심층 검토 필요', 'Needs deliberation')} lo={t('불필요', 'No')} hi={t('필요', 'Yes')} value={deep} />
              {pri && <Bar label={t('검토 우선순위', 'Review priority')} lo={t('일상', 'Routine')} hi={t('신속', 'Expedited')} value={pri.score} max={3} ticks={[1, 2]} />}
              {special && <Bar label={t('특수 상황', 'Special situation')} lo={t('해당 없음', 'None')} hi={special.choice} value={special.confidence} />}
            </Sec>
            {grades.length > 0 && <Sec title={t('C. 근거 등급 (집단 수준)', 'C. Evidence grade (population level)')}>
              {grades.map((g) => <div key={g.id} className="cr-grade"><span><i>{g.drug}</i> × {g.pt}</span><b className={`cr-g cr-g-${g.grade}`}>{g.grade}</b><span>{g.pv_class_name}{g.stats ? ` · PRR ${n2(g.stats.prr)}` : ''}</span></div>)}
            </Sec>}
            <Sec title={t('D. 보고된 이상사례 (MedDRA PT)', 'D. Reported events (MedDRA PT)')}>
              {unlisted.length > 0 && <div className="cr-pts"><span>{t('허가사항 미기재', 'Not listed in the label')}</span><b>{unlisted.join(', ')}</b></div>}
              {inLabel.length > 0 && <div className="cr-pts"><span>{t('허가사항 기재', 'Listed in the label')}</span><b>{inLabel.join(', ')}</b></div>}
              {unknown.length > 0 && <div className="cr-pts"><span>{na}</span><b>{unknown.join(', ')}</b></div>}
            </Sec>
            <p className="cr-foot-note">{t('평가 결론은 결정 정책에 따른 자동 분류이며, 보고 여부와 인과성의 최종 판단은 약물감시 담당자가 합니다. 판정 지표는 판단 모델의 집단 수준 보정 확률이고 개별 사례에 대한 확신도가 아닙니다. 근거 등급은 집단 수준의 분류 후보입니다.',
              'The conclusion is an automatic classification by the decision policy; the pharmacovigilance reviewer makes the final reporting and causality decisions. Indicators are population-level calibrated probabilities, not certainty about this case. Evidence grades are population-level candidate classifications.')}</p>
          </div>
        </div>

        <h2 className="cr-h2">DETAILS</h2>
        <Sec title={t('A-1. 의약품 정보', 'A-1. Drugs')}>
          <table className="cr-tbl"><thead><tr><th>No.</th><th>{t('구분', 'Role')}</th><th>{t('성분명', 'Drug')}</th><th>{t('적응증 (보고 기재)', 'Indication (as reported)')}</th><th>{t('투여 중단 / 재투여', 'Dechallenge / rechallenge')}</th></tr></thead>
            <tbody>{c.drugs.map((d, i) => <tr key={i}><td>{i + 1}</td><td className={d.role === 'PS' ? 'cr-blue' : ''}>{ROLE()[d.role] ?? d.role}</td><td><b>{d.drug}</b></td><td>{d.indication ?? '–'}</td><td>{dc(d.dechal)} / {dc(d.rechal)}</td></tr>)}</tbody></table>
        </Sec>
        <Sec title={t('A-2. 이상사례 정보', 'A-2. Events')}>
          <table className="cr-tbl"><thead><tr><th>No.</th><th>{t('이상사례 (MedDRA PT)', 'Event (MedDRA PT)')}</th><th>{t('미국 허가사항 기재', 'US label')}</th><th>{t('FAERS 불균형 신호', 'FAERS disproportionality')}</th></tr></thead>
            <tbody>{c.reactions.map((r, i) => { const l = listed(r), s = sdr(r); return <tr key={r}><td>{i + 1}</td><td><b><i>{r}</i></b></td>
              <td className={l === false ? 'cr-red' : l === undefined ? 'cr-dim' : ''}>{l === true ? yes : l === false ? no : na}</td>
              <td className={s ? (s.evans && s.ror_sig && s.ic_sig ? 'cr-blue' : '') : 'cr-dim'}>{s ? (s.a < 3 || s.note ? t('산출 불가', 'Not computable') : s.evans && s.ror_sig && s.ic_sig ? t('신호 있음 · 3중 기준 충족', 'Signal · triple criterion met') : t('신호 기준 미충족', 'Below signal criteria')) : na}</td></tr> })}</tbody></table>
        </Sec>
        <Sec title={t('B. 평가 결과', 'B. Results')}>
          <table className="cr-tbl"><thead><tr><th>{t('평가 항목', 'Item')}</th><th>{t('판정', 'Result')}</th><th>{t('판단 확률', 'Probability')}</th></tr></thead><tbody>
            <tr><td>{t('중대성 · ICH E2A', 'Seriousness · ICH E2A')}</td><td>{serious === null ? '–' : serious >= 0.5 ? t('중대', 'Serious') : t('비중대', 'Non-serious')} <span className="cr-dim">({outcomes})</span></td><td>{n2(serious)}</td></tr>
            <tr><td>{t('예측성', 'Expectedness')}</td><td>{expected === null ? '–' : expected >= 0.5 ? t('예상됨 (허가사항 기재)', 'Expected (listed)') : t('예상하지 못함 (허가사항 미기재)', 'Unexpected (not listed)')}</td><td>{n2(expected)}</td></tr>
            {caus && <tr><td>{t('인과성 · WHO-UMC', 'Causality · WHO-UMC')}</td><td>{caus.choice}</td><td>{top2(caus.probabilities).map(([k, v]) => `${k} ${n2(v)}`).join(' · ')}</td></tr>}
            {special && <tr><td>{t('특수 상황', 'Special situation')}</td><td>{special.choice}</td><td>{n2(special.confidence)}</td></tr>}
            {pri && <tr><td>{t('검토 우선순위', 'Review priority')}</td><td>{pri.legend?.[String(Math.round(pri.score))] ?? '–'}</td><td>{n2(pri.score)} / 3</td></tr>}
            <tr><td>{t('전문가 심층 검토', 'Expert deliberation')}</td><td>{deep === null ? '–' : deep >= 0.5 ? t('필요', 'Needed') : t('불필요', 'Not needed')}</td><td>{n2(deep)}</td></tr>
            {route && <tr><td>{t('규정상 다음 행동', 'Next action')}</td><td>{route.choice}</td><td>{top2(route.probabilities).map(([k, v]) => `${k} ${n2(v)}`).join(' · ')}</td></tr>}
            <tr><td>{t('처리 경로', 'Route')}</td><td colSpan={2}><b className="cr-red">{am?.label ?? dec.action}</b></td></tr>
          </tbody></table>
        </Sec>

        {asr ? <>
          <Sec title={t('C-1. 허가사항 (미국 FDA 라벨)', 'C-1. Label (US FDA)')}>
            {asr.evidence.label.found ? <>
              <p>{asr.evidence.label.brand}{asr.evidence.label.effective ? t(` (시행일 ${asr.evidence.label.effective})`, ` (effective ${asr.evidence.label.effective})`) : ''}</p>
              {(asr.evidence.label.hits ?? []).map((h) => <blockquote key={h.id} className="cr-quote"><b>{h.pt}</b> · {h.section}<br />“{h.quote}”<code>{h.id}</code></blockquote>)}
              {!(asr.evidence.label.hits ?? []).length && <p className="cr-dim">{t('보고된 반응에 해당하는 기재를 찾지 못했습니다.', 'No label text matching the reported events was found.')}</p>}
            </> : <p className="cr-dim">{t('허가사항을 찾지 못했습니다.', 'No label found.')}</p>}
          </Sec>
          <Sec title={t(`C-2. FAERS 불균형 분석 (${c.quarter})`, `C-2. FAERS disproportionality (${c.quarter})`)}>
            <table className="cr-tbl"><thead><tr><th>{t('약물 × 이상사례', 'Drug × event')}</th><th>{t('보고 수 (a)', 'Reports (a)')}</th><th>PRR [95% CI]</th><th>ROR₀₂₅</th><th>IC₀₂₅</th><th>{t('신호 기준', 'Criteria')}</th></tr></thead>
              <tbody>{asr.evidence.faers.map((r) => { const ok = r.a >= 3 && !r.note; return <tr key={r.id}><td><i>{asr.evidence.suspect}</i> × {r.pt}</td><td>{fmt.int(r.a)}</td>
                {ok ? <><td>{n2(r.prr)} [{n2(r.prr_lo)}–{n2(r.prr_hi)}]</td><td>{n2(r.ror_lo)}</td><td>{n2(r.ic025)}</td><td>{[r.evans && 'Evans', r.ror_sig && 'ROR', r.ic_sig && 'IC'].filter(Boolean).join(' · ') || '–'}</td></>
                  : <td colSpan={4} className="cr-dim">{r.note ?? t('산출 불가', 'Not computable')}</td>}</tr> })}</tbody></table>
            <p className="cr-small">{t('통계값은 DuckDB가 SQL로 계산했으며 언어모델은 수치를 만들거나 바꾸지 않습니다. 불균형 보고 신호는 인과관계의 증거가 아니라 검토를 시작할 근거입니다.', 'Statistics are computed in SQL by DuckDB; language models do not create or change numbers. A disproportionality signal is a reason to start a review, not evidence of causation.')}</p>
          </Sec>
          <Sec title={t('C-3. 문헌 (PubMed)', 'C-3. Literature (PubMed)')}>
            <table className="cr-tbl"><thead><tr><th>{t('이상사례', 'Event')}</th><th>{t('검색 문헌', 'Found')}</th><th>{t('분석 연구 지지', 'Analytic support')}</th><th>PMID</th></tr></thead>
              <tbody>{Object.entries(asr.evidence.pubmed).map(([pt, v]) => { const g = grades.find((x) => x.pt === pt)?.axes.literature; return <tr key={pt}><td><i>{pt}</i></td><td>{v.count ?? '–'}</td><td>{g ? `${g.analytic_supportive} / ${g.analytic_read}` : '–'}</td><td className="cr-mono">{v.pmids.slice(0, 6).join(', ') || '–'}</td></tr> })}</tbody></table>
          </Sec>
          {grades.length > 0 && <Sec title={t('C-4. 근거 등급 (집단 수준)', 'C-4. Evidence grade (population level)')}>
            <table className="cr-tbl"><thead><tr><th>{t('약물 × 이상사례', 'Drug × event')}</th><th>{t('등급', 'Grade')}</th><th>{t('분류', 'Class')}</th><th>{t('사유', 'Basis')}</th></tr></thead>
              <tbody>{grades.map((g) => <tr key={g.id}><td><i>{g.drug}</i> × {g.pt}</td><td><b className={`cr-g cr-g-${g.grade}`}>{g.grade}</b></td><td>{g.pv_class_name}</td><td>{g.summary}</td></tr>)}</tbody></table>
          </Sec>}
          <Sec title={t('D. 종합 평가 의견', 'D. Overall assessment')}>
            {asr.memo.narrative ? <p>{asr.memo.narrative}</p> : <p className="cr-note">{t('이번 실행에서 Nemotron이 평가 메모를 완성하지 못했습니다. 숙고를 다시 실행한 뒤 보고서를 다시 만들어 주세요. 위의 근거(C-1 ~ C-4)는 메모와 무관하게 수집된 값입니다.', 'Nemotron did not complete an assessment memo in this run. Run deliberation again and regenerate the report. The evidence above (C-1 to C-4) was collected independently of the memo.')}</p>}
            <p className="cr-small">{t(`NVIDIA Nemotron(${last?.model ?? ''})이 쓴 평가 메모 원문입니다. 판정: ${asr.memo.assessment}`, `Assessment memo as written by NVIDIA Nemotron (${last?.model ?? ''}). Verdict: ${asr.memo.assessment}`)}</p>
          </Sec>
          {(asr.memo.open_questions?.length ?? 0) > 0 && <Sec title={t('E. 추가 확인 사항', 'E. Open questions')}>
            <ol className="cr-ol">{asr.memo.open_questions!.map((q) => <li key={q}>{q}</li>)}</ol>
          </Sec>}
        </> : <p className="cr-note">{t('Nemotron 숙고를 실행하지 않아 근거(허가사항 · FAERS 통계 · 문헌 · 근거 등급)와 평가 메모는 이 보고서에 없습니다. 사례 분류 화면에서 숙고를 실행한 뒤 다시 만들면 포함됩니다.',
          'Nemotron deliberation was not run, so the evidence (label · FAERS statistics · literature · grades) and the assessment memo are not in this report. Run deliberation on the triage screen and generate the report again to include them.')}</p>}

        <h2 className="cr-h2">APPENDIX</h2>
        <Sec title={t('I. 반사 판단 원시 출력', 'I. Reflex triage raw output')}>
          <p className="cr-small">{tri.jev.model} · {t('호출 1회', '1 call')} · {fmt.ms(tri.jev.latency_ms)} · {t('입력', 'input')} {fmt.int(tri.jev.usage.input_tokens)} tok · {t('출력', 'output')} {fmt.int(tri.jev.usage.output_tokens)} tok{tri.grounding ? ` · ${t('허가사항 조회', 'label lookup')} ${fmt.ms(tri.grounding.latency_ms)}` : ''}</p>
          <table className="cr-tbl"><thead><tr><th>{t('문항', 'Question')}</th><th>{t('출력', 'Output')}</th><th>conf</th></tr></thead>
            <tbody>{Object.entries(a).map(([k, v]) => <tr key={k}><td>{k}</td>
              <td>{v.type === 'noul' ? n2(v.noul) : v.type === 'score' ? `${n2(v.score)} / 3` : top2(v.probabilities).map(([x, p]) => `${x} ${n2(p)}`).join(' · ')}</td>
              <td>{v.type === 'noul' ? '–' : n2(v.confidence)}</td></tr>)}</tbody></table>
        </Sec>
        {asr && <Sec title={t('II. Nemotron 평가 메모 원문과 크리틱 결과', 'II. Nemotron memo and critic results')}>
          <p className="cr-small">{last?.model} · {t(`${asr.rounds.length}회차`, `round ${asr.rounds.length}`)} · {fmt.ms(last?.latency_ms ?? 0)} · {asr.verdict === 'pass' ? t('통과', 'passed') : t('반려', 'returned')}</p>
          {!memoOk && issues.length > 0 && <ul className="cr-reasons">{issues.map((i, k) => <li key={k}>T{i.tier} {i.rule} · {i.detail}</li>)}</ul>}
          {memoOk && <table className="cr-tbl"><thead><tr><th>ID</th><th>{t('주장 (원문)', 'Claim (verbatim)')}</th><th>{t('근거 ID', 'Evidence IDs')}</th><th>{t('크리틱', 'Critic')}</th></tr></thead>
            <tbody>{claims.map((cl) => { const is = issues.filter((i) => i.claim === cl.id); return <tr key={cl.id}><td>{cl.id}</td><td>{cl.text}</td><td className="cr-mono">{cl.evidence.join(' · ')}</td>
              <td className={is.length ? 'cr-red' : 'cr-blue'}>{is.length ? t(`반려 · ${is.map((i) => `T${i.tier} ${i.rule}`).join(', ')}`, `Rejected · ${is.map((i) => `T${i.tier} ${i.rule}`).join(', ')}`) : t('통과', 'Passed')}{cl.overclaim_p !== undefined && <span className="cr-dim"> p {n2(cl.overclaim_p)}</span>}</td></tr> })}</tbody></table>}
          <p className="cr-small">{t('p: 과잉해석 판정 확률(낮을수록 근거 범위 안). 크리틱은 근거 ID 실재, 근거 수치 일치, 과잉해석 여부를 검사하며 내용의 모든 오류를 잡아내지는 않습니다.', 'p: overclaim probability (lower is closer to the evidence). The critic checks that evidence IDs exist, numbers match and claims do not overreach; it does not catch every content error.')}</p>
        </Sec>}
        <Sec title={t('III. 처리 이력', 'III. Processing log')}>
          <table className="cr-tbl"><thead><tr><th>No.</th><th>{t('단계', 'Stage')}</th><th>{t('처리 내용', 'What ran')}</th><th>{t('소요 시간', 'Elapsed')}</th></tr></thead>
            <tbody>{TIMING.filter(([k]) => timings[k] !== undefined).map(([k, l, d], i) => <tr key={k}><td>{i + 1}</td><td>{l}</td><td>{d}</td><td>{fmt.ms(timings[k])}</td></tr>)}</tbody></table>
        </Sec>

        <Sec title="DISCLAIMER">
          <p>{t('이 보고서는 약물감시 담당자의 사례 검토를 돕기 위한 자동 생성 초안이며, 의약품의 안전성이나 개별 사례의 인과관계를 확정하지 않습니다. 보고 여부, 인과성, 근거 등급의 최종 판단은 약물감시 담당자와 규제기관이 합니다. FlyGate는 규제기관의 허가나 인증을 받은 시스템이 아니며 외부 제출을 수행하지 않습니다.',
            'This report is an automatically generated draft to support case review by a pharmacovigilance reviewer. It does not establish the safety of a medicine or causation in an individual case. Final decisions on reporting, causality and evidence grading rest with the reviewer and the regulator. FlyGate is not approved or certified by any regulator and does not submit anything externally.')}</p>
        </Sec>
        <footer className="cr-footer"><b>FLYGATE</b><span>{t('문서번호', 'Document')} {docNo}</span><span>{t('생성', 'Generated')} {when}</span><span>{t('자료원', 'Data')} FDA FAERS {c.quarter}</span><span>{t('자동 생성 초안 · 담당자 검토 전 효력 없음', 'Auto-generated draft · not valid before reviewer sign-off')}</span></footer>
      </article>
    </div>, document.body,
  )
}
