import React, { useEffect, useState } from 'react'

export function Modal({ title, onClose, children, wide }) {
  useEffect(() => {
    const esc = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', esc)
    return () => window.removeEventListener('keydown', esc)
  }, [onClose])
  return (
    <div className="modal-back" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={'modal' + (wide ? ' wide' : '')} role="dialog" aria-modal="true" aria-label={title}>
        <header><h3>{title}</h3><button className="btn ghost" onClick={onClose} aria-label="Close">Close</button></header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}

export function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span className="field-l">{label}</span>
      {children}
      {hint && <span className="field-h">{hint}</span>}
    </label>
  )
}

const STATUS = {
  official: ['Official', 'good'], 'vendor-guide-verify': ['Verify', 'warn'], 'team-assumption': ['Our assumption', 'muted'],
}
export function RuleStatus({ status }) {
  const [t, c] = STATUS[status] || [status, 'muted']
  return <span className={'rstatus ' + c}>{t}</span>
}

// A rule key from a flag or assumption, expandable to its text, source, status and date.
export function RuleCite({ rule, rulebook }) {
  const [open, setOpen] = useState(false)
  const r = rulebook?.find((x) => x.key === rule)
  if (!r) return rule ? <code className="cite">rule: {rule}</code> : null
  const value = typeof r.value === 'object' ? Object.entries(r.value).map(([k, v]) => `${k} ${Number(v).toLocaleString('en-IN')}`).join(', ') : String(r.value)
  return (
    <span className="cite-wrap">
      <button type="button" className="cite" onClick={() => setOpen(!open)} aria-expanded={open}>
        rule: {rule} <RuleStatus status={r.status} />
      </button>
      {open && (
        <span className="cite-card">
          <b>{value}{r.unit && r.unit !== 'text' ? ` ${r.unit}` : ''}</b>
          <span>Source: {r.source}</span>
          <span>Checked: {r.as_of} · {r.scope === 'national' ? 'national rule' : `${r.scope} rule`}</span>
          {r.note && <span>{r.note}</span>}
        </span>
      )}
    </span>
  )
}

export function Badge({ kind, children }) {
  return <span className={'badge-s ' + kind}>{children}</span>
}

export function Empty({ title, children, action }) {
  return (
    <div className="empty">
      <b>{title}</b>
      <p>{children}</p>
      {action}
    </div>
  )
}

export function Toasts({ items, onDismiss }) {
  return (
    <div className="toasts" aria-live="polite">
      {items.map((t) => (
        <div key={t.id} className={'toast ' + t.kind}>
          <span>{t.text}</span>
          <button onClick={() => onDismiss(t.id)} aria-label="Dismiss">×</button>
        </div>
      ))}
    </div>
  )
}

export const inrFmt = (n) => (n == null ? '—' : 'Rs ' + Math.round(n).toLocaleString('en-IN'))
