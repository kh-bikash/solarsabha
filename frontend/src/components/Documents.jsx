import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { Badge, Empty } from './ui.jsx'

const STATUS = { READ: ['Read', 'good'], NEEDS_REVIEW: ['Check this', 'warn'], NEEDS_ENTRY: ['Type it in', 'bad'] }
const num = (v) => (v === '' || v == null ? null : Number(v))
const blankQuote = { vendor: '', capacity_kw: '', total_price_inr: '', advance_pct: '', warranty_panel_years: '', service_years: '', payment_terms_text: '', offer_text: '' }

export default function Documents({ project, session, canEdit, onSaved, notify }) {
  const [kind, setKind] = useState('bill')
  const [uploading, setUploading] = useState(0)
  const [drag, setDrag] = useState(false)
  const input = useRef(null)
  const docs = project.documents || []
  const byId = Object.fromEntries(docs.map((d) => [d.id, d]))

  const upload = async (files) => {
    let latest = null
    for (const f of [...files]) {
      setUploading((n) => n + 1)
      try {
        latest = await api.upload(session, kind, f)
        const entry = latest.documents[latest.documents.length - 1]
        notify(entry.status === 'READ' ? 'ok' : 'warn', `${f.name}: ${STATUS[entry.status][0].toLowerCase()}. ${entry.notes || ''}`)
      } catch (e) { notify('error', `${f.name}: ${e.message}`) } finally { setUploading((n) => n - 1) }
    }
    if (latest) onSaved(latest)
  }
  const remove = async (d) => {
    if (!window.confirm(`Delete the original file ${d.filename}? The numbers already read from it stay.`)) return
    try { onSaved(await api.deleteDocument(session, d.id)) } catch (e) { notify('error', e.message) }
  }

  return (
    <div className="folder-body docs">
      <div
        className={'drop' + (drag ? ' on' : '') + (canEdit ? '' : ' off')}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); canEdit && upload(e.dataTransfer.files) }}>
        <div className="seg" role="radiogroup" aria-label="What are you uploading?">
          <button type="button" className={kind === 'bill' ? 'on' : ''} onClick={() => setKind('bill')}>Electricity bills</button>
          <button type="button" className={kind === 'quote' ? 'on' : ''} onClick={() => setKind('quote')}>Vendor quotations</button>
        </div>
        <p>Drop {kind === 'bill' ? 'common-area bills' : 'quotations'} here (PDF, or a photo up to 6 MB), or</p>
        <button className="btn dark" disabled={!canEdit || uploading > 0} onClick={() => input.current?.click()}>
          {uploading ? `Reading ${uploading} file(s)…` : 'Choose files'}
        </button>
        <input ref={input} type="file" multiple accept="application/pdf,image/png,image/jpeg" hidden onChange={(e) => { upload(e.target.files); e.target.value = '' }} />
        <p className="fine">{project.result.reader_mode === 'live'
          ? `Read by the AI Reader (${project.result.ai_provider === 'bedrock' ? 'Amazon Bedrock' : 'Gemini'}), with the plain-rule reader as a fallback. Check every value before you rely on it.`
          : 'Read with plain rules (no AI): digital PDFs work; photos and scans need the AI Reader or typing in.'}</p>
      </div>

      {docs.length > 0 && (
        <table className="ledger doclist">
          <thead><tr><th>File</th><th>Type</th><th>Status</th><th>Notes</th><th /></tr></thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.filename}</td>
                <td>{d.kind === 'bill' ? 'Bill' : 'Quotation'}</td>
                <td><Badge kind={STATUS[d.status][1]}>{STATUS[d.status][0]}</Badge></td>
                <td className="small">{d.notes || '—'}</td>
                <td className="row-actions">
                  <button className="btn ghost tiny" onClick={() => api.downloadDocument(session, d.id).catch((e) => notify('error', e.message))}>Original</button>
                  {canEdit && <button className="btn ghost tiny" onClick={() => remove(d)}>Delete</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <BillsEditor project={project} session={session} canEdit={canEdit} byId={byId} onSaved={onSaved} notify={notify} />
      <QuotesEditor project={project} session={session} canEdit={canEdit} byId={byId} onSaved={onSaved} notify={notify} />
      <FlatsEditor project={project} session={session} canEdit={canEdit} onSaved={onSaved} notify={notify} />
    </div>
  )
}

function useDraft(source) {
  const [rows, setRows] = useState(source)
  const [dirty, setDirty] = useState(false)
  useEffect(() => { setRows(source); setDirty(false) }, [JSON.stringify(source)])
  return [rows, (r) => { setRows(r); setDirty(true) }, dirty]
}

function BillsEditor({ project, session, canEdit, byId, onSaved, notify }) {
  const [rows, setRows, dirty] = useDraft(project.inputs.bills)
  const upd = (i, k, v) => setRows(rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)))
  const save = async () => {
    try {
      onSaved(await api.put(session, 'bills', { bills: rows.map((r) => ({ month: r.month, units_kwh: num(r.units_kwh), amount_inr: num(r.amount_inr),
        unclear: !!r.unclear, verified: !!r.verified, source_doc: r.source_doc || null })) }))
      notify('ok', 'Bills saved. The plan has been recalculated.')
    } catch (e) { notify('error', e.message) }
  }
  const avg = project.result.bill_average_rate
  return (
    <section className="editor">
      <header>
        <h4>Common-area bills <span className="muted">{rows.length} month(s)</span></h4>
        {avg && <span className="fine">Your bills average Rs {avg} per unit, including fixed charges and taxes.</span>}
      </header>
      {rows.length === 0 ? <Empty title="No bills yet">Upload the last 12 common-area bills above, or add the months by hand.</Empty> : (
        <table className="ledger edit">
          <thead><tr><th>Month</th><th>Units (kWh)</th><th>Amount (Rs)</th><th>Unclear</th><th>Checked</th><th>From</th><th /></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className={r.unclear && !r.verified ? 'flag' : ''}>
                <td><input type="month" value={r.month} disabled={!canEdit} onChange={(e) => upd(i, 'month', e.target.value)} /></td>
                <td><input type="number" min={0} value={r.units_kwh ?? ''} disabled={!canEdit} onChange={(e) => upd(i, 'units_kwh', e.target.value)} /></td>
                <td><input type="number" min={0} value={r.amount_inr ?? ''} disabled={!canEdit} onChange={(e) => upd(i, 'amount_inr', e.target.value)} /></td>
                <td><input type="checkbox" checked={!!r.unclear} disabled={!canEdit} onChange={(e) => upd(i, 'unclear', e.target.checked)} aria-label="Unclear" /></td>
                <td><input type="checkbox" checked={!!r.verified} disabled={!canEdit} onChange={(e) => upd(i, 'verified', e.target.checked)} aria-label="Checked by a person" /></td>
                <td className="small muted">{r.source_doc ? byId[r.source_doc]?.filename || 'file deleted' : 'typed in'}</td>
                <td>{canEdit && <button className="btn ghost tiny" onClick={() => setRows(rows.filter((_, j) => j !== i))}>Remove</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {canEdit && (
        <div className="editor-actions">
          <button className="btn ghost" onClick={() => setRows([...rows, { month: '', units_kwh: '', amount_inr: '', unclear: false, verified: true }])}>Add a month</button>
          <button className="btn primary" disabled={!dirty} onClick={save}>Save bills</button>
        </div>
      )}
    </section>
  )
}

function QuotesEditor({ project, session, canEdit, byId, onSaved, notify }) {
  const [rows, setRows, dirty] = useDraft(project.inputs.quotes)
  const upd = (i, k, v) => setRows(rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)))
  const save = async () => {
    try {
      onSaved(await api.put(session, 'quotes', { quotes: rows.map((q) => ({
        vendor: q.vendor, capacity_kw: num(q.capacity_kw), total_price_inr: num(q.total_price_inr), advance_pct: num(q.advance_pct),
        warranty_panel_years: num(q.warranty_panel_years), service_years: num(q.service_years),
        payment_terms_text: q.payment_terms_text || '', offer_text: q.offer_text || '', raw_text: q.raw_text || '', source_doc: q.source_doc || null })) }))
      notify('ok', 'Quotations saved. The audit has been re-run.')
    } catch (e) { notify('error', e.message) }
  }
  const F = [['vendor', 'Vendor', 'text'], ['capacity_kw', 'Size (kW)', 'number'], ['total_price_inr', 'Total price (Rs)', 'number'],
    ['advance_pct', 'Advance (%)', 'number'], ['warranty_panel_years', 'Panel warranty (yrs)', 'number'], ['service_years', 'Free service (yrs)', 'number']]
  return (
    <section className="editor">
      <header><h4>Vendor quotations <span className="muted">{rows.length}</span></h4>
        <span className="fine">Empty means the quotation does not say. The Auditor flags it rather than guessing.</span></header>
      {rows.length === 0 && <Empty title="No quotations yet">Upload quotations above, or add one by hand.</Empty>}
      <div className="qedit">
        {rows.map((q, i) => (
          <div key={i} className="qedit-card">
            <div className="qedit-grid">
              {F.map(([k, l, t]) => (
                <label key={k} className="field"><span className="field-l">{l}</span>
                  <input type={t} value={q[k] ?? ''} disabled={!canEdit} onChange={(e) => upd(i, k, e.target.value)} /></label>
              ))}
            </div>
            <label className="field"><span className="field-l">Payment terms</span>
              <input value={q.payment_terms_text || ''} disabled={!canEdit} onChange={(e) => upd(i, 'payment_terms_text', e.target.value)} /></label>
            <label className="field"><span className="field-l">Offer conditions</span>
              <input value={q.offer_text || ''} disabled={!canEdit} onChange={(e) => upd(i, 'offer_text', e.target.value)} /></label>
            <div className="qedit-foot">
              <span className="small muted">{q.source_doc ? `From ${byId[q.source_doc]?.filename || 'a deleted file'}` : 'Typed in'}</span>
              {canEdit && <button className="btn ghost tiny" onClick={() => setRows(rows.filter((_, j) => j !== i))}>Remove</button>}
            </div>
          </div>
        ))}
      </div>
      {canEdit && (
        <div className="editor-actions">
          <button className="btn ghost" disabled={rows.length >= 12} onClick={() => setRows([...rows, { ...blankQuote }])}>Add a quotation</button>
          <button className="btn primary" disabled={!dirty} onClick={save}>Save quotations</button>
        </div>
      )}
    </section>
  )
}

function FlatsEditor({ project, session, canEdit, onSaved, notify }) {
  const toText = (m) => Object.entries(m || {}).map(([k, v]) => `${k}, ${v}`).join('\n')
  const [text, setText] = useState(toText(project.inputs.flat_areas_sqft))
  useEffect(() => setText(toText(project.inputs.flat_areas_sqft)), [JSON.stringify(project.inputs.flat_areas_sqft)])
  const save = async () => {
    const areas = {}
    for (const line of text.split('\n').map((l) => l.trim()).filter(Boolean)) {
      const m = /^(.+?)[,\t ]+(\d+(?:\.\d+)?)$/.exec(line)
      if (!m) return notify('error', `Could not read "${line}". Use: flat, area`)
      areas[m[1].trim()] = Number(m[2])
    }
    try { onSaved(await api.put(session, 'flats', { flat_areas_sqft: areas })); notify('ok', 'Flat areas saved.') } catch (e) { notify('error', e.message) }
  }
  const n = text.split('\n').filter((l) => l.trim()).length
  return (
    <section className="editor">
      <header><h4>Flat areas <span className="muted">{n} of {project.inputs.society.flats} flats</span></h4>
        <span className="fine">Needed for the by-area cost split. One flat per line: <code>A-101, 950</code> (sq ft). You can paste from a spreadsheet.</span></header>
      <textarea rows={6} value={text} disabled={!canEdit} onChange={(e) => setText(e.target.value)} placeholder={'A-101, 950\nA-102, 950'} />
      {canEdit && <div className="editor-actions"><button className="btn primary" onClick={save}>Save flat areas</button></div>}
    </section>
  )
}
