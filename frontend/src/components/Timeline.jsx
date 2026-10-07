import React from 'react'

const STATUS = {
  DONE: { c: '#2f8a3e', t: 'Done' }, ACTIVE: { c: '#c98a00', t: 'In progress' },
  OVERDUE: { c: '#c63a2b', t: 'Late' }, WAITING: { c: '#b9ad96', t: 'Waiting' },
}

// One track, stages laid end to end by their planned windows. Late days extend the active stage in red.
export default function Timeline({ r }) {
  let cursor = 0
  const segs = r.timeline.map((s) => {
    const start = s.start_day ?? cursor
    const len = s.done_day != null ? s.done_day - start : s.max_days
    cursor = start + len + (s.overdue_by || 0)
    return { ...s, start, len }
  })
  const span = Math.max(cursor, r.today_day + 5)
  const pct = (d) => `${(d / span) * 100}%`
  const n = r.next_action
  return (
    <div className="folder-body">
      <p className="lede">
        {n.status === 'OVERDUE'
          ? <><b>{n.label}</b> is <b className="bad">{n.overdue_by} days late</b>. The Chaser drafted {n.chase_level === 2 ? 'an escalation to the grievance cell' : 'a polite reminder'}. It waits on your desk.</>
          : <>Next up: <b>{n.label}</b>. The Chaser is asleep with an alarm set, and wakes when it is due or when a reply arrives.</>}
      </p>
      <div className="track">
        {segs.map((s) => (
          <React.Fragment key={s.key}>
            <div className="seg-bar" style={{ left: pct(s.start), width: pct(s.len), '--c': STATUS[s.status].c }} title={`${s.label}: ${STATUS[s.status].t}`} />
            {s.overdue_by > 0 && <div className="seg-bar late" style={{ left: pct(s.start + s.len), width: pct(s.overdue_by) }} title={`${s.overdue_by} days late`} />}
          </React.Fragment>
        ))}
        <div className="today" style={{ left: pct(r.today_day) }}><span>Today · day {r.today_day}</span></div>
      </div>
      <div className="track-axis"><span>day 0</span><span>day {span}</span></div>
      <ol className="stages">
        {segs.map((s, i) => (
          <li key={s.key} style={{ '--c': STATUS[s.status].c }}>
            <span className="num">{i + 1}</span>
            <div><b>{s.label}</b><span>{STATUS[s.status].t}{s.overdue_by ? `, ${s.overdue_by} days` : ''} · usually {s.min_days} to {s.max_days} days</span></div>
          </li>
        ))}
      </ol>
      <p className="fine"><span className="tape small">Simulated clock</span> Stage windows come from vendor guides, not the government. The time machine moves a fake clock; the wake-up code path is the real one.</p>
    </div>
  )
}
