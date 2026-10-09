import React, { useEffect, useState } from 'react'
import { api, MODE } from '../api.js'
import { shareLink } from '../session.js'
import { STATES } from '../states.js'
import { Field } from './ui.jsx'
import PrivacyNotice from './PrivacyNotice.jsx'

const ROLE_HELP = { secretary: 'everything, including members and deletion', member: 'edit, upload and approve', viewer: 'read only' }

export default function Settings({ project, session, role, onSaved, onDeleted, notify }) {
  const soc = project.inputs.society
  const [s, setS] = useState(soc)
  const [members, setMembers] = useState(project.members)
  const [confirm, setConfirm] = useState('')
  const [privacy, setPrivacy] = useState(false)
  useEffect(() => setS(soc), [JSON.stringify(soc)])
  useEffect(() => setMembers(project.members), [JSON.stringify(project.members)])
  const canEdit = role === 'secretary' || role === 'member'
  const isSec = role === 'secretary'
  const set = (k) => (e) => setS({ ...s, [k]: k === 'flats' ? e.target.value : e.target.value })

  const saveSociety = async (e) => {
    e.preventDefault()
    try { onSaved(await api.put(session, 'society', { ...s, flats: Number(s.flats) })); notify('ok', 'Society details saved.') } catch (err) { notify('error', err.message) }
  }
  const saveMembers = async () => {
    try { onSaved(await api.put(session, 'members', { members: members.filter((m) => m.name.trim()) })); notify('ok', 'Members saved.') } catch (err) { notify('error', err.message) }
  }
  const remove = async () => {
    try { await api.deleteProject(session, confirm); notify('ok', 'Project deleted, with all its files and data.'); onDeleted() } catch (err) { notify('error', err.message) }
  }
  const copy = async () => {
    try { await navigator.clipboard.writeText(shareLink(session)); notify('ok', 'Link copied. Share it only with your committee.') }
    catch { window.prompt('Copy this link', shareLink(session)) }
  }

  return (
    <div className="folder-body settings">
      <form className="editor" onSubmit={saveSociety}>
        <header><h4>Society</h4><span className="fine">{project.result.rule_coverage?.message}</span></header>
        <div className="f-grid">
          <Field label="Society name"><input required value={s.name} disabled={!canEdit} onChange={set('name')} /></Field>
          <Field label="Number of flats"><input required type="number" min={1} max={5000} value={s.flats} disabled={!canEdit} onChange={set('flats')} /></Field>
          <Field label="Address"><input value={s.address || ''} disabled={!canEdit} onChange={set('address')} /></Field>
          <Field label="City"><input value={s.city || ''} disabled={!canEdit} onChange={set('city')} /></Field>
          <Field label="State">
            <select value={s.state || ''} disabled={!canEdit} onChange={set('state')}>
              <option value="">Not set</option>{STATES.map((x) => <option key={x}>{x}</option>)}
            </select>
          </Field>
          <Field label="DISCOM"><input value={s.discom || ''} disabled={!canEdit} onChange={set('discom')} /></Field>
          <Field label="Portal application no." hint="Used in letters to the DISCOM."><input value={s.application_ref || ''} disabled={!canEdit} onChange={set('application_ref')} /></Field>
          <Field label="Common-meter consumer no."><input value={s.consumer_no || ''} disabled={!canEdit} onChange={set('consumer_no')} /></Field>
        </div>
        {canEdit && <div className="editor-actions"><button className="btn primary">Save society details</button></div>}
      </form>

      <section className="editor">
        <header><h4>Committee members</h4><span className="fine">Only the secretary can change this list.</span></header>
        <table className="ledger edit">
          <thead><tr><th>Name</th><th>Role</th><th>Can</th><th /></tr></thead>
          <tbody>
            {members.map((m, i) => (
              <tr key={i}>
                <td><input value={m.name} disabled={!isSec} onChange={(e) => setMembers(members.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))} /></td>
                <td>
                  <select value={m.role} disabled={!isSec} onChange={(e) => setMembers(members.map((x, j) => (j === i ? { ...x, role: e.target.value } : x)))}>
                    <option value="secretary">Secretary</option><option value="member">Member</option><option value="viewer">Viewer</option>
                  </select>
                </td>
                <td className="small muted">{ROLE_HELP[m.role]}</td>
                <td>{isSec && <button className="btn ghost tiny" onClick={() => setMembers(members.filter((_, j) => j !== i))}>Remove</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isSec && (
          <div className="editor-actions">
            <button className="btn ghost" onClick={() => setMembers([...members, { name: '', role: 'member' }])}>Add member</button>
            <button className="btn primary" onClick={saveMembers}>Save members</button>
          </div>
        )}
      </section>

      <section className="editor">
        <header><h4>Sharing and privacy</h4></header>
        <p>Anyone with this project’s link can open it, because the link contains its access key. Share it only with your committee.</p>
        <div className="editor-actions left">
          {MODE === 'LIVE' && <button className="btn dark" onClick={copy}>Copy share link</button>}
          <button className="btn ghost" onClick={() => api.exportProject(session).catch((e) => notify('error', e.message))}>Export all data (JSON)</button>
          <button className="btn ghost" onClick={() => setPrivacy(true)}>Privacy notice</button>
        </div>
        <p className="fine">{project.sample ? 'Sample project: fictional data.' : `Consent recorded from ${project.consent?.by} on ${project.consent?.at?.slice(0, 10)}.`}
          {' '}This project is deleted automatically on {new Date(project.expires_at * 1000).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}.</p>
      </section>

      {isSec && MODE === 'LIVE' && (
        <section className="editor danger">
          <header><h4>Delete this project</h4></header>
          <p>This permanently deletes the project, every uploaded file and all its data. It cannot be undone. Export first if you need a copy.</p>
          <div className="editor-actions left">
            <input placeholder={`Type “${soc.name}” to confirm`} value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            <button className="btn danger" disabled={confirm.trim().toLowerCase() !== soc.name.toLowerCase()} onClick={remove}>Delete project</button>
          </div>
        </section>
      )}
      {privacy && <PrivacyNotice onClose={() => setPrivacy(false)} />}
    </div>
  )
}
