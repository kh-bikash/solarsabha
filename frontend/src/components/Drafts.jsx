import React, { useState } from 'react'

const KIND = {
  agm_notice: 'Meeting notice', agm_resolution: 'Resolution', counter_offer: 'Counter-offer', proof_request: 'Proof request',
  discom_reminder: 'DISCOM reminder', discom_escalation: 'Escalation',
}

export default function Drafts({ drafts, onApprove }) {
  const [open, setOpen] = useState(null)
  return (
    <div className="folder-body">
      <div className="papers">
        {drafts.map((d) => (
          <article key={d.id} className={'paper' + (d.status === 'APPROVED' ? ' approved' : '') + (open === d.id ? ' open' : '')}>
            <span className="kind">{KIND[d.kind] || d.kind}</span>
            <h4>{d.subject}</h4>
            <span className="to">To: {d.to}</span>
            {open === d.id && <pre>{d.body}</pre>}
            <div className="paper-actions">
              <button className="btn ghost" onClick={() => setOpen(open === d.id ? null : d.id)}>{open === d.id ? 'Fold' : 'Read'}</button>
              {d.status === 'DRAFT' && <button className="btn" onClick={() => onApprove(d.id)}>Approve</button>}
            </div>
            <span className="stamp big">{d.status === 'APPROVED' ? 'Approved' : 'Draft'}</span>
          </article>
        ))}
      </div>
      <p className="fine">Approving marks the draft. This build has no send, sign, pay or file function, by design.</p>
    </div>
  )
}
