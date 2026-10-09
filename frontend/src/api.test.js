import { describe, expect, it } from 'vitest'
import { api, MODE } from './api.js'

// Without VITE_API_URL the app runs as a read-only static demo of the sample society.
describe('static demo mode', () => {
  const s = { id: 'demo', key: 'demo', actor: 'Meera (sample)' }

  it('runs without a server', () => expect(MODE).toBe('MOCK'))

  it('walks the sample through the time machine, a DISCOM reply and an approval', async () => {
    const start = await api.createProject({ sample: true })
    expect(start.result.clock.today_day).toBe(10)
    const later = await api.advance(s, 40)
    expect(later.result.clock.today_day).toBe(50)
    expect(later.result.next_action.status).toBe('OVERDUE')
    const replied = await api.discomReply(s, 'any text')
    expect(replied.result.plan_v2.plan.recommended_kw).toBe(25)
    const id = replied.drafts[0].id
    const approved = await api.approveDraft(s, id)
    expect(approved.drafts[0]).toMatchObject({ status: 'APPROVED', approved_by: 'Meera (sample)' })
  })

  it('refuses edits with a clear message', async () => {
    await expect(api.put(s, 'bills', { bills: [] })).rejects.toThrow(/static demo/)
    await expect(api.createProject({ society: { name: 'X', flats: 1 } })).rejects.toThrow(/static demo/)
  })
})
