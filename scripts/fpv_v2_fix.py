"""Fix v2 first-person index selection against the new equipment mesh layout."""
def patch_fpv(src):
    def line(prefix,new):
        nonlocal src
        hits=[x for x in src.splitlines() if x.startswith(prefix)]
        if len(hits)!=1:raise ValueError("FPV anchor mismatch: "+prefix)
        src=src.replace(hits[0],new,1)
    # Body parts and rigid equipment are separate contiguous index ranges.
    # In the old FPV implementation, the full mesh included both equipment sets.
    line("  F.figIdx = function ()", """  F.figIdx = function (mode) {
    const m = Skier.mesh, keep = [];
    if (!m.pr || m.pr.length !== 18 || !m.bodyNi || !m.nSki) throw new Error('unexpected FPV mesh layout');
    const end = mode === 'ski' ? m.nSki : m.bodyNi;
    for (let i = 0; i < end; i += 3) {
      const id = m.V[m.I[i] * 10 + 6];
      if (id !== 9 && id !== 10 && id !== 2 && (mode === 'ski' || (id !== 11 && id !== 3)))
        keep.push(m.I[i],m.I[i+1],m.I[i+2]);
    }
    if (mode !== 'ski') {
      // Retain just the selected board, its bindings and snowboard boots.
      for (const k of [mode === 'goofy' ? 15 : 6,16,17])
        for (let i=m.pr[k][0];i<m.pr[k][1];i++) keep.push(m.I[i]);
    }
    return new Uint32Array(keep);
  };
  const frFpvBuffers = new WeakMap();
  function frFpvIndices(mode) {
    const m=Skier.mesh;
    let cache=frFpvBuffers.get(m);
    if (!cache) { cache=new Map(); frFpvBuffers.set(m,cache); }
    if (!cache.has(mode)) {
      const idx=F.figIdx(mode);
      cache.set(mode,{ib:gfx.buffer(idx,'index'),count:idx.length});
    }
    return cache.get(mode);
  }""")
    line("      const fi = F.figIdx(); hideIb", "      // FPV indices are created lazily for the selected equipment.")
    line("        if (Skier.want) Skier.want(); if (hideFor !== Skier.mesh)", """        if (Skier.want) Skier.want();
        const mode = AVZ.board ? (AVZ.sbSg < 0 ? 'goofy' : 'regular') : 'ski';
        const selected=frFpvIndices(mode);""")
    line("        gfx.draw = function (P, d) { if (d && d.tex && d.tex.tBones === figTex", """        gfx.draw = function (P, d) {
          const m=Skier.mesh, live=mode==='ski' ? {ib:m.gpu.ib,n:m.nSki} : (mode==='goofy' ? m.sbG : m.sbR);
          if (d && d.tex && d.tex.tBones===figTex && live && d.ib===live.ib && d.count===live.n) {
            n++;
            const e=Object.assign({},d,{tex:Object.assign({},d.tex,{tBones:hideTex}),ib:selected.ib,count:selected.count});
            F.frDraw={mode,count:e.count,frames:(F.frDraw?.frames||0)+1};
            return d0.call(this,P,e);
          }
          return d0.apply(this,arguments);
        };""")
    return src
