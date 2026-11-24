#!/usr/bin/env python3
"""Opt-in startup profiling and reduced cosmetic texture sizes.

This is an experiment applied to a validated standalone HTML; physics, DEM,
route data and default visual settings remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

def instrument(src):
    def rep(old,new):
        nonlocal src
        if src.count(old)!=1: raise ValueError("unexpected performance anchor: "+old[:100])
        src=src.replace(old,new,1)
    rep("  const manual = QS.has('manual'), step = async (f, name) => { if (stage) stage(f, name); if (!manual) await new Promise(r => requestAnimationFrame(() => setTimeout(r, 0))); };",
        """  const frLight = QS.get('frlight') === '1';
  const frProfile = QS.get('frprofile') === '1';
  const frBoot = { mode: frLight ? 'light' : 'original', start: performance.now(), stages: [], completeMs: null };
  if (frProfile) window.__frBoot = frBoot;
  const manual = QS.has('manual'), step = async (f, name) => {
    if (frProfile) frBoot.stages.push({progress:f, name:name || null, atMs:performance.now()-frBoot.start});
    if (stage) stage(f, name);
    if (!manual) await new Promise(r => requestAnimationFrame(() => setTimeout(r, 0)));
  };""")
    rep("farW: +QS.get('vistares') || (gfx.caps.maxTex >= 4096 ? 3072 : 2048), cityW: +QS.get('cityres') || 1024",
        "farW: +QS.get('vistares') || (frLight ? 2048 : (gfx.caps.maxTex >= 4096 ? 3072 : 2048)), cityW: +QS.get('cityres') || (frLight ? 768 : 1024)")
    rep("Nebula.init(gfx, +QS.get('nebres') || (gfx.caps.maxTex >= 4096 && (navigator.deviceMemory || 8) >= 4 ? 1536 : 768))",
        "Nebula.init(gfx, +QS.get('nebres') || (frLight ? 768 : (gfx.caps.maxTex >= 4096 && (navigator.deviceMemory || 8) >= 4 ? 1536 : 768)))")
    rep("  App.ready = true;\n}\n// one simulation + presentation step.",
        """  if (frProfile) {
    frBoot.completeMs = performance.now() - frBoot.start;
    frBoot.quality = {tier:Quality.tier, why:Quality.why};
    frBoot.backend = gfx.caps.backend;
    frBoot.sizes = {
      farW:+QS.get('vistares') || (frLight ? 2048 : (gfx.caps.maxTex >= 4096 ? 3072 : 2048)),
      cityW:+QS.get('cityres') || (frLight ? 768 : 1024),
      nebulaW:+QS.get('nebres') || (frLight ? 768 : (gfx.caps.maxTex >= 4096 && (navigator.deviceMemory || 8) >= 4 ? 1536 : 768))
    };
  }
  App.ready = true;
}
// one simulation + presentation step.""")
    return src

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.input.resolve()==a.out.resolve(): p.error("refuse to overwrite validated original")
    raw=a.input.read_bytes()
    src=raw.decode("utf-8")
    result=instrument(src)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(result.encode("utf-8"))
    print(json.dumps({"inputSha256":hashlib.sha256(raw).hexdigest(),"outputSha256":hashlib.sha256(a.out.read_bytes()).hexdigest(),"bytes":a.out.stat().st_size,"mode":"original by default; ?frlight=1 opt-in"}))

if __name__=="__main__": main()
