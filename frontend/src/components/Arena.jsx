import React, { useEffect, useMemo, useState } from 'react'
import { inr, lakh } from '../office/story.js'

// The negotiation room, replayed as three chat threads. Vendors are SIMULATED personas with hidden floors;
// a RED vendor gets a proof request, never a haggle. Counters are drafts for the committee to approve.
const VERDICT = { GREEN: '#2f8a3e', AMBER: '#c98a00', RED: '#c63a2b' }

export default function Arena({ negotiations, audits }) {
  const steps = useMemo(() => {
    const s = []
    const longest = Math.max(...negotiations.map((n) => n.rounds.length))
    for (let i = 0; i < longest; i++) negotiations.forEach((n, vi) => { if (n.rounds[i]) s.push([vi, i]) })
    return s
  }, [negotiations])
  const [shown, setShown] = useState(0)
  const [play, setPlay] = useState(false)
  useEffect(() => {
    if (!play) return
    if (shown >= steps.length) { setPlay(false); return }
    const t = setTimeout(() => setShown(shown + 1), 650)
    return () => clearTimeout(t)
  }, [play, shown, steps.length])
  const visible = new Set(steps.slice(0, shown).map(([v, i]) => v + ':' + i))

  return (
    <div className="folder-body">
      <div className="room-top">
        <button className="btn dark" onClick={() => { setShown(0); setPlay(true) }}>{shown ? 'Replay the room' : 'Play the room'}</button>
        <p className="fine">The committee sets the target, code works out a fair counter, the agent drafts it, and a person approves it. The vendors here are simulated, so this is a replay of the logic, not a claim of savings.</p>
      </div>
      <div className="threads">
        {negotiations.map((n, vi) => {
          const a = audits[vi]
          return (
            <section key={n.vendor} className="thread" style={{ '--v': VERDICT[a.verdict] }}>
              <header><b>{n.vendor}</b><span className="stamp sm">{a.verdict}</span></header>
              <p className="mono start">{n.skipped ? 'Not negotiated: unverified vendor' : `Quoted ${lakh(n.start_price)}`}</p>
              <div className="msgs">
                {n.rounds.map((rd, i) => visible.has(vi + ':' + i) && (
                  <div key={i} className={'msg ' + rd.from}>
                    <span className="who">{rd.from === 'committee' ? 'Committee (draft)' : 'Vendor (simulated)'}</span>
                    {rd.message}
                  </div>
                ))}
              </div>
              {!n.skipped && shown >= steps.length && (
                <p className="result">Ends at <b>{inr(n.final_price)}</b>, {n.final_advance_pct}% advance.</p>
              )}
            </section>
          )
        })}
      </div>
    </div>
  )
}
