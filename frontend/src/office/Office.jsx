import React from 'react'
import { Sprite } from '../pixel/Sprite.jsx'
import * as P from '../pixel/sprites.js'
import { AGENT_COLOR } from './story.js'

// The SolarSabha office: a pixel-art view of the same trace events the logbook lists.
// Logical canvas is 320 x 200; HTML overlays (labels, bubbles) are positioned in % of it.
const VW = 320, VH = 200
const at = (x, y) => ({ left: `${(x / VW) * 100}%`, top: `${(y / VH) * 100}%` })

const DESKS = {
  Secretary: { x: 142, y: 40, deskY: 56, deskX: 122, deskW: 56, mon: [128, 43], screen: 'chart', label: [150, 73], head: [150, 39], folder: 'plan',
    role: 'Coordinator', lines: ['Talks to the committee', 'Calls the specialists'] },
  Reader: { x: 22, y: 92, deskY: 108, deskX: 8, deskW: 60, mon: [44, 95], screen: 'doc', label: [38, 126], head: [30, 91], folder: 'plan',
    role: 'Reads bills + quotes', lines: ['PDFs and photos', 'Flags what is unclear'] },
  Auditor: { x: 94, y: 92, deskY: 108, deskX: 80, deskW: 60, mon: [116, 95], screen: 'audit', label: [110, 126], head: [102, 91], folder: 'quotes',
    role: 'Checks quotes', lines: ['Red, amber, green', 'Ignores hidden orders'] },
  Chaser: { x: 166, y: 92, deskY: 108, deskX: 152, deskW: 60, mon: [188, 95], screen: 'cal', label: [182, 126], head: [174, 91], folder: 'timeline',
    role: 'Follows up', lines: ['Tracks the DISCOM', 'Drafts the chasers'] },
}
const GRIDS = { Secretary: P.SECRETARY, Reader: P.READER, Auditor: P.AUDITOR, Chaser: P.CHASER }
const OBJ_AT = { calc: [167, 45], cabinet: [91, 41], room: [268, 92], calendar: [78, 22], bills: [24, 99] }
const FLIGHT_FROM = { Secretary: [150, 50], Chaser: [182, 100], Reader: [38, 100], Auditor: [110, 100] }
const INBOX = [155, 165]
const VERDICT = { GREEN: '#2f8a3e', AMBER: '#c98a00', RED: '#c63a2b' }

export default function Office({ r, current, board, phase, dayShown, draftsWaiting, agmPinned, flights, envelope, chaserAsleep, onPick, roomPrices }) {
  const night = phase === 'night'
  const active = current?.agent
  const hotObj = current?.object
  return (
    <div className={'scene' + (night ? ' is-night' : '')}>
      <svg viewBox={`0 0 ${VW} ${VH}`} shapeRendering="crispEdges" role="img"
        aria-label="Pixel-art office: the Sabha Secretary, Reader, Auditor and Chaser at their desks, the committee in front.">
        <Room night={night} dayShown={dayShown} board={board} hotObj={hotObj} phase={phase} />
        {Object.entries(DESKS).map(([name, d]) => {
          const asleep = night || (name === 'Chaser' && chaserAsleep)
          const state = active === name ? 'working' : asleep ? 'asleep' : 'idle'
          return <DeskStation key={name} name={name} d={d} state={state} night={night} hotObj={hotObj} onPick={onPick} />
        })}
        <NegotiationRoom r={r} hot={hotObj === 'room'} roomPrices={roomPrices} onPick={onPick} />
        <Foreground draftsWaiting={draftsWaiting} agmPinned={agmPinned} onPick={onPick} />
        <rect className="night-veil" x="0" y="0" width={VW} height={VH} fill="#0b1230" />
        <Lamps night={night} />
      </svg>

      {/* desk labels */}
      {Object.entries(DESKS).map(([name, d]) => (
        <button key={name} className="dlabel" style={{ ...at(...d.label), '--c': AGENT_COLOR[name] }} onClick={() => onPick(d.folder)}>
          <b>{name === 'Secretary' ? 'Sabha Secretary' : name}</b>
          <span>{d.role}</span>
          <p>{d.lines[0]}<br />{d.lines[1]}</p>
        </button>
      ))}
      <button className="dlabel committee" style={at(186, 178)} onClick={() => onPick('desk')}>
        <b>Committee · you</b>
        <span>{draftsWaiting ? `${draftsWaiting} draft${draftsWaiting > 1 ? 's' : ''} need you` : 'Nothing waiting'}</span>
      </button>
      <span className="tape room-tape" style={at(268, 79)}>Negotiation room · simulation</span>

      {/* speech bubble for whoever is working */}
      {current && (
        <div key={current.key} className={'bubble' + (current.agent === 'Reader' ? ' left' : '')}
          style={{ ...at(...DESKS[current.agent].head), '--c': AGENT_COLOR[current.agent] }}>
          <div className="bub-head"><span>{current.agent}</span>{current.tool && <code>{current.tool}()</code>}</div>
          <p>{current.text}</p>
        </div>
      )}
      {current?.code && hotObj && OBJ_AT[hotObj] && <span key={'t' + current.key} className="codetag" style={at(...OBJ_AT[hotObj])}>plain code</span>}

      {/* sleeping and waking */}
      {Object.entries(DESKS).map(([name, d]) => ((night || (name === 'Chaser' && chaserAsleep)) && active !== name
        ? <span key={'z' + name} className="zzz" style={at(d.head[0] + 6, d.head[1] + 2)}>z<i>z</i><i>z</i></span> : null))}
      {phase === 'ring' && <span className="ring" style={at(78, 6)}>RING! Day {dayShown}</span>}
      {night && <div className="night-card">Time machine · simulated clock<b>Day {dayShown}</b><span>The agents saved their notes and went to sleep. An alarm wakes the Chaser.</span></div>}

      {/* papers flying to the committee's inbox, and the DISCOM's letter flying in */}
      {flights.map((f) => {
        const [x1, y1] = f.from === 'room' ? [268, 110] : FLIGHT_FROM[f.from] || [150, 60]
        return <span key={f.id} className="flight" style={{ ...at(x1, y1), '--dx': `${((INBOX[0] - x1) / VW) * 100}cqw`, '--dy': `${((INBOX[1] - y1) / VW) * 100}cqw` }} />
      })}
      {envelope && <span className="flight letter" style={{ ...at(34, 28), '--dx': `${((182 - 34) / VW) * 100}cqw`, '--dy': `${((100 - 28) / VW) * 100}cqw` }} />}
    </div>
  )
}

function Room({ night, dayShown, board, hotObj, phase }) {
  const tiles = []
  for (let y = 73, row = 0; y < VH; y += 12, row++) for (let x = 0, col = 0; x < VW; x += 20, col++)
    tiles.push(<rect key={x + '-' + y} x={x} y={y} width={20} height={12} fill={(row + col) % 2 ? '#d6c9ad' : '#cfc1a3'} />)
  return (
    <g>
      {/* wall */}
      <rect x="0" y="0" width={VW} height="73" fill="#e8d9bb" />
      <rect x="0" y="54" width={VW} height="17" fill="#d6c29d" />
      <rect x="0" y="54" width={VW} height="1" fill="#bba47c" />
      <rect x="0" y="70" width={VW} height="3" fill="#7a5a3a" />
      {tiles}
      {!night && <polygon points="8,73 62,73 96,118 28,118" fill="#fff4d2" opacity=".35" />}

      {/* window with the society building and its solar roof */}
      <rect x="4" y="5" width="62" height="45" fill="#8d969b" />
      <rect x="6" y="7" width="58" height="41" fill={night ? '#1a2346' : '#3f9fe3'} />
      {!night && <>
        <rect x="6" y="20" width="58" height="10" fill="#6db7ea" />
        <rect x="6" y="30" width="58" height="18" fill="#a9d6f3" />
        {[[9, 11, 9], [24, 15, 12], [40, 22, 8]].map(([x, y, w]) => (
          <g key={x} className="cloud">
            <rect x={x + 2} y={y - 2} width={w - 4} height="2" fill="#ffffff" />
            <rect x={x} y={y} width={w} height="2" fill="#ffffff" />
            <rect x={x + 1} y={y + 2} width={w - 2} height="1" fill="#d9ecf8" />
          </g>
        ))}
      </>}
      {night ? <>
        <Sprite grid={P.MOON} pal={{ Y: '#f3e9b5' }} x={50} y={10} />
        {[[12, 11], [24, 16], [40, 9], [30, 24], [58, 22]].map(([x, y]) => <rect key={x} x={x} y={y} width="1" height="1" fill="#f3e9b5" />)}
      </> : <Sprite grid={P.SUN} pal={{ Y: '#ffd34d' }} x={50} y={10} />}
      {[[36, 30, 8, 18], [46, 26, 7, 22], [55, 33, 9, 15], [7, 34, 6, 14]].map(([x, y, w, h]) =>
        <rect key={x} x={x} y={y} width={w} height={h} fill={night ? '#2b3558' : '#8aa2b8'} />)}
      <rect x="14" y="22" width="19" height="26" fill={night ? '#3d3a4a' : '#efe1c4'} />
      {[0, 1, 2, 3].map((r) => [0, 1, 2].map((c) =>
        <rect key={r + '' + c} x={16 + c * 6} y={25 + r * 6} width="3" height="3" fill={night ? ((r + c) % 2 ? '#ffd66b' : '#2b2a36') : '#c7b28b'} />))}
      <rect x="13" y="19" width="21" height="3" fill={night ? '#1d3157' : '#2f6db5'} />
      {[16, 20, 24, 28].map((x) => <rect key={x} x={x} y="19" width="1" height="3" fill={night ? '#2a426e' : '#7fb0e6'} />)}
      {!night && <rect x="30" y="19" width="2" height="1" fill="#ffffff" className="glint" />}
      <rect x="35" y="7" width="1" height="41" fill="#8d969b" />
      <rect x="2" y="50" width="66" height="3" fill="#b8c0c4" />

      {/* clock and calendar */}
      <Sprite grid={P.CLOCK} pal={P.PAL_CLOCK} x={72} y={7} />
      <g className={'clock-hands' + (phase === 'night' ? ' spin' : '')}>
        <rect x="77" y="9" width="1" height="4" fill="#c63a2b" />
        <rect x="77" y="12" width="3" height="1" fill="#2b2f36" />
      </g>
      <g className={'obj' + (hotObj === 'calendar' ? ' hot' : '')}>
        <rect x="69" y="21" width="18" height="21" fill="#fbf8f1" />
        <rect x="69" y="21" width="18" height="5" fill="#c63a2b" />
        <text x="78" y="25.2" textAnchor="middle" fontSize="3.6" fill="#fbf8f1" className="px">DAY</text>
        <text x="78" y="37.5" textAnchor="middle" fontSize="10" fill="#161412" className="px b">{dayShown}</text>
      </g>

      {/* name plaque */}
      <rect x="102" y="5" width="96" height="19" fill="#1f2a44" />
      <rect x="103" y="6" width="94" height="1" fill="#33456b" />
      <text x="150" y="16" textAnchor="middle" fontSize="7" textLength="84" lengthAdjust="spacingAndGlyphs" fill="#fbf8f1" className="px b">SOLARSABHA &amp; CO.</text>
      <text x="150" y="21.6" textAnchor="middle" fontSize="3.4" textLength="74" lengthAdjust="spacingAndGlyphs" fill="#f2a65a" className="px">SOCIETY SOLAR OFFICE · EST. 2026</text>

      {/* the Secretary's glass cabin */}
      <rect x="112" y="27" width="76" height="2" fill="#8d969b" />
      <rect x="112" y="27" width="2" height="44" fill="#8d969b" />
      <rect x="186" y="27" width="2" height="44" fill="#8d969b" />

      {/* rulebook cabinet */}
      <g className={'obj' + (hotObj === 'cabinet' ? ' hot' : '')}>
        <rect x="88" y="44" width="18" height="27" fill="#7f8c92" />
        <rect x="88" y="44" width="18" height="1" fill="#a9b4b9" />
        {[47, 55, 63].map((y) => <g key={y}><rect x="90" y={y} width="14" height="7" fill="#6f7b80" /><rect x="94" y={y + 1} width="6" height="2" fill="#f3efe6" /><rect x="96" y={y + 4} width="2" height="1" fill="#d2d9dc" /></g>)}
        <text x="97" y="48.6" textAnchor="middle" fontSize="1.9" fill="#161412" className="px">RULES</text>
      </g>
      <Sprite grid={P.PLANT} pal={P.PAL_PLANT} x={91} y={33} s={0.95} />

      {/* poster */}
      <rect x="196" y="8" width="25" height="32" fill="#f7f1e3" />
      <rect x="196" y="8" width="25" height="1" fill="#ef6a1a" />
      {['CODE', 'DOES', 'THE', 'MATHS.'].map((t, i) => <text key={t} x="198.5" y={16 + i * 5.4} fontSize="4.6" fill="#161412" className="px b">{t}</text>)}
      <rect x="198" y="36" width="15" height="1" fill="#ef6a1a" />

      {/* whiteboard */}
      <rect x="228" y="5" width="86" height="47" fill="#9aa3a8" />
      <rect x="230" y="7" width="82" height="43" fill="#fbfbf7" />
      <text x="234" y="14.5" fontSize="5.2" fill="#161412" className="px b">THE FIVE JOBS</text>
      <rect x="234" y="16" width="36" height="1" fill="#ef6a1a" />
      {board.map((it, i) => (
        <g key={i}>
          <rect x="234" y={20 + i * 6} width="4" height="4" fill="#161412" />
          <rect x="235" y={21 + i * 6} width="2" height="2" fill="#fbfbf7" />
          {it.done && <g className="tick"><rect x="235" y={22 + i * 6} width="1" height="1" fill="#ef6a1a" /><rect x="236" y={23 + i * 6} width="1" height="1" fill="#ef6a1a" /><rect x="237" y={20 + i * 6} width="1" height="3" fill="#ef6a1a" /><rect x="238" y={19 + i * 6} width="1" height="2" fill="#ef6a1a" /></g>}
          <text x="241" y={23.4 + i * 6} fontSize="3.7" fill={it.done ? '#7b7366' : '#161412'} className="px">{it.label}</text>
        </g>
      ))}
      <rect x="232" y="50" width="40" height="2" fill="#7f8a8f" />

      {/* water cooler */}
      <rect x="300" y="54" width="10" height="7" fill="#9fd0ea" />
      <rect x="301" y="54" width="2" height="7" fill="#c9e7f5" />
      <rect x="298" y="61" width="14" height="10" fill="#e6eaec" />
      <rect x="302" y="64" width="2" height="2" fill="#2d6cc0" />
      <Sprite grid={P.PLANT} pal={P.PAL_PLANT} x={66} y={58} />
    </g>
  )
}

function Monitor({ x, y, kind, state, night }) {
  const on = state === 'working'
  const glass = on ? '#dff5ef' : state === 'asleep' ? '#121820' : night ? '#1c2c35' : '#3f5d66'
  const ink = on ? '#4c7c84' : '#5f7f87'
  return (
    <g className={'monitor' + (on ? ' on' : '')}>
      {night && state !== 'asleep' && <ellipse cx={x + 7} cy={y + 5} rx="12" ry="9" fill="#9fe8d8" opacity=".18" />}
      <rect x={x} y={y} width="14" height="10" fill="#22262c" />
      <rect x={x + 1} y={y + 1} width="12" height="8" fill={glass} />
      {state !== 'asleep' && kind === 'doc' && [[2, 8], [4, 10], [6, 6]].map(([dy, w]) => <rect key={dy} x={x + 2} y={y + dy} width={w} height="1" fill={ink} />)}
      {state !== 'asleep' && kind === 'audit' && [['#2f8a3e', 9], ['#c98a00', 6], ['#c63a2b', 8]].map(([c, w], i) => <rect key={i} x={x + 2} y={y + 2 + i * 2} width={w} height="1" fill={c} />)}
      {state !== 'asleep' && kind === 'cal' && [0, 1, 2].map((r) => [0, 1, 2, 3].map((c) => <rect key={r + '' + c} x={x + 2 + c * 3} y={y + 2 + r * 2} width="2" height="1" fill={r === 1 && c === 2 ? '#c63a2b' : ink} />))}
      {state !== 'asleep' && kind === 'chart' && [[2, 3], [5, 5], [8, 2], [11, 0]].map(([dx, h]) => <rect key={dx} x={x + dx} y={y + 3 + h} width="2" height={5 - h} fill="#ef6a1a" />)}
      <rect x={x + 6} y={y + 10} width="2" height="2" fill="#22262c" />
      <rect x={x + 4} y={y + 12} width="6" height="1" fill="#22262c" />
    </g>
  )
}

function Desk({ x, y, w, h }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height="3" fill="#c08a52" />
      <rect x={x} y={y} width={w} height="1" fill="#dba66c" />
      <rect x={x + 2} y={y + 3} width={w - 4} height={h} fill="#8b5a2f" />
      <rect x={x + 2} y={y + 3} width={w - 4} height="1" fill="#6b4322" />
      <rect x={x + w - 20} y={y + 5} width="15" height={Math.floor(h / 2) - 1} fill="#9a6838" />
      <rect x={x + w - 14} y={y + 6} width="3" height="1" fill="#e2c08d" />
      <rect x={x + w - 20} y={y + 5 + Math.floor(h / 2)} width="15" height={Math.floor(h / 2) - 3} fill="#9a6838" />
      <rect x={x + w - 14} y={y + 6 + Math.floor(h / 2)} width="3" height="1" fill="#e2c08d" />
    </g>
  )
}

function DeskStation({ name, d, state, night, hotObj, onPick }) {
  const pal = P.PAL[name]
  const grid = state === 'asleep' ? P.asleep(GRIDS[name]) : GRIDS[name]
  const h = name === 'Secretary' ? 12 : 13
  return (
    <g className={'station ' + state} onClick={() => onPick(d.folder)} style={{ cursor: 'pointer' }}>
      <g className="body"><Sprite grid={grid} pal={pal} x={d.x} y={d.y} /></g>
      <Desk x={d.deskX} y={d.deskY} w={d.deskW} h={h} />
      <Monitor x={d.mon[0]} y={d.mon[1]} kind={d.screen} state={state} night={night} />
      {state === 'working' && <g className="hands">
        <rect className="hand l" x={d.x + 3} y={d.deskY - 1} width="3" height="2" fill={pal.S} />
        <rect className="hand r" x={d.x + 10} y={d.deskY - 1} width="3" height="2" fill={pal.S} />
      </g>}
      {name === 'Secretary' && <g className={'obj' + (hotObj === 'calc' ? ' hot' : '')}>
        <rect x="160" y="50" width="12" height="6" fill="#d9d4c7" />
        <rect x="160" y="50" width="12" height="1" fill="#efeadf" />
        {[0, 1, 2, 3].map((c) => <rect key={c} x={161 + c * 3} y="53" width="2" height="1" fill="#4a443d" />)}
        <rect className="tape-roll" x="163" y="44" width="5" height="6" fill="#fbf8f1" />
        <rect x="164" y="46" width="3" height="1" fill="#b9b1a3" />
      </g>}
      {name === 'Reader' && <g className={'obj' + (hotObj === 'bills' ? ' hot' : '')}>
        {[0, 1, 2, 3].map((i) => <rect key={i} x={10 + (i % 2)} y={103 - i * 1.5} width="10" height="2" fill={i === 3 ? '#fbf8f1' : '#e9e2d3'} />)}
        <rect x="12" y="99" width="6" height="1" fill="#c9c2b4" />
      </g>}
      {name === 'Chaser' && <g>
        <rect x="155" y="104" width="9" height="4" fill="#2b2f36" />
        <rect x="156" y="103" width="7" height="1" fill="#3e444d" />
      </g>}
      {name === 'Auditor' && <g>
        <rect x="83" y="104" width="8" height="4" fill="#fbf8f1" />
        <rect x="84" y="105" width="5" height="1" fill="#c63a2b" />
      </g>}
    </g>
  )
}

function NegotiationRoom({ r, hot, roomPrices, onPick }) {
  const seats = [[242, 104], [264, 100], [286, 104]]
  return (
    <g className={'obj room' + (hot ? ' hot' : '')} onClick={() => onPick('room')} style={{ cursor: 'pointer' }}>
      <rect x="222" y="84" width="92" height="74" fill="#b9c6c2" />
      {[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x="222" y={88 + i * 12} width="92" height="1" fill="#adbbb7" />)}
      {r.audits.map((a, i) => (
        <Sprite key={a.vendor} grid={P.BUST} pal={{ H: ['#2a1e18', '#5a3b22', '#1c1512'][i], S: '#d29a70', E: '#1d1a17', W: VERDICT[a.verdict] }} x={seats[i][0] - 4} y={seats[i][1]} />
      ))}
      <ellipse cx="268" cy="121" rx="25" ry="8" fill="#9a6a3c" />
      <ellipse cx="268" cy="120" rx="24" ry="7" fill="#c48c55" />
      <Sprite grid={P.BUST} pal={{ H: '#1f1713', S: '#1f1713', E: '#1f1713', W: '#ef6a1a' }} x={264} y={126} />
      <rect x="220" y="80" width="96" height="3" fill="#8d969b" />
      <rect x="220" y="80" width="2" height="80" fill="#8d969b" />
      <rect x="314" y="80" width="2" height="80" fill="#8d969b" />
      <rect x="220" y="157" width="96" height="2" fill="#8d969b" />
      <rect x="222" y="83" width="92" height="74" fill="#dff1f6" opacity=".22" />
      {roomPrices.map((p, i) => p && (
        <g key={i}>
          <rect x={seats[i][0] - 11} y={seats[i][1] - 8} width="22" height="6" fill="#fbf8f1" />
          <rect x={seats[i][0] - 11} y={seats[i][1] - 8} width="1" height="6" fill={VERDICT[r.audits[i].verdict]} />
          <text x={seats[i][0] + 0.5} y={seats[i][1] - 3.6} textAnchor="middle" fontSize="3.6" fill="#161412" className="px b">{p}</text>
        </g>
      ))}
    </g>
  )
}

function Foreground({ draftsWaiting, agmPinned, onPick }) {
  const sheets = Math.min(draftsWaiting, 8)
  return (
    <g>
      {/* the society notice board; the solar AGM notice is pinned once a person approves it */}
      <g onClick={() => onPick('desk')} style={{ cursor: 'pointer' }}>
        <rect x="238" y="163" width="76" height="34" fill="#6e4526" />
        <rect x="240" y="168" width="72" height="27" fill="#c19160" />
        <text x="276" y="167" textAnchor="middle" fontSize="3.4" fill="#f3e2c4" className="px b">NOTICE BOARD</text>
        <rect x="244" y="171" width="18" height="13" fill="#fbf8f1" />
        <text x="246" y="176" fontSize="2.6" fill="#161412" className="px">LIFT</text>
        <text x="246" y="179.5" fontSize="2.6" fill="#161412" className="px">SERVICE</text>
        <rect x="246" y="181" width="12" height="1" fill="#b9b1a3" />
        <rect x="252" y="170" width="2" height="2" fill="#c63a2b" />
        <rect x="265" y="175" width="16" height="12" fill="#fbe8a6" />
        <text x="267" y="180" fontSize="2.6" fill="#161412" className="px">TANK</text>
        <text x="267" y="183.5" fontSize="2.6" fill="#161412" className="px">CLEANING</text>
        <rect x="272" y="174" width="2" height="2" fill="#2d6cc0" />
        {agmPinned ? (
          <g className="pinned">
            <rect x="285" y="170" width="23" height="21" fill="#ffffff" />
            <rect x="285" y="170" width="23" height="3" fill="#ef6a1a" />
            <text x="287" y="177.5" fontSize="2.8" fill="#161412" className="px b">SOLAR AGM</text>
            <text x="287" y="181.5" fontSize="2.4" fill="#4a443d" className="px">{agmPinned} kW ROOF</text>
            <rect x="287" y="184" width="16" height="1" fill="#b9b1a3" />
            <rect x="287" y="186.5" width="12" height="1" fill="#b9b1a3" />
            <rect x="295" y="169" width="2" height="2" fill="#c63a2b" />
          </g>
        ) : <rect x="285" y="170" width="23" height="21" fill="none" stroke="#9c7346" strokeWidth=".6" strokeDasharray="1.5 1.5" />}
      </g>

      {/* the committee's desk */}
      <g onClick={() => onPick('desk')} style={{ cursor: 'pointer' }}>
        <rect x="0" y="172" width="216" height="28" fill="#6e4526" />
        <rect x="0" y="172" width="216" height="2" fill="#93603a" />
        <Sprite grid={P.PLANT} pal={P.PAL_PLANT} x={2} y={160} />
        <Sprite grid={P.CHAI} pal={P.PAL_CHAI} x={34} y={167} />
        <g className="steam"><rect x="35" y="163" width="1" height="2" fill="#ffffff" /><rect x="37" y="161" width="1" height="2" fill="#ffffff" /></g>
        <rect x="56" y="156" width="28" height="17" fill="#3a3e45" />
        <rect x="57" y="157" width="26" height="1" fill="#4b5059" />
        <rect x="68" y="163" width="4" height="4" fill="#ef6a1a" />
        <rect x="52" y="172" width="36" height="2" fill="#2b2f36" />
        <Sprite grid={P.COMMITTEE_BACK} pal={P.PAL_COMMITTEE} x={96} y={162} s={1.75} />
        <rect x="142" y="166" width="26" height="7" fill="#b98f55" />
        <rect x="142" y="166" width="26" height="1" fill="#d6ad72" />
        {Array.from({ length: sheets }, (_, i) => <rect key={i} className="sheet" x={144 + (i % 2)} y={170 - i * 1.6} width="22" height="1.6" fill={i % 2 ? '#fbf8f1' : '#ebe4d6'} />)}
        <rect x="174" y="163" width="4" height="3" fill="#c63a2b" />
        <rect x="175" y="166" width="2" height="4" fill="#7a2a20" />
        <rect x="172" y="170" width="8" height="3" fill="#2b2f36" />
      </g>
    </g>
  )
}

function Lamps({ night }) {
  return (
    <g className="lamps" pointerEvents="none">
      {[94, 216].map((x) => (
        <g key={x}>
          {night && <polygon points={`${x - 3},6 ${x + 3},6 ${x + 26},70 ${x - 26},70`} fill="#ffd98a" opacity=".12" />}
          <rect x={x} y="0" width="1" height="3" fill="#2b2f36" />
          <rect x={x - 3} y="3" width="7" height="3" fill="#2b2f36" />
          <rect x={x - 2} y="6" width="5" height="1" fill={night ? '#ffe08a' : '#8a8f96'} />
        </g>
      ))}
    </g>
  )
}

