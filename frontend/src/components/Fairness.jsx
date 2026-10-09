import React, { useState } from 'react'
import { inr } from '../office/story.js'
import { Empty } from './ui.jsx'

export default function Fairness({ fairness, payback, goTo }) {
  const [model, setModel] = useState('equal')
  if (!fairness) {
    return <div className="folder-body"><Empty title="Nothing to share yet">Once there is a plan, this shows what each flat pays and saves.</Empty></div>
  }
  const k = model === 'equal' ? 'equal' : 'area'
  const eq = fairness.equal_per_flat
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
            ? <>Each of the {fairness.total_flats} flats pays <b>{inr(eq.cost)}</b> once and saves <b>{inr(eq.saving_year)}</b> a year. Back in about {payback} years.</>
            : <>Bigger flats pay more and save more. A {first.area_sqft} sq ft flat pays <b>{inr(first.area_cost)}</b>.</>}
        </p>
      </div>
      {fairness.flats.length > 0 ? (
        <table className="ledger">
          <thead><tr><th>Flat</th><th>Area</th><th>Pays once</th><th>Saves a year</th></tr></thead>
          <tbody>
            {fairness.flats.map((f) => (
              <tr key={f.flat}><td>{f.flat}</td><td>{f.area_sqft} sq ft</td><td>{inr(f[k + '_cost'])}</td><td>{inr(f[k + '_saving_year'])}</td></tr>
            ))}
          </tbody>
        </table>
      ) : (
        <Empty title="Add flat areas to compare" action={<button className="btn ghost" onClick={() => goTo('docs')}>Add flat areas</button>}>
          The equal split above needs only the number of flats. To compare a split by flat area, add each flat's area.
        </Empty>
      )}
      <p className="fine">{fairness.note}</p>
    </div>
  )
}
