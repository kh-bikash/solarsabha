import React, { useState } from 'react'
import { inr, lakh } from '../office/story.js'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const monthName = (m) => { const [y, mo] = m.split('-'); return `${MONTHS[+mo - 1]} ${y.slice(2)}` }

// What the Reader pulled out of the 12 common-area bills. One series, so no legend; the unclear month
// carries a hatch and a text label, not just a colour.
function BillsChart({ bills }) {
  const [hover, setHover] = useState(null)
  const W = 520, H = 170, L = 40, B = 24, T = 14
  const max = Math.ceil(Math.max(...bills.map((b) => b.units_kwh)) / 1000) * 1000
  const step = (W - L - 6) / bills.length, bw = step - 6
  const y = (v) => T + (H - T - B) * (1 - v / max)
  const ticks = [0, max / 2, max]
  return (
    <figure className="chart">
      <figcaption>Units on the common meter, per month <span className="muted">kWh · read by the Reader</span></figcaption>
      <div className="chart-wrap" onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Monthly common-area units, 12 bills">
          <defs>
            <pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="5" height="5" fill="#f7d9c2" /><rect width="2" height="5" fill="#ef6a1a" />
            </pattern>
          </defs>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={L} x2={W - 4} y1={y(t)} y2={y(t)} stroke={t === 0 ? '#b9ad96' : '#e7dfcf'} strokeWidth="1" />
              <text x={L - 6} y={y(t) + 3.5} textAnchor="end" className="tick">{t ? (t / 1000) + 'k' : '0'}</text>
            </g>
          ))}
          {bills.map((b, i) => {
            const x = L + 4 + i * step, top = y(b.units_kwh), h = y(0) - top
            return (
              <g key={b.month} onMouseEnter={() => setHover(i)}>
                <rect x={x - 3} y={T} width={step} height={H - T - B} fill="transparent" />
                <path d={`M${x},${y(0)} V${top + 4} q0,-4 4,-4 h${bw - 8} q4,0 4,4 V${y(0)} Z`}
                  fill={b.unclear ? 'url(#hatch)' : '#157a74'} opacity={hover == null || hover === i ? 1 : 0.55} />
                {b.unclear && <text x={x + bw / 2} y={top - 5} textAnchor="middle" className="flagtxt">unsure</text>}
                {i % 2 === 0 && <text x={x + bw / 2} y={H - 8} textAnchor="middle" className="tick">{monthName(b.month)}</text>}
              </g>
            )
          })}
        </svg>
        {hover != null && (
          <div className="tip" style={{ left: `${((L + 4 + hover * step + bw / 2) / W) * 100}%` }}>
            <b>{monthName(bills[hover].month)}</b>
            <span>{bills[hover].units_kwh.toLocaleString('en-IN')} kWh</span>
            {bills[hover].amount_inr && <span>{inr(bills[hover].amount_inr)} bill</span>}
            {bills[hover].unclear && <em>Reader was not sure. Committee to confirm.</em>}
          </div>
        )}
      </div>
    </figure>
  )
}

export default function PlanCard({ r }) {
  const m = r.recommended, a = m.assumptions, v2 = r.plan_v2
  return (
    <div className="folder-body plan">
      <div className="plan-left">
        {r.bills && <BillsChart bills={r.bills} />}
        <div className="opts">
          {r.plan.options.map((o) => {
            const mm = r.money[o.label]
            return (
              <div key={o.label} className={'opt' + (o.label === 'recommended' ? ' rec' : '')}>
                <span className="opt-l">{o.label}</span>
                <b>{mm.kw} kW</b>
                <span>covers {Math.round(o.share_of_load * 100)}% of use</span>
                <span>pays {lakh(mm.net_cost)}</span>
              </div>
            )
          })}
        </div>
      </div>
      <div className="plan-right">
        <div className="hero-row">
          <div className="hero"><b>{m.kw}<small> kW</small></b><span>sized from the society's real use</span></div>
          <div className="hero"><b>{lakh(m.net_cost).replace('Rs ', '₹')}</b><span>society pays after a {lakh(m.subsidy)} subsidy</span></div>
          <div className="hero"><b>{m.payback_years}<small> yrs</small></b><span>simple payback</span></div>
          <div className="hero"><b>{m.co2_tonnes_year}<small> t</small></b><span>CO₂ avoided a year</span></div>
        </div>
        <p className="fine">The subsidy ceiling is {r.plan.subsidy_ceiling_kw} kW ({r.society.flats} flats × 3 kW). That is a limit, not a target.</p>
        {v2 && (
          <div className="v2">
            <span className="tape">Plan v2</span>
            <p><b>{m.kw} kW → {v2.plan.recommended_kw} kW</b> because of a {v2.reason}.</p>
            <p>Society now pays {lakh(v2.money.net_cost)}, payback {v2.money.payback_years} yrs, {v2.money.co2_tonnes_year} t CO₂ a year.</p>
          </div>
        )}
        <div className="sticky">
          <b>Assumptions</b>
          <span>Cost {inr(a.cost_per_kw)} per kW · tariff Rs {a.tariff} a unit · {a.yield_kwh_per_kw} kWh per kW a year.</span>
          <span>{a.caveat}</span>
        </div>
      </div>
    </div>
  )
}
