import React, { useCallback, useEffect, useRef, useState } from 'react'
import { MODE, createProject, advance, sendDiscomReply, approveDraft, DISCOM_REPLY_EXAMPLE } from './api.js'
import Office from './office/Office.jsx'
import { describe, boardItems, AGENT_COLOR } from './office/story.js'
import { PixelIcon } from './pixel/Sprite.jsx'
import { ICONS, iconPal } from './pixel/sprites.js'
import PlanCard from './components/PlanCard.jsx'
import QuoteTable from './components/QuoteTable.jsx'
import Fairness from './components/Fairness.jsx'
import Timeline from './components/Timeline.jsx'
import Arena from './components/Arena.jsx'
import Drafts from './components/Drafts.jsx'
import TracePanel from './components/TracePanel.jsx'

const sleep = (ms) => new Promise((res) => setTimeout(res, ms))
const sig = (e) => `${e.agent}|${e.tool}|${e.output}`
const shortLakh = (n) => '₹' + (n / 1e5).toFixed(1).replace(/\.0$/, '') + 'L'
const FOLDERS = [['plan', 'The plan'], ['quotes', 'Quote audit'], ['pays', 'Who pays'], ['timeline', 'Timeline'],
  ['room', 'Negotiation room'], ['desk', 'Your desk'], ['log', 'Logbook']]

export default function App() {
  const [project, setProject] = useState(null)
  const [error, setError] = useState('')
  const [played, setPlayed] = useState([])
  const [queue, setQueue] = useState([])
  const [current, setCurrent] = useState(null)
  const [phase, setPhase] = useState('day')
  const [dayShown, setDayShown] = useState(0)
  const [flights, setFlights] = useState([])
  const [envelope, setEnvelope] = useState(false)
  const [busy, setBusy] = useState(false)
  const [folder, setFolder] = useState('plan')
  const [speed, setSpeed] = useState(1)
  const keyRef = useRef(0)
  const filesRef = useRef(null)
  const withKey = (e) => ({ ...e, key: ++keyRef.current })

  const load = useCallback((p) => {
    setProject(p); setPlayed([]); setCurrent(null); setDayShown(p.result.today_day)
    setQueue(describe(p.result.trace, p.result).map(withKey))
  }, [])

  // Replays only what is new after a time jump or a DISCOM reply. The wake-up check always replays.
  const continueWith = (prev, next) => {
    const oldSigs = new Set(prev.result.trace.map(sig))
    const desc = describe(next.result.trace, next.result).map(withKey)
    const isNew = next.result.trace.map((e) => !oldSigs.has(sig(e)) || e.tool === 'build_timeline')
    setProject(next); setCurrent(null)
    setPlayed(desc.filter((_, i) => !isNew[i]))
    setQueue(desc.filter((_, i) => isNew[i]))
  }

  useEffect(() => { createProject().then(load).catch((e) => setError(String(e))) }, [load])

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
    setBusy(true); setError('')
    try { await fn() } catch (e) { setError(String(e)); setPhase('day') } finally { setBusy(false) }
  }
  const jump = (days) => act(async () => {
    const prev = project, to = Math.min(dayShown + days, MODE === 'MOCK' ? 50 : Infinity)
    setPhase('night'); setQueue([]); setCurrent(null)
    const tick = setInterval(() => setDayShown((d) => (d < to ? Math.min(to, d + Math.max(1, Math.round(days / 24))) : d)), 90)
    const [next] = await Promise.all([advance(prev, days), sleep(2700)])
    clearInterval(tick); setDayShown(next.result.today_day)
    setPhase('ring'); await sleep(1100); setPhase('day')
    continueWith(prev, next)
  })
  const reply = () => act(async () => {
    const prev = project
    setEnvelope(true)
    const [next] = await Promise.all([sendDiscomReply(prev, DISCOM_REPLY_EXAMPLE), sleep(1500)])
    setEnvelope(false); setDayShown(next.result.today_day)
    continueWith(prev, next)
  })
  const approve = (id) => act(async () => setProject(await approveDraft(project, id)))
  const startOver = () => act(async () => { setPhase('day'); load(await createProject()) })
  const pick = (f) => { setFolder(f); filesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }

  if (error && !project) return <div className="wrap"><p className="err">{error}</p></div>
  if (!project) return <div className="wrap loading">Opening the office…</div>

  const r = project.result
  const board = boardItems(played, r)
  const idle = !current && !queue.length
  const secretaryDrafted = played.some((e) => e.agent === 'Secretary' && /^Drafted/.test(e.text))
  const chaserDrafted = played.some((e) => e.agent === 'Chaser' && /Drafted/.test(e.text))
  const waiting = project.drafts.filter((d) => d.status === 'DRAFT')
  const chaserPending = waiting.some((d) => d.kind.startsWith('discom_')) && !chaserDrafted ? 1 : 0
  const draftsWaiting = secretaryDrafted ? waiting.length - chaserPending : 0
  const agmPinned = project.drafts.some((d) => d.kind === 'agm_notice' && d.status === 'APPROVED') ? r.recommended.kw : 0
  const negPlayed =played.filter((e) => e.tool === 'run_simulated_negotiation').length
  const auditPlayed = played.filter((e) => e.tool === 'audit_quote').length
  const roomPrices = r.negotiations.map((neg, i) => {
    if (i >= auditPlayed) return null
    if (neg.skipped) return 'proof?'
    return shortLakh(i < negPlayed ? neg.final_price : neg.start_price)
  })
  const n = r.next_action
  const chaserAsleep = n.status !== 'OVERDUE' && current?.agent !== 'Chaser' && played.length > 0
  const last = current || played[played.length - 1]
  const total = played.length + queue.length + (current ? 1 : 0)
  const modeLabel = MODE === 'MOCK' ? 'Bundled demo data' : r.mode === 'offline' ? 'Local API · offline pipeline' : 'Live agents on Bedrock'

  return (
    <div className="wrap">
      <header className="appbar">
        <div className="brand">
          <svg className="mark" viewBox="0 0 8 8" shapeRendering="crispEdges" aria-hidden="true">
            <rect x="2" y="1" width="4" height="4" fill="#ef6a1a" /><rect x="1" y="2" width="6" height="2" fill="#ef6a1a" /><rect x="0" y="6" width="8" height="2" fill="#2f6db5" />
          </svg>
          <b>SolarSabha</b>
          <span className="meta">{r.society.name} · {r.society.flats} flats · {r.society.discom}</span>
        </div>
        <div className="badges">
          <span className="chip trackchip"><i />Track 03 · Waste and Energy</span>
          <span className="chip">{modeLabel}</span>
          {r.mode === 'offline' && <span className="chip">No AI model in this run</span>}
          <span className="tape">Simulated: {r.simulated_parts.join(', ')}</span>
        </div>
      </header>

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
              <div><dt>Size</dt><dd>{r.plan_v2 ? <>{r.recommended.kw} → <b>{r.plan_v2.plan.recommended_kw} kW</b></> : <b>{r.recommended.kw} kW</b>}</dd></div>
              <div><dt>Quotes</dt><dd>{auditPlayed < r.audits.length ? `${auditPlayed} of ${r.audits.length} checked` : r.audits.map((a) => <span key={a.vendor} className={'dot ' + a.verdict.toLowerCase()} title={`${a.vendor}: ${a.verdict}`}>{a.verdict[0]}</span>)}</dd></div>
              <div className={draftsWaiting ? 'pf-alert' : ''}><dt>Your desk</dt><dd>{draftsWaiting ? <b>{draftsWaiting} drafts to approve</b> : 'Empty'}</dd></div>
              <div><dt>DISCOM</dt><dd>{n.status === 'OVERDUE' ? <b className="bad">{n.overdue_by} days late</b> : 'Within its window'}</dd></div>
              <div><dt>Clock</dt><dd>Day {dayShown}</dd></div>
            </dl>
          </div>
          <div className="controls">
            <button className="btn primary" disabled={busy} onClick={() => load(project)}><PixelIcon grid={ICONS.play} pal={iconPal('#161412')} size={14} />Run the office again</button>
            <div className="tm">
              <span className="tm-l"><PixelIcon grid={ICONS.clock} pal={iconPal('#ef6a1a')} size={14} />Time machine <em>simulated</em></span>
              <div className="tm-b">
                <button className="btn dark" disabled={busy} onClick={() => jump(25)}>+25 days</button>
                <button className="btn dark" disabled={busy} onClick={() => jump(50)}>+50 days</button>
              </div>
            </div>
            <button className="btn dark" disabled={busy || !!r.plan_v2} onClick={reply}><PixelIcon grid={ICONS.mail} pal={iconPal('#fbf8f1')} size={14} />{r.plan_v2 ? 'DISCOM reply delivered' : 'Deliver the DISCOM’s reply'}</button>
            <div className="ctl-row">
              <button className="btn ghost" disabled={busy} onClick={startOver}><PixelIcon grid={ICONS.reset} pal={iconPal('#161412')} size={13} />Start over</button>
              <button className="btn ghost" onClick={() => setSpeed(speed === 1 ? 2 : 1)} aria-label="Playback speed">{speed}× speed</button>
            </div>
            {error && <p className="err small">{error}</p>}
          </div>
        </aside>
      </section>

      <section className="files" ref={filesRef}>
        <div className="tabs" role="tablist">
          {FOLDERS.map(([k, label]) => (
            <button key={k} role="tab" aria-selected={folder === k} className={'tab' + (folder === k ? ' on' : '')} onClick={() => setFolder(k)}>
              {label}{k === 'desk' && draftsWaiting > 0 && <span className="count">{draftsWaiting}</span>}
              {k === 'plan' && r.plan_v2 && <span className="count o">v2</span>}
            </button>
          ))}
        </div>
        <div className="folder">
          {folder === 'plan' && <PlanCard r={r} />}
          {folder === 'quotes' && <QuoteTable audits={r.audits} band={r.price_band} />}
          {folder === 'pays' && <Fairness fairness={r.fairness} payback={r.recommended.payback_years} />}
          {folder === 'timeline' && <Timeline r={r} />}
          {folder === 'room' && <Arena negotiations={r.negotiations} audits={r.audits} />}
          {folder === 'desk' && <Drafts drafts={project.drafts} onApprove={approve} />}
          {folder === 'log' && <TracePanel played={played} current={current} mode={r.mode} />}
        </div>
      </section>

      <footer>
        <span>Nothing here is sent anywhere. Drafts need a human. Rules come from a dated rulebook; items marked “verify” must be checked against official guidelines.</span>
        <span>Sample society, bills, quotes and vendor list. Built for Environmental Hacks 2026, Track 03.</span>
      </footer>
    </div>
  )
}
