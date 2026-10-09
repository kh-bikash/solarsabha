import React, { useCallback, useEffect, useRef, useState } from 'react'
import { MODE, api, SAMPLE_DISCOM_REPLY } from './api.js'
import { fromHash, getActor, rememberProject, forgetProject, setActor, setHash } from './session.js'
import Office from './office/Office.jsx'
import { describe, describeAgentRun, boardItems, AGENT_COLOR } from './office/story.js'
import { PixelIcon } from './pixel/Sprite.jsx'
import { ICONS, iconPal } from './pixel/sprites.js'
import Welcome from './components/Welcome.jsx'
import PlanCard from './components/PlanCard.jsx'
import Documents from './components/Documents.jsx'
import QuoteTable from './components/QuoteTable.jsx'
import Fairness from './components/Fairness.jsx'
import Timeline from './components/Timeline.jsx'
import Arena from './components/Arena.jsx'
import Drafts from './components/Drafts.jsx'
import TracePanel from './components/TracePanel.jsx'
import Settings from './components/Settings.jsx'
import { Modal, Toasts } from './components/ui.jsx'

const sleep = (ms) => new Promise((res) => setTimeout(res, ms))
const sig = (e) => `${e.agent}|${e.tool}|${e.output}`
const shortLakh = (n) => '₹' + (n / 1e5).toFixed(1).replace(/\.0$/, '') + 'L'
const FOLDERS = [['plan', 'The plan'], ['docs', 'Documents'], ['quotes', 'Quote audit'], ['pays', 'Who pays'], ['timeline', 'Timeline'],
  ['room', 'Negotiation room'], ['desk', 'Your desk'], ['log', 'Logbook'], ['settings', 'Settings']]

export default function App() {
  const [session, setSession] = useState(null)
  const [doc, setDoc] = useState(null)
  const [toasts, setToasts] = useState([])
  const [loading, setLoading] = useState(true)

  const notify = useCallback((kind, text) => {
    const id = Math.random().toString(36).slice(2)
    setToasts((t) => [...t.slice(-3), { id, kind, text }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), kind === 'error' ? 8000 : 4500)
  }, [])

  const open = useCallback(async (s, d) => {
    try {
      const data = d || await api.getProject(s)
      const names = data.members.map((m) => m.name)
      const remembered = getActor(data.id)
      const actor = names.includes(remembered) ? remembered : data.members.length === 1 || data.sample ? names[0] : null
      const full = { id: data.id, key: s.key, name: data.inputs.society.name, actor }
      if (MODE === 'LIVE') { rememberProject(full); setHash(full) }
      setSession(full); setDoc(data)
    } catch (e) {
      notify('error', e.status === 404 ? 'That project no longer exists (it may have been deleted or expired).' : e.message)
      if (e.status === 404 || e.status === 401) forgetProject(s.id)
      setHash(null)
    } finally { setLoading(false) }
  }, [notify])

  useEffect(() => {
    const shared = fromHash()
    if (shared) open(shared)
    else if (MODE === 'MOCK') open({ id: 'demo', key: 'demo' })
    else setLoading(false)
  }, [open])

  const leave = () => { setSession(null); setDoc(null); setHash(null) }
  const chooseActor = (name) => { setActor(session.id, name); setSession({ ...session, actor: name }) }

  return (
    <>
      {loading ? <div className="wrap loading">Opening the office…</div>
        : session && doc ? <Workspace key={session.id} session={session} initial={doc} onLeave={leave} onActor={chooseActor} notify={notify} />
        : <div className="wrap"><AppBar /><Welcome onOpen={open} notify={notify} /></div>}
      <Toasts items={toasts} onDismiss={(id) => setToasts((t) => t.filter((x) => x.id !== id))} />
    </>
  )
}

function AppBar({ children, meta }) {
  return (
    <header className="appbar">
      <div className="brand">
        <svg className="mark" viewBox="0 0 8 8" shapeRendering="crispEdges" aria-hidden="true">
          <rect x="2" y="1" width="4" height="4" fill="#ef6a1a" /><rect x="1" y="2" width="6" height="2" fill="#ef6a1a" /><rect x="0" y="6" width="8" height="2" fill="#2f6db5" />
        </svg>
        <b>SolarSabha</b>
        {meta && <span className="meta">{meta}</span>}
      </div>
      <div className="appbar-right">{children || <span className="chip trackchip"><i />Track 03 · Waste and Energy</span>}</div>
    </header>
  )
}

function Workspace({ session, initial, onLeave, onActor, notify }) {
  const [project, setProject] = useState(initial)
  const [played, setPlayed] = useState([])
  const [queue, setQueue] = useState([])
  const [current, setCurrent] = useState(null)
  const [phase, setPhase] = useState('day')
  const [dayShown, setDayShown] = useState(initial.result.clock.today_day)
  const [flights, setFlights] = useState([])
  const [envelope, setEnvelope] = useState(false)
  const [busy, setBusy] = useState(false)
  const [folder, setFolder] = useState(initial.result.needs?.includes('bills') ? 'docs' : 'plan')
  const [speed, setSpeed] = useState(1)
  const [replyOpen, setReplyOpen] = useState(false)
  const [replyText, setReplyText] = useState('')
  const keyRef = useRef(0)
  const filesRef = useRef(null)
  const projectRef = useRef(initial)
  const withKey = (e) => ({ ...e, key: ++keyRef.current })

  const replayAll = useCallback((p) => {
    projectRef.current = p
    setProject(p); setPlayed([]); setCurrent(null); setDayShown(p.result.clock.today_day)
    setQueue(describe(p.result.trace, p.result).map(withKey))
  }, [])
  useEffect(() => { replayAll(initial) }, [replayAll, initial])

  // Replays only what is new. After a time jump the Chaser's wake-up check always replays.
  const continueWith = (next, wake = false) => {
    const prev = projectRef.current
    projectRef.current = next
    const oldSigs = new Set(prev.result.trace.map(sig))
    const desc = describe(next.result.trace, next.result).map(withKey)
    const isNew = next.result.trace.map((e) => !oldSigs.has(sig(e)) || (wake && e.tool === 'build_timeline'))
    setProject(next); setCurrent(null); setDayShown(next.result.clock.today_day)
    setPlayed(desc.filter((_, i) => !isNew[i]))
    setQueue(desc.filter((_, i) => isNew[i]))
  }
  const onSaved = (next) => continueWith(next)

  // playback: one event at a time
  useEffect(() => {
    if (current || !queue.length || phase !== 'day') return
    setCurrent(queue[0]); setQueue(queue.slice(1))
  }, [queue, current, phase])
  useEffect(() => {
    if (!current) return
    const t = setTimeout(() => {
      setPlayed((p) => [...p, current])
      if (current.flight) spawnFlights(current.flight, current.flight === 'Secretary' ? 3 : 1)
      setCurrent(null)
    }, Math.min(3400, 1200 + current.text.length * 20) / speed)
    return () => clearTimeout(t)
  }, [current, speed])

  const spawnFlights = (from, n) => {
    for (let i = 0; i < n; i++) {
      const id = Math.random().toString(36).slice(2)
      setTimeout(() => setFlights((f) => [...f, { id, from }]), i * 200)
      setTimeout(() => setFlights((f) => f.filter((x) => x.id !== id)), i * 200 + 1200)
    }
  }

  const act = async (fn) => {
    if (busy) return
    setBusy(true)
    try { await fn() } catch (e) { notify('error', e.message); setPhase('day') } finally { setBusy(false) }
  }
  const jump = (days) => act(async () => {
    const to = Math.min(dayShown + days, MODE === 'MOCK' ? 50 : Infinity)
    setPhase('night'); setQueue([]); setCurrent(null)
    const tick = setInterval(() => setDayShown((d) => (d < to ? Math.min(to, d + Math.max(1, Math.round(days / 24))) : d)), 90)
    try {
      const [next] = await Promise.all([api.advance(session, days), sleep(2700)])
      clearInterval(tick); setDayShown(next.result.clock.today_day)
      setPhase('ring'); await sleep(1100); setPhase('day')
      continueWith(next, true)
    } finally { clearInterval(tick) }
  })
  const deliverReply = () => act(async () => {
    setReplyOpen(false); setEnvelope(true)
    try {
      const [next] = await Promise.all([api.discomReply(session, replyText || SAMPLE_DISCOM_REPLY), sleep(1500)])
      continueWith(next)
    } finally { setEnvelope(false) }
  })
  const clearReply = () => act(async () => continueWith(await api.clearReply(session)))
  const runReview = () => act(async () => {
    notify('ok', 'The Secretary is reviewing the project with the Auditor and the Chaser…')
    const next = await api.review(session)
    projectRef.current = next
    setProject(next)
    setQueue((q) => [...q, ...describeAgentRun(next.review.trace).map(withKey)])
    notify('ok', 'Review ready: see the quote cards, the Timeline and Logbook > Agents’ review.')
  })
  const pick = (f) => { setFolder(f); filesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }

  const r = project.result
  const me = project.members.find((m) => m.name === session.actor)
  const role = me?.role
  const editRole = role === 'secretary' || role === 'member'
  const canEdit = MODE === 'LIVE' && editRole
  const board = boardItems(played, r)
  const idle = !current && !queue.length
  const secretaryDrafted = played.some((e) => e.agent === 'Secretary' && /^Drafted/.test(e.text))
  const chaserDrafted = played.some((e) => e.agent === 'Chaser' && /Drafted/.test(e.text))
  const waiting = project.drafts.filter((d) => d.status === 'DRAFT')
  const chaserPending = waiting.some((d) => d.kind.startsWith('discom_')) && !chaserDrafted ? 1 : 0
  const draftsWaiting = secretaryDrafted || chaserDrafted ? waiting.length - chaserPending : 0
  const agmPinned = project.drafts.some((d) => d.kind === 'agm_notice' && d.status === 'APPROVED') ? r.recommended?.kw : 0
  const negPlayed = played.filter((e) => e.tool === 'run_simulated_negotiation').length
  const auditPlayed = played.filter((e) => e.tool === 'audit_quote').length
  const roomPrices = r.negotiations.map((neg, i) => {
    if (i >= auditPlayed) return null
    if (neg.skipped) return neg.rounds[0].kind === 'request_proof' ? 'proof?' : 'details?'
    return shortLakh(i < negPlayed ? neg.final_price : neg.start_price)
  })
  const n = r.next_action
  const chaserAsleep = n.status !== 'OVERDUE' && current?.agent !== 'Chaser' && played.length > 0
  const last = current || played[played.length - 1]
  const total = played.length + queue.length + (current ? 1 : 0)
  const live = r.reader_mode === 'live'
  const modeLabel = MODE === 'MOCK' ? 'Static demo' : live ? 'Live agents on Bedrock' : 'Offline reader · no AI model'
  const soc = project.inputs.society

  return (
    <div className="wrap">
      <AppBar meta={`${soc.name} · ${soc.flats} flats${soc.discom ? ` · ${soc.discom}` : ''}`}>
        <label className="actor">
          <span>You are</span>
          <select value={session.actor || ''} onChange={(e) => onActor(e.target.value)}>
            <option value="" disabled>Choose…</option>
            {project.members.map((m) => <option key={m.name} value={m.name}>{m.name} ({m.role})</option>)}
          </select>
        </label>
        <button className="btn ghost" onClick={onLeave}>All projects</button>
      </AppBar>
      <div className="badges">
        <span className="chip trackchip"><i />Track 03 · Waste and Energy</span>
        <span className="chip">{modeLabel}</span>
        {project.sample && <span className="tape">Sample society · fictional data</span>}
        <span className="tape">Simulated: {r.simulated_parts.join(', ')}</span>
        {!session.actor && <span className="notice warn inline">Choose who you are (top right) to make changes.</span>}
        {session.actor && role === 'viewer' && <span className="notice inline">You are a viewer: read only.</span>}
      </div>

      <section className="stage">
        <div className="stage-main">
          <Office r={r} current={current} board={board} phase={phase} dayShown={dayShown} draftsWaiting={draftsWaiting} agmPinned={agmPinned}
            flights={flights} envelope={envelope} chaserAsleep={chaserAsleep} onPick={pick} roomPrices={roomPrices} />
          <div className="ticker" aria-live="polite">
            {last ? <>
              <span className="tk-who" style={{ '--c': AGENT_COLOR[last.agent] }}>{last.agent}</span>
              {last.tool && <code>{last.tool}()</code>}
              <span className="tk-text">{last.text}</span>
            </> : <span className="tk-text">The office is opening…</span>}
            <span className="tk-count">{played.length + (current ? 1 : 0)}/{total}</span>
          </div>
        </div>

        <aside className="rail">
          <div className="projfile">
            <div className="pf-head">
              <span>Project file</span>
              <b className={current ? 'pf-live' : ''}>{current ? `${current.agent} working` : phase === 'night' ? 'Asleep' : idle ? 'Idle' : 'Starting'}</b>
            </div>
            <dl>
              <div><dt>Size</dt><dd>{!r.recommended ? <button className="linkish" onClick={() => pick('docs')}>Needs bills</button>
                : r.plan_v2 ? <>{r.recommended.kw} → <b>{r.plan_v2.plan.recommended_kw} kW</b></> : <b>{r.recommended.kw} kW</b>}</dd></div>
              <div><dt>Quotes</dt><dd>{!r.audits.length ? <button className="linkish" onClick={() => pick('docs')}>None yet</button>
                : auditPlayed < r.audits.length ? `${auditPlayed} of ${r.audits.length} checked`
                : r.audits.map((a) => <span key={a.vendor} className={'dot ' + a.verdict.toLowerCase()} title={`${a.vendor}: ${a.verdict}`}>{a.verdict[0]}</span>)}</dd></div>
              <div className={draftsWaiting ? 'pf-alert' : ''}><dt>Your desk</dt><dd>{draftsWaiting ? <b>{draftsWaiting} to approve</b> : 'Empty'}</dd></div>
              <div><dt>DISCOM</dt><dd>{n.status === 'OVERDUE' ? <b className="bad">{n.overdue_by} days late</b> : n.stage ? 'Within its window' : 'All done'}</dd></div>
              <div><dt>Clock</dt><dd>Day {dayShown}{r.clock.simulated ? ' (simulated)' : ''}</dd></div>
            </dl>
          </div>
          <div className="controls">
            <button className="btn primary" disabled={busy} onClick={() => replayAll(project)}><PixelIcon grid={ICONS.play} pal={iconPal('#ffffff')} size={14} />Run the office again</button>
            <div className="tm">
              <span className="tm-l"><PixelIcon grid={ICONS.clock} pal={iconPal('#d4561c')} size={14} />Time machine <em>simulated</em></span>
              <div className="tm-b">
                <button className="btn dark" disabled={busy || !editRole} onClick={() => jump(25)}>+25 days</button>
                <button className="btn dark" disabled={busy || !editRole} onClick={() => jump(40)}>+40 days</button>
              </div>
            </div>
            {project.discom_reply
              ? <button className="btn ghost" disabled={busy || !canEdit} onClick={clearReply}>Remove the DISCOM reply</button>
              : <button className="btn dark" disabled={busy || !editRole} onClick={() => { setReplyText(''); setReplyOpen(true) }}>
                  <PixelIcon grid={ICONS.mail} pal={iconPal('#fbf8f1')} size={14} />A DISCOM reply arrived</button>}
            <button className="btn dark" disabled={busy || !live || !canEdit} onClick={runReview}
              title={live ? 'The Secretary calls the Auditor and the Chaser on Amazon Bedrock' : 'Live agents are off: this deployment runs the offline reader'}>
              Ask the agents to review</button>
            {project.review && <p className={'fine review-state' + (r.review_stale ? ' stale' : '')}>
              {r.review_stale ? 'The agents’ review is out of date: inputs changed since.' : `Reviewed by the agents on ${new Date(project.review.at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}.`}</p>}
            {!live && MODE === 'LIVE' && <p className="fine">Live agents are off in this deployment (offline reader).</p>}
            <div className="ctl-row">
              <button className="btn ghost" onClick={() => setSpeed(speed === 1 ? 2 : 1)} aria-label="Playback speed">{speed}× speed</button>
            </div>
          </div>
        </aside>
      </section>

      <section className="files" ref={filesRef}>
        <div className="tabs" role="tablist">
          {FOLDERS.map(([k, label]) => (
            <button key={k} role="tab" aria-selected={folder === k} className={'tab' + (folder === k ? ' on' : '')} onClick={() => setFolder(k)}>
              {label}
              {k === 'desk' && draftsWaiting > 0 && <span className="count">{draftsWaiting}</span>}
              {k === 'plan' && r.plan_v2 && <span className="count o">v2</span>}
              {k === 'docs' && (r.needs?.includes('bills') || r.needs?.includes('quotes')) && <span className="count">!</span>}
            </button>
          ))}
        </div>
        <div className="folder">
          {folder === 'plan' && <PlanCard r={r} canEdit={canEdit} session={session} onSaved={onSaved} notify={notify} goTo={setFolder} />}
          {folder === 'docs' && <Documents project={project} session={session} canEdit={canEdit} onSaved={onSaved} notify={notify} />}
          {folder === 'quotes' && <QuoteTable audits={r.audits} band={r.price_band} rulebook={r.rulebook} goTo={setFolder} review={project.review} stale={r.review_stale} />}
          {folder === 'pays' && <Fairness fairness={r.fairness} payback={r.recommended?.payback_years} goTo={setFolder} />}
          {folder === 'timeline' && <Timeline r={r} project={project} session={session} canEdit={canEdit} onSaved={onSaved} notify={notify} />}
          {folder === 'room' && <Arena negotiations={r.negotiations} audits={r.audits} />}
          {folder === 'desk' && <Drafts drafts={project.drafts} session={session} canEdit={canEdit} canApprove={editRole} canPolish={canEdit && live} actor={session.actor}
            onSaved={(next) => { projectRef.current = next; setProject(next) }} notify={notify} />}
          {folder === 'log' && <TracePanel played={played} current={current} mode={live ? 'live' : 'offline'} audit={project.audit} review={project.review} stale={r.review_stale} />}
          {folder === 'settings' && <Settings project={project} session={session} role={MODE === 'LIVE' ? role : 'viewer'}
            onSaved={(next) => { projectRef.current = next; setProject(next) }} onDeleted={() => { forgetProject(session.id); onLeave() }} notify={notify} />}
        </div>
      </section>

      <footer>
        <span>Nothing here is sent anywhere. Drafts need a person to approve them. Rules come from a dated rulebook; items marked “verify” must be checked against official guidelines.</span>
        <span>Built for Environmental Hacks 2026, Track 03 (Waste and Energy).</span>
      </footer>

      {replyOpen && (
        <Modal title="A reply from the DISCOM" onClose={() => setReplyOpen(false)}>
          <p>Paste the email or letter from {soc.discom || 'the DISCOM'}. The Chaser reads it and, if the DISCOM limits the capacity, re-plans.</p>
          <textarea rows={7} value={replyText} onChange={(e) => setReplyText(e.target.value)} placeholder="Paste the reply here…" />
          <div className="editor-actions">
            <button className="btn ghost" onClick={() => setReplyText(SAMPLE_DISCOM_REPLY)}>Use the sample reply</button>
            <button className="btn primary" disabled={(replyText || '').trim().length < 5} onClick={deliverReply}>Give it to the Chaser</button>
          </div>
        </Modal>
      )}
    </div>
  )
}
