import React, { useState } from 'react'
import { MODE, api } from '../api.js'
import { savedProjects, forgetProject } from '../session.js'
import { STATES } from '../states.js'
import { Field } from './ui.jsx'
import PrivacyNotice from './PrivacyNotice.jsx'

export default function Welcome({ onOpen, notify }) {
  const [form, setForm] = useState({ name: '', flats: '', city: '', state: '', discom: '', you: '', consent: false })
  const [busy, setBusy] = useState(false)
  const [privacy, setPrivacy] = useState(false)
  const [saved, setSaved] = useState(savedProjects())
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const open = async (body) => {
    setBusy(true)
    try {
      const d = await api.createProject(body)
      onOpen({ id: d.id, key: d.access_key, name: d.inputs.society.name }, d)
    } catch (e) { notify('error', e.message) } finally { setBusy(false) }
  }
  const start = (e) => {
    e.preventDefault()
    open({
      society: { name: form.name, flats: Number(form.flats), city: form.city, state: form.state, discom: form.discom },
      you: { name: form.you, role: 'secretary' }, consent: form.consent,
    })
  }

  return (
    <div className="welcome">
      <section className="w-intro">
        <h2>Rooftop solar for your housing society, managed from one place.</h2>
        <p>SolarSabha reads your common-area electricity bills, sizes the system, checks vendor quotations for traps, drafts the meeting
          papers and letters, and keeps track of the DISCOM. Your committee approves everything. Nothing is ever sent on its own.</p>
      </section>

      <div className="w-grid">
        <section className="w-card">
          <h3>See it with a sample society</h3>
          <p>Sunrise Apartments: 50 flats, a year of bills, three vendor quotations (one of them hides a trap). All sample data is fictional.</p>
          <button className="btn primary" disabled={busy} onClick={() => open({ sample: true })}>Open the sample society</button>
          {saved.length > 0 && (
            <div className="w-saved">
              <h4>Projects on this browser</h4>
              <ul>
                {saved.map((p) => (
                  <li key={p.id}>
                    <button className="linkish" onClick={() => onOpen(p)}>{p.name}</button>
                    <button className="btn ghost tiny" onClick={() => { forgetProject(p.id); setSaved(savedProjects()) }}>Forget</button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <form className="w-card" onSubmit={start}>
          <h3>Start your society’s project</h3>
          {MODE === 'MOCK' && <p className="notice warn">This is the static demo. Run the API to create real projects.</p>}
          <div className="f-grid">
            <Field label="Society name"><input required minLength={2} maxLength={120} value={form.name} onChange={set('name')} placeholder="e.g. Green Park CHS Ltd" /></Field>
            <Field label="Number of flats"><input required type="number" min={1} max={5000} value={form.flats} onChange={set('flats')} /></Field>
            <Field label="City"><input maxLength={80} value={form.city} onChange={set('city')} /></Field>
            <Field label="State">
              <select value={form.state} onChange={set('state')}>
                <option value="">Choose…</option>
                {STATES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Electricity company (DISCOM)"><input maxLength={120} value={form.discom} onChange={set('discom')} /></Field>
            <Field label="Your name" hint="You become the project's secretary."><input required minLength={2} maxLength={80} value={form.you} onChange={set('you')} /></Field>
          </div>
          <label className="check">
            <input type="checkbox" checked={form.consent} onChange={set('consent')} required />
            <span>I have read the <button type="button" className="linkish" onClick={() => setPrivacy(true)}>privacy notice</button> and agree that
              SolarSabha stores our society’s bills, quotations and committee names for this project.</span>
          </label>
          <button className="btn primary" disabled={busy || MODE === 'MOCK'}>Create project</button>
        </form>
      </div>
      {privacy && <PrivacyNotice onClose={() => setPrivacy(false)} />}
    </div>
  )
}
