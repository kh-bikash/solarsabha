import { describe as suite, expect, it } from 'vitest'
import demo from '../mock/demo.json'
import { describe, boardItems, lakh, inr } from './story.js'

const start = demo.start.result
const day50 = demo.day50_reply.result

suite('describe() turns trace events into plain sentences', () => {
  it('describes every event without falling back to raw tool output', () => {
    for (const r of [start, day50]) {
      const events = describe(r.trace, r)
      expect(events).toHaveLength(r.trace.length)
      for (const e of events) {
        expect(e.text).toBeTruthy()
        expect(e.text).not.toMatch(/^\w+: \{/)          // the generic fallback prints a dict
      }
    }
  })
  it('maps plain-code tools to office objects and flags paper flights', () => {
    const events = describe(start.trace, start)
    expect(events.find((e) => e.tool === 'size_system').object).toBe('calc')
    expect(events.find((e) => e.tool === 'audit_quote').object).toBe('cabinet')
    expect(events.some((e) => e.flight === 'Secretary')).toBe(true)
  })
  it('uses the real numbers from the result', () => {
    const sizing = describe(start.trace, start).find((e) => e.tool === 'size_system')
    expect(sizing.text).toContain(`${start.plan.recommended_kw} kW`)
    const replan = describe(day50.trace, day50).find((e) => e.tool === 'replan_for_load_limit')
    expect(replan.text).toContain(`${day50.plan_v2.plan.recommended_kw} kW`)
  })
})

suite('boardItems() ticks the five jobs from what has played', () => {
  it('starts empty and finishes ticked', () => {
    expect(boardItems([], start).every((b) => !b.done)).toBe(true)
    const all = describe(day50.trace, day50)
    const done = boardItems(all, day50)
    expect(done.map((b) => b.done)).toEqual([true, true, true, true, true])
    expect(done[4].label).toMatch(/plan v2/)
  })
  it('does not tick quotes when there are none', () => {
    const empty = { ...start, audits: [] }
    expect(boardItems([], empty)[3].done).toBe(false)
  })
})

suite('money formatting', () => {
  it('formats rupees the Indian way', () => {
    expect(inr(1152000)).toBe('Rs 11,52,000')
    expect(lakh(1152000)).toBe('Rs 11.52 lakh')
    expect(lakh(800000)).toBe('Rs 8 lakh')
  })
})
