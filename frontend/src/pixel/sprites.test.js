import { describe, expect, it } from 'vitest'
import * as S from './sprites.js'

// A sprite is a grid of equal-length rows whose characters all exist in its palette.
const GRIDS = Object.entries(S).filter(([, v]) => Array.isArray(v) && typeof v[0] === 'string')

describe('pixel sprites', () => {
  it.each(GRIDS)('%s has equal-length rows', (name, grid) => {
    expect(new Set(grid.map((r) => r.length)).size).toBe(1)
  })
  it.each(Object.entries(S.ICONS))('icon %s is 8 x 8', (name, grid) => {
    expect(grid).toHaveLength(8)
    expect(grid.every((r) => r.length === 8)).toBe(true)
  })
  it('every agent palette covers its sprite', () => {
    const grids = { Secretary: S.SECRETARY, Reader: S.READER, Auditor: S.AUDITOR, Chaser: S.CHASER }
    for (const [name, grid] of Object.entries(grids)) {
      const used = new Set(grid.join('').replace(/\./g, ''))
      for (const ch of used) expect(S.PAL[name][ch], `${name} palette is missing '${ch}'`).toBeTruthy()
    }
  })
  it('asleep() closes the eyes without changing size', () => {
    const a = S.asleep(S.CHASER)
    expect(a).toHaveLength(S.CHASER.length)
    expect(a[7]).not.toContain('E')
  })
})
