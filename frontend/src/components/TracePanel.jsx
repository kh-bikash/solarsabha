import React from 'react'
import { AGENT_COLOR } from '../office/story.js'

// The logbook: every event the office has played, in plain words. Same events that drive the scene.
export default function TracePanel({ played, current, mode }) {
  const rows = current ? [...played, current] : played
  return (
    <div className="folder-body">
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
    </div>
  )
}
