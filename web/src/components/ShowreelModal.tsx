import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { t, useLang } from '../lib/i18n'
import './ShowreelModal.css'

export default function ShowreelModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { lang } = useLang()
  const dialog = useRef<HTMLDialogElement>(null)
  const close = useRef<HTMLButtonElement>(null)
  const handler = useRef(onClose)
  handler.current = onClose
  useEffect(() => {
    if (!open) return
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const node = dialog.current
    node?.showModal()
    close.current?.focus()
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); handler.current() }
      if (event.key === 'Tab') {
        // Native modal dialogs include the video's browser-owned controls in their focus trap.
        if (!node?.contains(document.activeElement)) { event.preventDefault(); close.current?.focus() }
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      node?.close()
      if (previous?.isConnected) previous.focus()
    }
  }, [open])
  if (!open) return null
  const base = `/showreel/FlyGate_showreel_v4.3.0${lang === 'en' ? '-en' : ''}`
  return createPortal(
    <dialog ref={dialog} className="srm-dialog" role="dialog" aria-modal="true" aria-labelledby="srm-title"
      onCancel={(event) => { event.preventDefault(); onClose() }}
      onClick={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <div className="srm-content">
        <div className="srm-head"><h2 id="srm-title">{t('FlyGate 소개 영상', 'FlyGate film')}</h2><button ref={close} type="button" className="btn ghost" onClick={onClose}>{t('닫기 · Esc', 'Close · Esc')}</button></div>
        {/* 결선 발표의 오프닝 영상(1분 31초, 한국어 자막)입니다. 기능을 길게 보여 주는 쇼릴은 아래 링크로 둡니다 */}
        <video className="srm-video" controls preload="metadata" poster="/showreel/FlyGate_film_poster_v1.0.0.jpg" src="/showreel/FlyGate_film_v1.0.0.mp4" aria-label={t('FlyGate 소개 영상', 'FlyGate film')} />
        <div className="srm-bottom"><p>{t('1분 31초 · 탈리도마이드에서 FlyGate까지. 한국어 자막입니다.', '1 min 31 s · from thalidomide to FlyGate. Korean captions.')}</p><span><a href={`${base}.mp4`} target="_blank" rel="noopener noreferrer">{t('기능 쇼릴 전체 보기 ↗', 'Watch the full feature showreel ↗')}</a>{' · '}<a href={`${base}.html`} target="_blank" rel="noopener noreferrer">{t('인터랙티브 판 ↗', 'Interactive edition ↗')}</a></span></div>
      </div>
    </dialog>, document.body,
  )
}
