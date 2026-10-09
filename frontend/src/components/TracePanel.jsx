import React, { useState } from 'react'
import { AGENT_COLOR } from '../office/story.js'

const when = (iso) => new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

// The logbook: what the office did (agent trace, plain words) and what people did (activity log).
export default function TracePanel({ played, current, mode, audit }) {
  const [tab, setTab] = useState('agents')
  const rows = current ? [...played, current] : played
  return (
    <div className="folder-body">
      <div className="seg" role="tablist">
        <button role="tab" aria-selected={tab === 'agents'} className={tab === 'agents' ? 'on' : ''} onClick={() => setTab('agents')}>What the office did</button>
        <button role="tab" aria-selected={tab === 'people'} className={tab === 'people' ? 'on' : ''} onClick={() => setTab('people')}>What people did</button>
      </div>
      {tab === 'agents' ? (
        <>
          <ol className="log">
            {rows.length === 0 && <li className="muted">Nothing has happened yet.</li>}
            {rows.map((e, i) => (
              <li key={i} className={e === current ? 'live' : ''} style={{ '--c': AGENT_COLOR[e.agent] || '#4a443d' }}>
                <span className="n">{String(i + 1).padStart(2, '0')}</span>
                <span className="who">{e.agent}</span>
                {e.tool ? <code>{e.tool}()</code> : <span className="note">note</span>}
                <span className="what">{e.text}</span>
                {e.tool && <span className="kind">plain code</span>}
              </li>
            ))}
          </ol>
          <p className="fine">{mode === 'offline'
            ? 'This run uses the offline pipeline, so every step here is ordinary code. In live mode the Reader, Auditor and Chaser run on a Bedrock model, and their tool calls appear here the same way.'
            : 'Live run: notes come from the agents; numbers still come from the plain-code tools.'}</p>
        </>
      ) : (
        <ol className="log people">
          {[...(audit || [])].reverse().map((a, i) => (
            <li key={i}>
              <span className="when">{when(a.at)}</span>
              <span className="who-p">{a.actor}</span>
              <span className="what">{a.action}{a.detail ? `: ${a.detail}` : ''}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
