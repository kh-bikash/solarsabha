import React, { useState } from 'react'
import { inr } from '../office/story.js'

export default function Fairness({ fairness, payback }) {
  const [model, setModel] = useState('equal')
  const k = model === 'equal' ? 'equal' : 'area'
  const first = fairness.flats[0]
  return (
    <div className="folder-body">
      <div className="fair-top">
        <div className="seg" role="tablist">
          {fairness.models.map((m) => (
            <button key={m} role="tab" aria-selected={m === model} className={m === model ? 'on' : ''} onClick={() => setModel(m)}>
              {m === 'equal' ? 'Equal split' : 'By flat area'}
            </button>
          ))}
        </div>
        <p className="lede">
          {model === 'equal'
            ? <>Every flat pays <b>{inr(first.equal_cost)}</b> once and saves <b>{inr(first.equal_saving_year)}</b> a year. Back in about {payback} years.</>
            : <>Bigger flats pay more and save more. A {first.area_sqft} sq ft flat pays <b>{inr(first.area_cost)}</b>.</>}
        </p>
      </div>
      <table className="ledger">
        <thead><tr><th>Flat</th><th>Area</th><th>Pays once</th><th>Saves a year</th></tr></thead>
        <tbody>
          {fairness.flats.map((f) => (
            <tr key={f.flat}><td>{f.flat}</td><td>{f.area_sqft} sq ft</td><td>{inr(f[k + '_cost'])}</td><td>{inr(f[k + '_saving_year'])}</td></tr>
          ))}
        </tbody>
      </table>
      <p className="fine">{fairness.note}</p>
    </div>
  )
}
