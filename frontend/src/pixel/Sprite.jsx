import React, { useMemo } from 'react'

// Renders a pixel grid (array of equal-length strings) as SVG rects. '.' is transparent; every other
// character is looked up in the palette. Horizontal runs of one colour merge into a single rect.
function toRects(grid, pal) {
  const out = []
  grid.forEach((row, y) => {
    let x = 0
    while (x < row.length) {
      const ch = row[x]
      let w = 1
      while (x + w < row.length && row[x + w] === ch) w++
      if (ch !== '.' && pal[ch]) out.push([x, y, w, pal[ch]])
      x += w
    }
  })
  return out
}

export function Sprite({ grid, pal, x = 0, y = 0, s = 1, className, ...rest }) {
  const rects = useMemo(() => toRects(grid, pal), [grid, pal])
  const t = `translate(${x} ${y})` + (s !== 1 ? ` scale(${s})` : '')
  return (
    <g transform={t} className={className} {...rest}>
      {rects.map(([rx, ry, w, c], i) => <rect key={i} x={rx} y={ry} width={w} height={1} fill={c} />)}
    </g>
  )
}

// Small standalone icon (for chips and buttons outside the office scene).
export function PixelIcon({ grid, pal, size = 18, className }) {
  return (
    <svg className={'picon ' + (className || '')} width={size} height={size} viewBox={`0 0 ${grid[0].length} ${grid.length}`} shapeRendering="crispEdges" aria-hidden="true">
      <Sprite grid={grid} pal={pal} />
    </svg>
  )
}
