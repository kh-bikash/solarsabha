import React, { useState } from 'react'
import { api } from '../api.js'

const STATUS = {
  DONE: { c: '#2f8a3e', t: 'Done' }, ACTIVE: { c: '#c98a00', t: 'In progress' },
  OVERDUE: { c: '#c63a2b', t: 'Late' }, WAITING: { c: '#b9ad96', t: 'Waiting' },
}
const addDays = (iso, n) => { const d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10) }
const nice = (iso) => new Date(iso + 'T00:00:00Z').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })

// One track, stages laid end to end by their planned windows. Late days extend the active stage in red.
export default function Timeline({ r, project, session, canEdit, onSaved, notify }) {
  const clock = r.clock
  const today = addDays(clock.started_on, clock.today_day)
  const [when, setWhen] = useState(today)
  let cursor = 0
  const segs = r.timeline.map((s) => {
    const start = s.start_day ?? cursor
    const len = s.done_day != null ? s.done_day - start : s.max_days
    cursor = start + len + (s.overdue_by || 0)
    return { ...s, start, len }
  })
  const span = Math.max(cursor, clock.today_day + 5)
  const pct = (d) => `${(d / span) * 100}%`
  const n = r.next_action
  const events = project.events || []

  const save = async (next, msg) => {
    try { onSaved(await api.put(session, 'events', { events: next })); notify('ok', msg) } catch (e) { notify('error', e.message) }
  }
  const markDone = () => n.stage && save([...events, { stage: n.stage, done_on: when }], `${n.label} recorded as done on ${nice(when)}.`)
  const undo = () => save(events.slice(0, -1), 'Removed the last recorded step.')
  const reset = async () => { try { onSaved(await api.resetClock(session)); notify('ok', 'Back to today’s date.') } catch (e) { notify('error', e.message) } }

  return (
    <div className="folder-body">
      <p className="lede">
        {n.status === 'OVERDUE'
          ? <><b>{n.label}</b> is <b className="bad">{n.overdue_by} days late</b>. The Chaser drafted {n.chase_level === 2 ? 'an escalation to the grievance cell' : 'a polite reminder'}. It waits on your desk.</>
          : n.stage ? <>Next up: <b>{n.label}</b>. The Chaser sleeps with an alarm set, and wakes when it is due or when a reply arrives.</>
          : <>Every stage is done.</>}
      </p>
      {project.reply_reading && <p className="agent-note"><span className="who">Chaser (AI) read the DISCOM’s reply</span>{project.reply_reading.summary}</p>}
      {project.review?.review?.next_step && <p className={'agent-note' + (r.review_stale ? ' stale' : '')}><span className="who">Chaser (AI){r.review_stale ? ' · out of date' : ''}</span>{project.review.review.next_step}</p>}
      <div className="track">
        {segs.map((s) => (
          <React.Fragment key={s.key}>
            <div className="seg-bar" style={{ left: pct(s.start), width: pct(s.len), '--c': STATUS[s.status].c }} title={`${s.label}: ${STATUS[s.status].t}`} />
            {s.overdue_by > 0 && <div className="seg-bar late" style={{ left: pct(s.start + s.len), width: pct(s.overdue_by) }} title={`${s.overdue_by} days late`} />}
          </React.Fragment>
        ))}
        <div className="today" style={{ left: pct(clock.today_day) }}><span>Today · day {clock.today_day}</span></div>
      </div>
      <div className="track-axis"><span>{nice(clock.started_on)}</span><span>day {span}</span></div>

      <ol className="stages">
        {segs.map((s, i) => {
          const ev = events.find((e) => e.stage === s.key)
          return (
            <li key={s.key} style={{ '--c': STATUS[s.status].c }}>
              <span className="num">{i + 1}</span>
              <div><b>{s.label}</b>
                <span>{ev ? `Done on ${nice(ev.done_on)}` : `${STATUS[s.status].t}${s.overdue_by ? `, ${s.overdue_by} days` : ''}`} · usually {s.min_days} to {s.max_days} days</span></div>
            </li>
          )
        })}
      </ol>

      {canEdit && (
        <div className="progress-bar">
          {n.stage && (
            <>
              <span>Record progress: <b>{n.label}</b> done on</span>
              <input type="date" value={when} min={clock.started_on} max={today} onChange={(e) => setWhen(e.target.value)} />
              <button className="btn primary" onClick={markDone}>Mark done</button>
            </>
          )}
          {events.length > 0 && <button className="btn ghost" onClick={undo}>Undo last step</button>}
        </div>
      )}
      <p className="fine">
        {clock.simulated
          ? <><span className="tape small">Simulated clock</span> The time machine has moved this project {clock.sim_offset_days} days ahead.
            {canEdit && <> <button className="linkish" onClick={reset}>Back to today</button>.</>} </>
          : <>Real dates, counted from the project start on {nice(clock.started_on)}. </>}
        Stage windows come from vendor guides, not the government.
      </p>
    </div>
  )
}
