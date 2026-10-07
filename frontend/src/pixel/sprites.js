// Pixel-art sprites for the SolarSabha office. Each sprite is an array of equal-length strings;
// '.' is transparent, every other character is a palette key. Drawn by <Sprite> in Sprite.jsx.

const SKIN = { S: '#e2a87c', s: '#c4875e', E: '#1d1a17', M: '#a2524a' }
const SKIN_DEEP = { S: '#b97a52', s: '#9a603d', E: '#1d1a17', M: '#7d3a33' }

// ---- seated agents (16 x 19, desk covers the bottom rows) ----
export const SECRETARY = [
  '....HHHHHHHH....',
  '...HHHHHHHHHH...',
  '..HHHHHHHHHHHH..',
  '..HHHHHHHHHHHH..',
  '..HHHHHHSSSSHH..',
  '..HSSSSSSSSSSH..',
  '..SSSSSSSSSSSS..',
  '..sSSESSSSESSs..',
  '..sSSESSSSESSs..',
  '...SSSSSSSSSS...',
  '...SSSSMMSSSS...',
  '....SSSSSSSS....',
  '......ssss......',
  '...WWWCTTCWWW...',
  '..WWWWCTTCWWWW..',
  '.WWWWWWTTWWWWWW.',
  '.WWWWWWTTWWWWWW.',
  '.wWWWWWWWWWWWWw.',
  '.wWWWWWWWWWWWWw.',
]
export const READER = [
  '....HHHHHHHH....',
  '...HHHHHHHHHH...',
  '..HHHHHHHHHHHH..',
  '..HHHHHHHHHHHH..',
  '..HHHSSSSSSHHH..',
  '..HHSSSSSSSSHH..',
  '..HSSSSSSSSSSH..',
  '..HSSESSSSESSH..',
  '..HSSESSSSESSH..',
  '..HSSSSSSSSSSH..',
  '..HHSSSMMSSSHH..',
  '..HHHSSSSSSHHH..',
  '..HHHHssssHHHH..',
  '..HHWWWTTWWWHH..',
  '.WHHWWWWWWWWHHW.',
  '.WWWWWWWWWWWWWW.',
  '.WWWWWWWWWWWWWW.',
  '.wWWWWWWWWWWWWw.',
  '.wWWWWWWWWWWWWw.',
]
export const AUDITOR = [
  '....HHHHHHHH....',
  '...HHHHHHHHHH...',
  '..HHHHHHHHHHHH..',
  '..HHHHHHHHHHHH..',
  '..HHSSSSSSSSHH..',
  '..HSSSSSSSSSSH..',
  '..SSGGGSSGGGSS..',
  '..sSGEGSSGEGSs..',
  '..sSGGGSSGGGSs..',
  '...SSSSSSSSSS...',
  '...HSSSMMSSSH...',
  '....HHHHHHHH....',
  '......ssss......',
  '...WWWCWWCWWW...',
  '..WWWWWWWWWWWW..',
  '.WWWWWWWWWWWWWW.',
  '.WWWWWWWWWWWWWW.',
  '.wWWWWWWWWWWWWw.',
  '.wWWWWWWWWWWWWw.',
]
export const CHASER = [
  '....HHHHHHHH....',
  '...HKKKKKKKKH...',
  '..KHHHHHHHHHHK..',
  '..KHHHHHHHHHHK..',
  '..KHSSSSSSSSHK..',
  '..KSSSSSSSSSSK..',
  '.KKSSSSSSSSSSKK.',
  '.KKSSESSSSESSKK.',
  '.KKSSESSSSESSKK.',
  '...SSSSSSSSSS.K.',
  '...SSSSMMSSSSK..',
  '....SSSSSSSS....',
  '......ssss......',
  '...WWWTWWTWWW...',
  '..WWWWTWWTWWWW..',
  '.WWWWWWWWWWWWWW.',
  '.WWWWWWWWWWWWWW.',
  '.wWWWWWWWWWWWWw.',
  '.wWWWWWWWWWWWWw.',
]
// eyes shut: drop the upper eye row so only a low line remains
export const asleep = (grid) => grid.map((r, i) => (i === 7 ? r.replace(/E/g, 'S') : r))

export const PAL = {
  Secretary: { ...SKIN, H: '#2b211c', W: '#24324f', w: '#18223a', C: '#f3efe6', T: '#ef6a1a' },
  Reader: { ...SKIN_DEEP, H: '#1c1512', W: '#157a74', w: '#0f5c57', T: '#e9b949' },
  Auditor: { ...SKIN, H: '#4a3426', W: '#7a4a9a', w: '#5c3577', C: '#f3efe6', G: '#2a2a2a' },
  Chaser: { ...SKIN_DEEP, H: '#2a1e18', K: '#2b2f36', W: '#2d6cc0', w: '#1f4f91', T: '#f3efe6' },
}

// ---- the committee member, seen from behind (foreground) ----
export const COMMITTEE_BACK = [
  '.......HHHHHH.......',
  '.....HHHHHHHHHH.....',
  '....HHHHhhhHHHHH....',
  '...HHHhhhKKHHHHHH...',
  '...HHhhHHHHHHHHHH...',
  '...HHhHHHHHHHHHHH...',
  '...sHHHHHHHHHHHHs...',
  '....HHHHHHHHHHHH....',
  '....HHHHHHHHHHHH....',
  '.....HHHHHHHHHH.....',
  '...WWHHHHHHHHHHWW...',
  '.WWWWHHHHHHHHHHWWWW.',
  'WWWWWWHHHHHHHHWWWWWW',
  'WWWWWWWHHHHHHWWWWWWW',
  'WWWWWWWWWWWWWWWWWWWW',
  'wWWWWWWWWWWWWWWWWWWw',
  'wWWWWWWWWWWWWWWWWWWw',
  'wWWWWWWWWWWWWWWWWWWw',
  'wWWWWWWWWWWWWWWWWWWw',
  'wWWWWWWWWWWWWWWWWWWw',
  'wWWWWWWWWWWWWWWWWWWw',
  'wWWWWWWWWWWWWWWWWWWw',
]
export const PAL_COMMITTEE = { h: '#5a4334', H: '#2e2119', K: '#ef6a1a', s: '#b97a52', W: '#c96a3a', w: '#a8552b' }

// ---- small busts for the negotiation room (8 x 9) ----
export const BUST = [
  '..HHHH..',
  '.HHHHHH.',
  '.HSSSSH.',
  '.SESSES.',
  '.SSSSSS.',
  '..SSSS..',
  '.WWWWWW.',
  'WWWWWWWW',
  'WWWWWWWW',
]

// ---- props ----
export const PLANT = [
  '....g..G....',
  '...gG.GGg...',
  '.G.gGGGg.g..',
  'gGG.GGG.GGg.',
  '.gGGgGGgGG..',
  '..gGGGGGg.G.',
  '.GgG.GG.GGg.',
  '..g.GGGG.g..',
  '....gGGg....',
  '..PPPPPPPP..',
  '..pPPPPPPp..',
  '...PPPPPP...',
  '...pPPPPp...',
]
export const PAL_PLANT = { G: '#5a9a3f', g: '#2f6a2c', P: '#b8653a', p: '#8c4a29' }

export const CLOCK = [
  '...OOOOO...',
  '..OWWWWWO..',
  '.OWWWWWWWO.',
  'OWWWWWWWWWO',
  'OWWWWWWWWWO',
  'OWWWWWWWWWO',
  'OWWWWWWWWWO',
  'OWWWWWWWWWO',
  '.OWWWWWWWO.',
  '..OWWWWWO..',
  '...OOOOO...',
]
export const PAL_CLOCK = { O: '#2b2f36', W: '#fbf8f1' }

export const SUN = [
  '..YYY..',
  '.YYYYY.',
  'YYYYYYY',
  'YYYYYYY',
  'YYYYYYY',
  '.YYYYY.',
  '..YYY..',
]
export const MOON = [
  '..YYY..',
  '.YYY...',
  'YYY....',
  'YYY....',
  'YYY....',
  '.YYY...',
  '..YYY..',
]

export const CHAI = [
  'CCCCC..',
  'CTTTCCC',
  'CTTTC.C',
  'CTTTCCC',
  '.CCC...',
]
export const PAL_CHAI = { C: '#f3efe6', T: '#b9783f' }


// ---- 8 x 8 icons for chips and buttons ----
export const ICONS = {
  check: ['........', '......OO', '.....OO.', 'O...OO..', 'OO.OO...', '.OOO....', '..O.....', '........'],
  gear: ['...OO...', '.O.OO.O.', '..OOOO..', 'OOO..OOO', 'OOO..OOO', '..OOOO..', '.O.OO.O.', '...OO...'],
  paper: ['.OOOO...', '.OWWOO..', '.OWWWWO.', '.OWOOWO.', '.OWWWWO.', '.OWOOWO.', '.OWWWWO.', '.OOOOOO.'],
  moon: ['...OOO..', '..OO....', '.OO.....', '.OO.....', '.OO.....', '.OO.....', '..OO....', '...OOO..'],
  alert: ['...OO...', '...OO...', '...OO...', '...OO...', '...OO...', '........', '...OO...', '...OO...'],
  mail: ['........', 'OOOOOOOO', 'OO....OO', 'O.O..O.O', 'O..OO..O', 'O......O', 'OOOOOOOO', '........'],
  play: ['.O......', '.OO.....', '.OOO....', '.OOOO...', '.OOOO...', '.OOO....', '.OO.....', '.O......'],
  clock: ['..OOOO..', '.O....O.', 'O..O...O', 'O..O...O', 'O..OOO.O', 'O......O', '.O....O.', '..OOOO..'],
  reset: ['..OOOO..', '.O....O.', 'O.......', 'O.....OO', 'O....OOO', '.O....O.', '..OOOO..', '........'],
}
export const iconPal = (c, w = '#fbf8f1') => ({ O: c, W: w })
