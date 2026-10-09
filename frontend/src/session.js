// Where this browser keeps its projects: id + access key per project, and who you are in each.
// The access key is a shared secret; the share link carries it in the URL hash (never sent to the server as a URL).
const LIST = 'solarsabha.projects'
const safe = (fn, fallback) => { try { return fn() } catch { return fallback } }

export function savedProjects() {
  return safe(() => JSON.parse(localStorage.getItem(LIST)) || [], [])
}

export function rememberProject(p) {
  const rest = savedProjects().filter((x) => x.id !== p.id)
  safe(() => localStorage.setItem(LIST, JSON.stringify([{ id: p.id, key: p.key, name: p.name }, ...rest].slice(0, 20))))
}

export function forgetProject(id) {
  safe(() => localStorage.setItem(LIST, JSON.stringify(savedProjects().filter((x) => x.id !== id))))
  safe(() => localStorage.removeItem(`solarsabha.actor.${id}`))
}

export const getActor = (id) => safe(() => localStorage.getItem(`solarsabha.actor.${id}`), null)
export const setActor = (id, name) => safe(() => localStorage.setItem(`solarsabha.actor.${id}`, name))

// #p=<id>&k=<key> opens a shared project
export function fromHash() {
  const h = new URLSearchParams(window.location.hash.slice(1))
  return h.get('p') && h.get('k') ? { id: h.get('p'), key: h.get('k') } : null
}

export function setHash(s) {
  const url = s ? `#p=${s.id}&k=${encodeURIComponent(s.key)}` : ' '
  window.history.replaceState(null, '', url === ' ' ? window.location.pathname : url)
}

export function shareLink(s) {
  return `${window.location.origin}${window.location.pathname}#p=${s.id}&k=${encodeURIComponent(s.key)}`
}
