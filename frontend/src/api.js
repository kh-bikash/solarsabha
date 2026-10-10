// Two modes. LIVE: VITE_API_URL points at the API (local: `python scripts/dev_server.py`, VITE_API_URL=http://localhost:8787).
// MOCK (no VITE_API_URL): a read-only walk through the bundled sample (src/mock/demo.json, from scripts/export_demo_json.py).
import demo from './mock/demo.json'

const BASE = import.meta.env.VITE_API_URL || ''
export const MODE = BASE ? 'LIVE' : 'MOCK'
export const SAMPLE_DISCOM_REPLY = 'Subject: Feasibility query. The sanctioned load for the common meter is insufficient for this capacity. Maximum permissible solar is 25 kW. Please revise.'

export class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status }
}

async function call(session, method, path, body) {
  const headers = { 'content-type': 'application/json' }
  if (session?.key) headers['x-project-key'] = session.key
  if (session?.actor) headers['x-actor'] = encodeURIComponent(session.actor)
  let r
  try {
    r = await fetch(BASE + path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined })
  } catch {
    throw new ApiError(0, 'Cannot reach the SolarSabha API. Is it running?')
  }
  const data = await r.json().catch(() => ({}))
  if (r.status === 409 && data.conflict) window.dispatchEvent(new CustomEvent('solarsabha:conflict'))   // someone saved first
  if (!r.ok) throw new ApiError(r.status, data.error || `Request failed (${r.status})`)
  return data
}

async function download(session, path) {
  const r = await fetch(BASE + path, { headers: { 'x-project-key': session.key } })
  if (!r.ok) throw new ApiError(r.status, (await r.json().catch(() => ({}))).error || 'Download failed')
  const name = /filename="([^"]+)"/.exec(r.headers.get('content-disposition') || '')?.[1] || 'download'
  const url = URL.createObjectURL(await r.blob())
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  document.body.appendChild(a); a.click(); a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

const toBase64 = (file) => new Promise((resolve, reject) => {
  const fr = new FileReader()
  fr.onload = () => resolve(String(fr.result).split(',')[1])
  fr.onerror = () => reject(new ApiError(0, 'Could not read the file'))
  fr.readAsDataURL(file)
})

// ---------- mock: the bundled sample, enough to walk through the demo without a server ----------
let mockState = null
const mockFrame = (name) => structuredClone(demo[name])
const readOnly = async () => { throw new ApiError(0, 'This is the static demo. Run the API to edit, upload or create projects.') }
const mock = {
  create: async () => (mockState = { ...mockFrame('start'), access_key: 'demo' }),
  get: async () => mockState || mock.create(),
  advance: async (s, days) => {
    const day = Math.min(mockState.result.clock.today_day + days, 50)
    const f = mockFrame(day >= 40 ? 'day50' : 'start')
    f.result.clock = { ...f.result.clock, today_day: day, simulated: day > 10 }
    return (mockState = { ...f, draft_state: mockState.draft_state, drafts: keepApprovals(f.drafts) })
  },
  reply: async () => { const f = mockFrame('day50_reply'); return (mockState = { ...f, drafts: keepApprovals(f.drafts) }) },
  approve: async (s, id, name) => {
    mockState.drafts = mockState.drafts.map((d) => (d.id === id ? { ...d, status: 'APPROVED', approved_by: name, approved_at: new Date().toISOString() } : d))
    return mockState
  },
}
function keepApprovals(drafts) {
  const ok = new Map((mockState?.drafts || []).filter((d) => d.status === 'APPROVED').map((d) => [d.id, d]))
  return drafts.map((d) => (ok.has(d.id) ? { ...d, ...pick(ok.get(d.id)) } : d))
}
const pick = (d) => ({ status: d.status, approved_by: d.approved_by, approved_at: d.approved_at })

// ---------- the API ----------
export const api = {
  createProject: (body) => (MODE === 'MOCK' ? (body.sample ? mock.create() : readOnly()) : call(null, 'POST', '/projects', body)),
  getProject: (s) => (MODE === 'MOCK' ? mock.get() : call(s, 'GET', `/projects/${s.id}`)),
  put: (s, section, body) => (MODE === 'MOCK' ? readOnly() : call(s, 'PUT', `/projects/${s.id}/${section}`, body)),
  upload: async (s, kind, file) => {
    if (MODE === 'MOCK') return readOnly()
    if (file.size > 6 * 1024 * 1024) throw new ApiError(400, `${file.name} is larger than 6 MB`)
    return call(s, 'POST', `/projects/${s.id}/documents`, { kind, filename: file.name, content_base64: await toBase64(file) })
  },
  deleteDocument: (s, did) => (MODE === 'MOCK' ? readOnly() : call(s, 'DELETE', `/projects/${s.id}/documents/${did}`)),
  downloadDocument: (s, did) => (MODE === 'MOCK' ? readOnly() : download(s, `/projects/${s.id}/documents/${did}`)),
  advance: (s, days) => (MODE === 'MOCK' ? mock.advance(s, days) : call(s, 'POST', `/projects/${s.id}/advance`, { days })),
  resetClock: (s) => (MODE === 'MOCK' ? readOnly() : call(s, 'POST', `/projects/${s.id}/clock/reset`, {})),
  discomReply: (s, text) => (MODE === 'MOCK' ? mock.reply() : call(s, 'POST', `/projects/${s.id}/discom-reply`, { text })),
  clearReply: (s) => (MODE === 'MOCK' ? readOnly() : call(s, 'DELETE', `/projects/${s.id}/discom-reply`)),
  editDraft: (s, id, subject, body) => (MODE === 'MOCK' ? readOnly() : call(s, 'PUT', `/projects/${s.id}/drafts/${id}`, { subject, body, editor: s.actor })),
  approveDraft: (s, id) => (MODE === 'MOCK' ? mock.approve(s, id, s.actor) : call(s, 'POST', `/projects/${s.id}/drafts/${id}/approve`, { name: s.actor })),
  downloadDraft: (s, id) => (MODE === 'MOCK' ? readOnly() : download(s, `/projects/${s.id}/drafts/${id}/docx`)),
  exportProject: async (s) => {
    const data = MODE === 'MOCK' ? mockState : await call(s, 'GET', `/projects/${s.id}/export`)
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: `solarsabha-${s.id}.json` })
    document.body.appendChild(a); a.click(); a.remove()
  },
  review: (s) => (MODE === 'MOCK' ? readOnly() : call(s, 'POST', `/projects/${s.id}/review`, {})),
  polishDraft: (s, id) => (MODE === 'MOCK' ? readOnly() : call(s, 'POST', `/projects/${s.id}/drafts/${id}/polish`, {})),
  deleteProject: (s, confirmName) => (MODE === 'MOCK' ? readOnly() : call(s, 'DELETE', `/projects/${s.id}`, { confirm_name: confirmName })),
}
