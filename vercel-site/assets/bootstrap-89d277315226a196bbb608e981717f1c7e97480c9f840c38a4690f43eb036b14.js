// Restore exact IEEE-754 float words before the unchanged legacy engine boots.
function frRestoreHeights(g) {
  if (!Object.hasOwn(g, 'codec')) return g;
  if (g.codec !== 'f32-xor-leb128-v1' || g.fmt !== 'f32') throw Error('Unknown grid codec');
  const n = g.nx * g.nz;
  if (!Number.isInteger(n) || n <= 0 || n > 900000) throw Error('Invalid grid size');
  const src = atob(g.h), buf = new Uint8Array(n * 4), view = new DataView(buf.buffer);
  let i = 0, prev = 0;
  for (let k = 0; k < n; k++) {
    let v = 0;
    for (let shift = 0; shift <= 28; shift += 7) {
      if (i >= src.length) throw Error('Truncated grid');
      const b = src.charCodeAt(i++);
      if (shift === 28 && b > 15) throw Error('Grid word overflow');
      v |= (b & 127) << shift;
      if (b < 128) break;
    }
    prev = (prev ^ v) >>> 0;
    view.setUint32(k * 4, prev, true);
  }
  if (i !== src.length) throw Error('Trailing grid bytes');
  // Chunk to avoid argument limits on mobile browsers.
  let binary = '';
  for (let i = 0; i < buf.length; i += 8192) binary += String.fromCharCode(...buf.subarray(i, i + 8192));
  g.h = btoa(binary);
  delete g.codec;
  return g;
}

AVZ_DATA.grids=AVZ_DATA.grids.map(frRestoreHeights);
if (AVZ_DATA.gridRefs) { const g=AVZ_DATA.grids; AVZ_DATA.grids=AVZ_DATA.gridRefs.map(i=>g[i]); delete AVZ_DATA.gridRefs; }
// Removed Avoriaz-only LiDAR building table.
// Removed old-resort data mutation.
// Removed old-resort data mutation.
// Removed old-resort data mutation.
