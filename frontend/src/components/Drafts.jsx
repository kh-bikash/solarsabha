import React, { useState } from 'react'
import { api } from '../api.js'
import { Empty } from './ui.jsx'

const KIND = {
  agm_notice: 'Meeting notice', agm_resolution: 'Resolution', counter_offer: 'Counter-offer', proof_request: 'Proof request',
  details_request: 'Details request', rfq: 'Request for quotation', discom_reminder: 'DISCOM reminder', discom_escalation: 'Escalation',
}
const when = (iso) => new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export default function Drafts({ drafts, session, canEdit, canApprove, canPolish, onSaved, notify, actor }) {
  const [polishing, setPolishing] = useState(null)
  const [open, setOpen] = useState(null)
  const [edit, setEdit] = useState(null)
  if (!drafts.length) {
    return <div className="folder-body"><Empty title="Your desk is clear">Letters appear here once there is a plan, quotations, or a late DISCOM stage.</Empty></div>
  }
  const save = async () => {
    try { onSaved(await api.editDraft(session, edit.id, edit.subject, edit.body)); setEdit(null); notify('ok', 'Draft saved. It needs approval again.') }
    catch (e) { notify('error', e.message) }
  }
  const polish = async (d) => {
    setPolishing(d.id)
    try { onSaved(await api.polishDraft(session, d.id)); notify('ok', 'Reworded by the Secretary. Facts unchanged. It needs approval.') }
    catch (e) { notify('error', e.message) } finally { setPolishing(null) }
  }
  const approve = async (d) => {
    try { onSaved(await api.approveDraft(session, d.id)); notify('ok', `Approved by ${actor}. Nothing has been sent.`) } catch (e) { notify('error', e.message) }
  }
  return (
    <div className="folder-body">
      <div className="papers">
        {drafts.map((d) => {
          const editing = edit?.id === d.id
          return (
            <article key={d.id} className={'paper' + (d.status === 'APPROVED' ? ' approved' : '') + (open === d.id || editing ? ' open' : '')}>
              <span className="kind">{KIND[d.kind] || d.kind}</span>
              {editing ? <input className="paper-subject" value={edit.subject} onChange={(e) => setEdit({ ...edit, subject: e.target.value })} /> : <h4>{d.subject}</h4>}
              <span className="to">To: {d.to}</span>
              {editing && <textarea className="paper-body" rows={14} value={edit.body} onChange={(e) => setEdit({ ...edit, body: e.target.value })} />}
              {!editing && open === d.id && <pre>{d.body}</pre>}
              <div className="paper-meta">
                {d.status === 'APPROVED' && <span className="ok">Approved by {d.approved_by}, {when(d.approved_at)}</span>}
                {d.stale_approval && <span className="warn">Approval by {d.stale_approval.by} was withdrawn because the letter changed.</span>}
                {d.edited_by && <span>Edited by {d.edited_by}, {when(d.edited_at)}</span>}
                {d.facts_changed && <span className="warn">The figures behind this letter have changed since it was edited. Check it.</span>}
              </div>
              <div className="paper-actions">
                {editing ? (
                  <><button className="btn primary" onClick={save}>Save</button><button className="btn ghost" onClick={() => setEdit(null)}>Cancel</button></>
                ) : (
                  <>
                    <button className="btn ghost" onClick={() => setOpen(open === d.id ? null : d.id)}>{open === d.id ? 'Fold' : 'Read'}</button>
                    {canEdit && <button className="btn ghost" onClick={() => { setEdit({ id: d.id, subject: d.subject, body: d.body }); setOpen(null) }}>Edit</button>}
                    {canPolish && <button className="btn ghost" disabled={polishing === d.id} title="AI rewording; rejected if any number, date or reference changes" onClick={() => polish(d)}>{polishing === d.id ? 'Polishing…' : 'Polish (AI)'}</button>}
                    <button className="btn ghost" onClick={() => api.downloadDraft(session, d.id).catch((e) => notify('error', e.message))}>Word</button>
                    {canApprove && actor && d.status === 'DRAFT' && <button className="btn" title={`Approve as ${actor}`} onClick={() => approve(d)}>Approve</button>}
                  </>
                )}
              </div>
              <span className="stamp big">{d.status === 'APPROVED' ? 'Approved' : 'Draft'}</span>
            </article>
          )
        })}
      </div>
      <p className="fine">Approving records who agreed to a letter. This build has no send, sign, pay or file function, by design: download it in Word and send it yourself.</p>
    </div>
  )
}
