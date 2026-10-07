// Turns raw trace events into plain sentences and tells the office scene where each one happens.
// Numbers come from the pipeline result (r), not from parsing the trace's shortened output strings.

export const AGENTS = ['Secretary', 'Reader', 'Auditor', 'Chaser']
export const AGENT_COLOR = { Secretary: '#24324f', Reader: '#157a74', Auditor: '#7a4a9a', Chaser: '#2d6cc0' }

// Which object in the office lights up when a plain-code tool runs.
const OBJECT = {
  sum_bills: 'bills', size_system: 'calc', money_summary: 'calc', fairness_table: 'calc', replan_for_load_limit: 'calc',
  audit_quote: 'cabinet', check_vendor: 'cabinet', get_rule: 'cabinet',
  run_simulated_negotiation: 'room', build_timeline: 'calendar', next_action: 'calendar', classify_reply: 'calendar',
}

export const inr = (n) => 'Rs ' + Math.round(n).toLocaleString('en-IN')
export const lakh = (n) => 'Rs ' + (n / 1e5).toFixed(2).replace(/\.?0+$/, '') + ' lakh'
const shortName = (v) => v.split(' ').slice(0, 2).join(' ')

export function describe(events, r) {
  const seen = {}
  return events.map((e) => {
    const k = (seen[e.tool] = (seen[e.tool] ?? -1) + 1)
    const base = { agent: e.agent, tool: e.tool, object: OBJECT[e.tool] || null, code: !!e.tool, flight: null }
    if (!e.tool) {
      const text = String(e.output)
      const flight = /^Drafted/.test(text) ? e.agent : /Drafted (an escalation|a polite reminder)/.test(text) ? e.agent : null
      return { ...base, text, flight }
    }
    return { ...base, text: say(e, k, r) }
  })
}

function say(e, k, r) {
  try {
    switch (e.tool) {
      case 'sum_bills':
        return `Read ${r.bills?.length ?? 12} monthly bills: ${r.annual_kwh.toLocaleString('en-IN')} kWh a year on the common meter.`
      case 'size_system':
        return `Sized from real use: ${r.plan.recommended_kw} kW. The ${r.plan.subsidy_ceiling_kw} kW subsidy ceiling is a limit, not a target.`
      case 'money_summary': {
        const opt = r.plan.options[k], m = r.money[opt.label]
        return `${opt.label[0].toUpperCase() + opt.label.slice(1)}, ${m.kw} kW: society pays ${lakh(m.net_cost)}, payback ${m.payback_years} yrs.`
      }
      case 'audit_quote': {
        const a = r.audits[k]
        return `${a.vendor}: ${inr(a.price_per_kw)} per kW, ${a.flags.length} flag(s).`
      }
      case 'run_simulated_negotiation': {
        const n = r.negotiations[k]
        return n.skipped
          ? `${shortName(n.vendor)} is unverified, so it gets a proof request, not a haggle.`
          : `${shortName(n.vendor)}: ${lakh(n.start_price)} to ${lakh(n.final_price)} in ${Math.ceil(n.rounds.length / 2)} rounds (simulated).`
      }
      case 'fairness_table': {
        const f = r.fairness.flats[0]
        return `Equal split across ${r.fairness.total_flats ?? r.society.flats} flats: ${inr(f.equal_cost)} each, saving ${inr(f.equal_saving_year)} a year.`
      }
      case 'build_timeline': {
        const s = r.timeline.find((x) => x.status !== 'DONE')
        return s ? `Day ${r.today_day}: ${s.label} is ${s.status.toLowerCase()}${s.overdue_by ? `, ${s.overdue_by} days late` : ''}.` : 'Every stage is done.'
      }
      case 'classify_reply':
        return r.plan_v2 ? `DISCOM replied: ${r.plan_v2.reason}.` : 'DISCOM replied. Nothing in the plan needs to change.'
      case 'replan_for_load_limit':
        return `Plan v2: ${r.recommended.kw} kW becomes ${r.plan_v2.plan.recommended_kw} kW to fit the DISCOM limit.`
    }
  } catch { /* fall through to the generic line */ }
  return `${e.tool}: ${String(e.output).slice(0, 90)}`
}

// What the whiteboard shows, based on the events played so far.
export function boardItems(played, r) {
  const has = (t) => played.some((e) => e.tool === t)
  const audits = played.filter((e) => e.tool === 'audit_quote').length
  const drafted = played.some((e) => !e.tool && /^Drafted/.test(String(e.text)))
  const chase = played.find((e) => e.agent === 'Chaser' && !e.tool && /Drafted/.test(e.text))
  const replanned = has('replan_for_load_limit')
  // The five jobs from the guide (Section 6), in its order.
  return [
    { label: 'Understand: read bills', done: has('sum_bills') },
    { label: 'Size: right kW', done: has('size_system') },
    { label: 'Decide: AGM papers', done: drafted },
    { label: `Choose: quotes ${audits}/${r.audits.length}`, done: audits >= r.audits.length },
    { label: replanned ? 'Follow: plan v2' : chase ? 'Follow: escalated' : 'Follow: DISCOM', done: replanned || !!chase },
  ]
}
