import { useEffect, useState, type ReactNode } from 'react'
import { Card, Loading, PageHead } from '../components/ui'
import Term from '../components/Term'
import { api } from '../lib/data'
import { t } from '../lib/i18n'

type Match = 'term' | 'ancestor' | 'none'
interface Assoc { score: number | null; score_no_literature: number | null; row_found: boolean }
interface PairRec {
  drug: string; pt: string; term: string | null; mapping: string
  safety_match: { target: string; index: number; relation: Match }[] | null
  assoc: Assoc | null; safety_recorded: boolean
}
type Item =
  | { id: string; layer: 'L1'; what: string; n: { liabilities: number | null } }
  | { id: string; layer: 'L2'; what: string; n: null; match: Match }
  | { id: string; layer: 'L3'; what: string; n: { median_tpm: number; rank_of_54: number } }
  | { id: string; layer: 'L4'; what: string; n: { score: number | null; score_no_literature: number | null } }
interface OmicsTerm {
  id: string | null; label: string | null; match: string; source: string | null
  organs: { sites: string[]; method: string; evidence: { ancestor: string; word: string }[] } | null
}
interface DrugsResp { asof: string | null; drugs: string[] }
interface PairsResp { drug: string; asof: string | null; pairs: PairRec[] }
interface PairResp { drug: string; pt: string; asof: string | null; pair: PairRec; items: Item[]; memo_items: Item[]; term: OmicsTerm | null }

type Load<T> = { s: 'idle' } | { s: 'loading' } | { s: 'ok'; v: T } | { s: 'missing' } | { s: 'error'; msg: string }
const MISSING = /is not in the omics extract$/

function useApi<T>(path: string | null): Load<T> {
  const [st, setSt] = useState<{ path: string | null; r: Load<T> }>({ path: null, r: { s: 'idle' } })
  useEffect(() => {
    if (!path) return
    let live = true
    api<T>(path).then((v) => { if (live) setSt({ path, r: { s: 'ok', v } }) })
      .catch((e: Error) => { if (live) setSt({ path, r: MISSING.test(e.message) ? { s: 'missing' } : { s: 'error', msg: e.message } }) })
    return () => { live = false }
  }, [path])
  if (!path) return { s: 'idle' }
  return st.path === path ? st.r : { s: 'loading' }
}

const readHash = () => {
  const p = new URLSearchParams(location.hash.split('?')[1] ?? '')
  return { drug: p.get('drug')?.toUpperCase() || null, pt: p.get('pt')?.toLowerCase() || null }
}
const go = (drug: string | null, pt: string | null = null) => {
  const p = new URLSearchParams()
  if (drug) p.set('drug', drug)
  if (pt) p.set('pt', pt)
  const s = p.toString()
  location.hash = `/omics${s ? `?${s}` : ''}`
}

// 항목에는 id 와 what 문장만 있어, 열은 api/_fv/omics.py 의 ID 형식과 문장 틀에서 읽습니다. 틀이 바뀌면 칸이 '-' 로 비고 원문은 행 title 에 남습니다
const idPart = (id: string, i: number) => id.split('@')[0].split(':')[i] ?? null
const grab = (s: string, re: RegExp) => s.match(re)?.slice(1) ?? null
const recorded = (x: string | undefined) => (x === undefined || x === 'not recorded' || x === 'no event ID' ? null : x)
const dash = (x: ReactNode) => x ?? <span className="dim">-</span>
const raw = (x: number | null) => (x == null ? '-' : String(x))

const byLayer = <L extends Item['layer']>(items: Item[], l: L) => items.filter((i): i is Extract<Item, { layer: L }> => i.layer === l)

function NotInExtract({ what }: { what: string }) {
  return <Card><div style={{ color: 'var(--warn)' }}>{t(`${what}: 추출본에 없음`, `${what}: not in the extract`)}</div>
    <div className="note" style={{ marginTop: 6 }}>{t('오믹스 추출본은 빌드 시점에 정한 약물과 쌍만 담습니다. 없다는 것은 조회하지 않았다는 뜻이지, 기전 근거가 없다는 뜻이 아닙니다.', 'The omics extract holds only the drugs and pairs chosen at build time. Absence means it was not queried, not that no mechanistic evidence exists.')}</div></Card>
}

function Status({ r, what }: { r: Load<unknown>; what: string }) {
  if (r.s === 'loading') return <Loading />
  if (r.s === 'missing') return <NotInExtract what={what} />
  if (r.s === 'error') return <Card><div style={{ color: 'var(--bad)' }}>{r.msg}</div></Card>
  return null
}

function MatchBadge({ m }: { m: Match }) {
  if (m === 'term') return <span className="chip bad" style={{ fontSize: 10 }}>{t('용어 일치', 'term match')}</span>
  if (m === 'ancestor') return <span className="chip warn" style={{ fontSize: 10 }}>{t('상위 개념 일치', 'ancestor match')}</span>
  return <span className="chip dim" style={{ fontSize: 10, opacity: 0.5 }}>{t('일치 없음', 'no match')}</span>
}

function Mapping({ m }: { m: string }) {
  return m === 'none' ? <span className="chip dim" style={{ fontSize: 10 }}>{t('매핑 안 됨', 'not mapped')}</span>
    : <span className="chip ok" style={{ fontSize: 10 }}>{m}</span>
}

function LayerTable<I extends Item>({ title, sub, head, items, memo, row, empty, hot }: {
  title: ReactNode; sub: ReactNode; head: ReactNode; items: I[]; memo: Set<string>; row: (i: I) => ReactNode; empty: ReactNode; hot?: (i: I) => boolean
}) {
  return (
    <Card title={<>{title} <span className="dim" style={{ fontSize: 12, fontWeight: 400 }}>· {items.length}</span></>} sub={sub} className="span2">
      {items.length === 0 ? <div className="note">{empty}</div> : (
        <div style={{ overflow: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>{t('근거 ID', 'Evidence ID')}</th>{head}</tr></thead>
            <tbody>{items.map((i) => (
              <tr key={i.id} title={i.what} style={{ background: hot?.(i) ? 'rgba(255,93,108,0.07)' : undefined }}>
                <td><span className="mono" style={{ fontSize: 10.5, wordBreak: 'break-all' }}>{i.id}</span>{memo.has(i.id) && <> <span className="chip jev" style={{ fontSize: 9 }}>{t('메모', 'memo')}</span></>}</td>
                {row(i)}
              </tr>))}</tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

function PairHead({ r }: { r: PairResp }) {
  const p = r.pair, term = r.term, o = term?.organs
  return (
    <Card title={<>{r.drug} × {r.pt} <span className="dim" style={{ fontSize: 13, fontWeight: 400 }}>· {t('추출 기준일', 'extract as of')} {r.asof ?? '-'}</span></>}
      sub={t(`근거 항목 ${r.items.length}건 · 숙고 메모에 들어가는 몫 ${r.memo_items.length}건`, `${r.items.length} evidence items · ${r.memo_items.length} go into the deliberation memo`)} className="span2">
      <div className="grid g3" style={{ gap: 8 }}>
        <div style={{ padding: 8, borderRadius: 10, border: '1px solid var(--line)' }}>
          <div className="dim mono" style={{ fontSize: 9.5 }}>{t('반응 용어 매핑', 'Reaction term mapping')}</div>
          <div style={{ marginTop: 6 }}><Mapping m={p.mapping} /></div>
          {term && term.id && <div style={{ fontSize: 12, marginTop: 4 }}><span className="mono">{term.id}</span> · {term.label ?? '-'} <span className="dim mono" style={{ fontSize: 10 }}>{term.source}</span></div>}
        </div>
        <div style={{ padding: 8, borderRadius: 10, border: '1px solid var(--line)' }}>
          <div className="dim mono" style={{ fontSize: 9.5 }}>{t('후보 장기 · 출처', 'Organ candidates · provenance')}</div>
          {!o ? <div className="note" style={{ marginTop: 6 }}>{t('후보 장기 없음. L3 는 발현 상위 5개 조직을 보입니다', 'No organ candidates. L3 shows the 5 tissues with the highest expression')}</div>
            : <>
              <div className="row wrap" style={{ gap: 4, marginTop: 6 }}>{o.sites.map((s) => <span key={s} className="chip" style={{ fontSize: 10 }}>{s}</span>)}</div>
              <div className="dim mono" style={{ fontSize: 10, marginTop: 4 }}>{o.method}</div>
              {o.evidence.map((e) => <div key={e.ancestor + e.word} className="mono" style={{ fontSize: 10.5 }}>{e.ancestor} · "{e.word}"</div>)}
            </>}
        </div>
        <div style={{ padding: 8, borderRadius: 10, border: '1px solid var(--line)' }}>
          <div className="dim mono" style={{ fontSize: 9.5 }}>{t('표적 안전성 책임 기록', 'Target safety liabilities recorded')}</div>
          <div style={{ fontSize: 12, marginTop: 6 }}>{p.safety_recorded ? t('기록 있음', 'recorded') : t('기록 없음 (0건이 아님)', 'nothing recorded (not zero)')}</div>
          <div className="dim" style={{ fontSize: 10.5 }}>{t(`이 반응과 맞은 책임 ${p.safety_match?.length ?? 0}건`, `${p.safety_match?.length ?? 0} liabilities match this reaction`)}</div>
        </div>
      </div>
    </Card>
  )
}

function PairDetail({ r }: { r: PairResp }) {
  const memo = new Set(r.memo_items.map((i) => i.id))
  const rowFound = r.pair.assoc?.row_found !== false
  const hint = t('행에 마우스를 올리면 근거 문장 원문이 보입니다', 'Hover a row to see the full evidence sentence')
  return <>
    <PairHead r={r} />
    <LayerTable title={t('L1 · 작용 기전 표적', 'L1 · Mechanism-of-action targets')} sub={<>Open Targets · {hint}</>} items={byLayer(r.items, 'L1')} memo={memo}
      head={<><th>{t('표적', 'Target')}</th><th>{t('작용 기전', 'Mechanism')}</th><th className="r">{t('안전성 책임', 'Liabilities')}</th></>}
      empty={t('표적 없음', 'No targets')}
      row={(i) => { const m = grab(i.what, /in Open Targets: (.*?)\. Open Targets (?:lists|records) /); const e = grab(i.what, /^\S+ \((\S+)\)/)
        return <><td><b>{dash(idPart(i.id, 3))}</b> <span className="dim mono" style={{ fontSize: 10 }}>{e?.[0]}</span></td><td style={{ fontSize: 12 }}>{dash(m?.[0] || null)}</td>
          <td className="r num">{i.n.liabilities == null ? <span className="dim">{t('기록 없음', 'nothing recorded')}</span> : i.n.liabilities}</td></> }} />
    <LayerTable title={t('L2 · 표적의 안전성 책임', 'L2 · Target safety liabilities')} sub={<>Open Targets safetyLiabilities · {t('이 반응과 용어 또는 상위 개념으로 맞은 책임을 강조합니다', 'liabilities that match this reaction by term or ancestor are highlighted')}</>}
      items={byLayer(r.items, 'L2')} memo={memo} hot={(i) => i.match !== 'none'}
      head={<><th>{t('표적', 'Target')}</th><th>{t('사건', 'Event')}</th><th>{t('사건 ID', 'Event ID')}</th><th>{t('일치', 'Match')}</th><th>{t('조직', 'Tissues')}</th><th>{t('출처', 'Source')}</th><th><Term k="PubMed">PMID</Term></th></>}
      empty={r.pair.safety_recorded ? t('기록된 안전성 책임 0건', '0 safety liabilities recorded') : t('기록 없음 (0건이 아님)', 'Nothing recorded (not zero)')}
      row={(i) => { const [ev, eid, tis, src, pmid] = grab(i.what, /^Open Targets safety liability of \S+: (.*) \(([^()]*)\); tissues (.*); source (.*), PMID (.*?)\. Population-level/) ?? []
        const pm = recorded(pmid)
        return <><td>{dash(idPart(i.id, 2))}</td><td style={{ fontSize: 12, opacity: i.match === 'none' ? 0.6 : 1 }}>{dash(ev ?? null)}</td><td className="mono" style={{ fontSize: 10.5 }}>{dash(recorded(eid))}</td>
          <td><MatchBadge m={i.match} /></td><td className="mono dim" style={{ fontSize: 10 }}>{dash(recorded(tis))}</td><td style={{ fontSize: 11.5 }}>{dash(recorded(src))}</td>
          <td>{pm ? <a href={`https://pubmed.ncbi.nlm.nih.gov/${pm}/`} target="_blank" rel="noreferrer">{pm}</a> : <span className="dim">-</span>}</td></> }} />
    <LayerTable title={t('L3 · 표적의 조직별 발현', 'L3 · Target tissue expression')} sub={<>GTEx · {t('후보 장기가 있으면 그 조직 묶음만, 없으면 발현 상위 5개 조직입니다', 'tissues in the candidate organ groups, or the 5 highest-expression tissues when there are none')}</>}
      items={byLayer(r.items, 'L3')} memo={memo}
      head={<><th>{t('표적', 'Target')}</th><th>{t('조직', 'Tissue')}</th><th>{t('조직 묶음', 'Group')}</th><th className="r">{t('중앙값 TPM', 'Median TPM')}</th><th className="r">{t('순위', 'Rank')}</th></>}
      empty={t('발현 값 없음 (0이 아님)', 'No expression values (not zero)')}
      row={(i) => { const g = grab(i.what, /\(tissue group (.*?)\)/); const of = grab(i.what, /rank \d+ of (\d+) tissues/)
        return <><td>{dash(idPart(i.id, 2))}</td><td className="mono" style={{ fontSize: 11 }}>{dash(idPart(i.id, 3))}</td><td>{dash(g?.[0] ?? null)}</td>
          <td className="r num">{i.n.median_tpm}</td><td className="r num">{i.n.rank_of_54}{of && <span className="dim"> / {of[0]}</span>}</td></> }} />
    <LayerTable title={t('L4 · 표적-질환 연관', 'L4 · Target-disease association')} sub={<>Open Targets · {t('문헌 동시 언급만 근거인 점수는 따로 표시합니다', 'scores that rest only on literature co-mention are flagged')}</>}
      items={byLayer(r.items, 'L4')} memo={memo}
      head={<><th className="r">{t('점수', 'Score')}</th><th className="r">{t('문헌 제외 점수', 'Score without literature')}</th><th>{t('문헌만', 'Literature only')}</th></>}
      empty={r.pair.mapping === 'none' ? t('반응 용어가 매핑되지 않아 연관을 조회하지 않았습니다', 'The reaction term is not mapped, so no association was queried') : t('연관을 조회하지 않았습니다', 'No association was queried')}
      row={(i) => !rowFound ? <td colSpan={3} className="dim">{t('연관 행 없음 (기록 없음, 0점이 아님)', 'No association row (nothing recorded, not a zero score)')}</td>
        : <><td className="r num">{raw(i.n.score)}</td><td className="r num">{raw(i.n.score_no_literature)}</td>
          <td>{(i.n.score ?? 0) > 0 && i.n.score_no_literature === 0 ? <span className="chip warn" style={{ fontSize: 10 }}>{t('문헌 동시 언급만', 'literature co-mention only')}</span> : <span className="dim">-</span>}</td></>} />
  </>
}

function Pairs({ drug, pt, r }: { drug: string; pt: string | null; r: PairsResp }) {
  return (
    <Card title={<>{drug} <span className="dim" style={{ fontSize: 13, fontWeight: 400 }}>· {t(`쌍 ${r.pairs.length}개`, `${r.pairs.length} pairs`)} · {t('추출 기준일', 'extract as of')} {r.asof ?? '-'}</span></>}
      sub={t('쌍을 누르면 L1~L4 근거를 펼칩니다', 'Pick a pair to open its L1-L4 evidence')} className="span2">
      {r.pairs.length === 0 ? <div className="note">{t('이 약물에 든 쌍이 없습니다', 'This drug has no pairs in the extract')}</div> : (
        <div style={{ maxHeight: 320, overflow: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>PT</th><th>{t('용어 매핑', 'Term mapping')}</th><th>{t('안전성 책임 기록', 'Liabilities recorded')}</th><th className="r">{t('맞은 책임', 'Matched liabilities')}</th><th>{t('연관 점수', 'Association')}</th></tr></thead>
            <tbody>{r.pairs.map((p) => (
              <tr key={p.pt} onClick={() => go(drug, p.pt)} style={{ cursor: 'pointer', background: pt === p.pt ? 'rgba(55,230,255,0.06)' : undefined }}>
                <td>{p.pt}</td><td><Mapping m={p.mapping} /></td>
                <td>{p.safety_recorded ? t('있음', 'yes') : <span className="dim">{t('기록 없음', 'nothing recorded')}</span>}</td>
                <td className="r num">{p.safety_match == null ? <span className="dim">-</span> : p.safety_match.length}</td>
                <td className="num">{p.assoc == null ? <span className="dim">{t('조회 안 함', 'not queried')}</span> : !p.assoc.row_found ? <span className="dim">{t('연관 행 없음', 'no row')}</span> : raw(p.assoc.score)}</td>
              </tr>))}</tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

export default function Omics() {
  const [{ drug, pt }, setSel] = useState(readHash)
  useEffect(() => { const on = () => setSel(readHash()); window.addEventListener('hashchange', on); return () => window.removeEventListener('hashchange', on) }, [])
  const [q, setQ] = useState('')
  const list = useApi<DrugsResp>('/api/omics/drugs')
  const pairs = useApi<PairsResp>(drug ? `/api/omics?drug=${encodeURIComponent(drug)}` : null)
  const one = useApi<PairResp>(drug && pt ? `/api/omics?drug=${encodeURIComponent(drug)}&pt=${encodeURIComponent(pt)}` : null)
  const drugs = list.s === 'ok' ? list.v.drugs : []
  const pick = (v: string) => { setQ(''); go(v.trim().toUpperCase()) }

  return (
    <div className="page">
      <PageHead eyebrow="Omics evidence · mechanistic context"
        title={t('오믹스 근거는 기전의 맥락이지, 인과가 아닙니다', 'Omics evidence is mechanistic context, not causation')}
        lede={t(<>빌드 시점에 공개 DB 에서 뽑아 둔 추출본을 읽습니다. 약물의 작용 기전 표적(L1), 표적의 안전성 책임(L2), 표적의 조직별 발현(L3), 표적-질환 연관 점수(L4)입니다. 집단 수준의 생물학적 개연성을 보여 줄 뿐, 이 사례에서 약이 반응을 일으켰다는 근거가 아니며, 기전 근거가 없다는 것도 연관에 반하는 근거가 아닙니다(<Term k="overclaim">R14</Term>). PV 분류 등급에는 반영하지 않습니다.</>,
          <>Reads an extract pulled from public databases at build time: the drug's mechanism-of-action targets (L1), the targets' safety liabilities (L2), the targets' tissue expression (L3), and the target-disease association score (L4). It shows biological plausibility at the population level. It never shows that the drug caused the reaction in this case, and missing mechanistic evidence is not evidence against the association (<Term k="overclaim">R14</Term>). The PV classification grade does not use it.</>)}
        right={<div className="row" style={{ gap: 8 }}><span className="chip jev">{t('메모 = 숙고 메모에 들어가는 항목', 'memo = item that goes into the deliberation memo')}</span></div>} />

      <Card style={{ marginBottom: 16 }}>
        <div className="row wrap" style={{ gap: 10 }}>
          <input className="input" list="omics-drugs" style={{ width: 280 }} placeholder={t('약물 (예: NIRAPARIB)', 'Drug (e.g. NIRAPARIB)')} value={q}
            onChange={(e) => { setQ(e.target.value); if (drugs.includes(e.target.value.toUpperCase())) pick(e.target.value) }}
            onKeyDown={(e) => { if (e.key === 'Enter' && q.trim()) pick(q) }} />
          <datalist id="omics-drugs">{drugs.map((d) => <option key={d} value={d} />)}</datalist>
          {drugs.length <= 30 && drugs.map((d) => <button key={d} className="chip" style={{ cursor: 'pointer', color: d === drug ? 'var(--c-sense)' : undefined, borderColor: d === drug ? 'var(--c-sense)' : undefined }} onClick={() => go(d)}>{d}</button>)}
          {list.s === 'ok' && drugs.length === 0 && <span className="note">{t('추출본 없음. 약물 이름을 직접 입력하세요', 'Extract not built. Type a drug name')}</span>}
          {list.s === 'error' && <span className="note" style={{ color: 'var(--bad)' }}>{list.msg}</span>}
          {list.s === 'ok' && <span className="dim mono" style={{ marginLeft: 'auto', fontSize: 11 }}>{t(`약물 ${drugs.length}개`, `${drugs.length} drugs`)} · {list.v.asof ?? '-'}</span>}
        </div>
      </Card>

      {!drug ? <Card><div className="note">{t('약물을 고르면 추출본에 든 반응 쌍이 나옵니다', 'Pick a drug to list its reaction pairs in the extract')}</div></Card> : (
        <div className="grid" style={{ gridTemplateColumns: 'minmax(0,1fr)' }}>
          {pairs.s === 'ok' ? <Pairs drug={drug} pt={pt} r={pairs.v} /> : <Status r={pairs} what={drug} />}
          {pt && pairs.s !== 'missing' && (one.s === 'ok' ? <PairDetail r={one.v} /> : <Status r={one} what={`${drug} × ${pt}`} />)}
        </div>
      )}
    </div>
  )
}
