import React from 'react'
import { inr } from '../office/story.js'

const VERDICT = { GREEN: { c: '#2f8a3e', t: 'Fair and clear' }, AMBER: { c: '#c98a00', t: 'Ask questions first' }, RED: { c: '#c63a2b', t: 'Do not proceed yet' } }

// Price per kW on one shared scale, with the rulebook's usual band shaded. A position, not a verdict.
function PriceBand({ price, band, color }) {
  const lo = 30000, hi = 65000, W = 300
  const x = (v) => 8 + ((Math.min(Math.max(v, lo), hi) - lo) / (hi - lo)) * (W - 16)
  return (
    <svg className="band" viewBox={`0 0 ${W} 46`} role="img" aria-label={`${inr(price)} per kW against the usual band ${inr(band.low)} to ${inr(band.high)}`}>
      <rect x="8" y="16" width={W - 16} height="6" rx="3" fill="#ece5d6" />
      <rect x={x(band.low)} y="16" width={x(band.high) - x(band.low)} height="6" fill="#cfc4ad" />
      <text x={(x(band.low) + x(band.high)) / 2} y="11" textAnchor="middle" className="tick">usual band</text>
      {[band.low, band.high].map((v) => <text key={v} x={x(v)} y="36" textAnchor="middle" className="tick">{v / 1000}k</text>)}
      <circle cx={x(price)} cy="19" r="6.5" fill={color} stroke="#fbf8f1" strokeWidth="2.5" />
      <title>{inr(price)} per kW</title>
    </svg>
  )
}

export default function QuoteTable({ audits, band }) {
  return (
    <div className="folder-body">
      <div className="quotes">
        {audits.map((a) => {
          const v = VERDICT[a.verdict]
          return (
            <article key={a.vendor} className="qcard" style={{ '--v': v.c }}>
              <header>
                <div><h4>{a.vendor}</h4><span className="mono">{inr(a.price_per_kw)} per kW</span></div>
                <span className="stamp">{a.verdict}</span>
              </header>
              {band && <PriceBand price={a.price_per_kw} band={band} color={v.c} />}
              <p className="verdict-line"><b>{v.t}.</b> {a.vendor_check?.found_in_list ? 'On the sample vendor list.' : 'Not found on the sample vendor list.'}</p>
              <ul className="flags">
                {a.flags.length === 0 && <li className="ok">No flags found.</li>}
                {a.flags.map((f, i) => (
                  <li key={i} className={f.level}>
                    <span className="lvl">{f.level}</span>{f.message}
                    {f.rule && <code>rule: {f.rule}</code>}
                    {f.code === 'DOCUMENT_CONTAINS_INSTRUCTIONS' && <em>Treated as data. The AI took no orders from it.</em>}
                  </li>
                ))}
              </ul>
            </article>
          )
        })}
      </div>
      <p className="fine"><span className="tape small">Sample data</span> The vendors and the vendor list are invented for the demo. In real use the official list comes from the national portal.</p>
    </div>
  )
}
