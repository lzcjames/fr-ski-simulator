#!/usr/bin/env python3
"""Engine v2 candidate: adapt the authorized 2026-11-26 upstream snapshot.

Keep v1 untouched; reuse its reviewed geographic adaptation and lossless codec.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from build_game import js, prepare_data
from engine_v1 import compile_engine as compile_v1, pack_engine as pack_v1, validate_slots
from resort_config import load_config
from grid_codec import decode_data
from fpv_v2_fix import patch_fpv
from mobile_lift_fix import patch_mobile_lift

UPSTREAM_SHA="1f41cd96d76c5ac30a371aa890bd6378806fd7d7340e0241e35d6fc002f86c70"
VERSION=2
REVISION='2.0.2'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def compile_engine(raw):
    if sha(raw)!=UPSTREAM_SHA:raise ValueError("unapproved v2 upstream snapshot: "+sha(raw))
    src=raw.decode("utf-8")
    def rep(old,new,count=1):
        nonlocal src
        if src.count(old)!=count:raise ValueError("v2 anchor mismatch: "+old[:100])
        src=src.replace(old,new)
    # Bridge the new title anchors to the existing audited v1 adapter.
    rep("<title>Avoriaz 滑雪</title>","<title>Avoriaz 滑雪 · 基于 雪迹 Cold Smoke</title>")
    rep("document.title = L.t('Avoriaz 滑雪');","document.title = L.t('Avoriaz 滑雪 · 基于 雪迹 Cold Smoke');")
    rep('"Avoriaz 滑雪":','"Avoriaz 滑雪 · 基于 雪迹 Cold Smoke":',7)
    # The new early locale script must not overwrite the resort-specific title.
    rep("document.title='Avoriaz';","")
    # New LiDAR table is indexed by the original Avoriaz building order.
    # Do not let a foreign resort inherit it even if some building indices match.
    lidar=list(re.finditer(r"^AVZ_DATA\.lidar = .*;$",src,re.M))
    if len(lidar)!=1:raise ValueError("missing upstream LiDAR table")
    rep(lidar[0][0],"// Removed Avoriaz-only LiDAR building table.")
    # Known shared-text anchors (not a global substitution in the locale dictionary).
    rep("out.push(en ? 'A run down the mountain at Avoriaz.' : '在 Avoriaz 滑了一趟。');",
        "out.push(en ? 'A run down the mountain at ' + FR_RESORT.name + '.' : '在 ' + FR_RESORT.name + ' 滑了一趟。');")
    rep("out.push(daily ? '#Avoriaz #滑雪 #今日之山' : '#Avoriaz #滑雪');",
        "out.push('#' + FR_RESORT.slug + (daily ? ' #滑雪 #今日之山' : ' #滑雪'));")
    rep("return { title: en ? 'Avoriaz 1800' : 'Avoriaz · 一个人，一座山', content: out.join('\\n') };",
        "return { title: FR_RESORT.name, content: out.join('\\n') };")
    # The original GPU layout requires 18 sampled textures. Refuse an
    # insufficient adapter before the canvas gets a WebGPU context.
    rep("  const device = await adapter.requestDevice({ requiredLimits: { maxSampledTexturesPerShaderStage: Math.min(adapter.limits.maxSampledTexturesPerShaderStage, 18) } });",
        """  const frTextureLimit = adapter.limits.maxSampledTexturesPerShaderStage;
  window.__frGpuPreflight = {available:frTextureLimit,required:18,accepted:frTextureLimit>=18};
  if (frTextureLimit < 18) { console.warn('WebGPU adapter has insufficient sampled textures; using WebGL2'); return null; }
  const device = await adapter.requestDevice({ requiredLimits: { maxSampledTexturesPerShaderStage: 18 } });""")
    src=patch_mobile_lift(patch_fpv(src))
    compiled=compile_v1(src)
    if re.search(r"^AVZ_DATA\.lidar\s*=",compiled,re.M):raise ValueError("foreign LiDAR mutation survived")
    validate_slots(compiled)
    return compiled

def pack_engine(compiled,data,cfg):
    if "lidar" in data:raise ValueError("unreviewed building-index LiDAR input")
    if "window.__frGpuPreflight" not in compiled:raise ValueError("not a v2 candidate template")
    src=pack_v1(compiled,data,cfg,compact_heights=True)
    pattern=r"^const FR_RESORT = (.*);$"
    m=re.search(pattern,src,re.M)
    meta=json.loads(m[1])
    meta.update(engineVersion=VERSION,engineRevision=REVISION,upstreamSha256=UPSTREAM_SHA,
                pbKey=cfg["slug"]+"-v2-preview-pb",onboardKey=cfg["slug"]+"-v2-preview-onboard")
    return src[:m.start()]+"const FR_RESORT = "+js(meta)+";"+src[m.end():]

def check_bundle(compiled,src,raw,cfg):
    validate_slots(compiled)
    expected=prepare_data(raw,cfg)
    if src!=pack_engine(compiled,expected,cfg):raise ValueError("non-deterministic v2 bundle")
    data=json.loads(re.search(r"^const AVZ_DATA = (.*);$",src,re.M)[1])
    meta=json.loads(re.search(r"^const FR_RESORT = (.*);$",src,re.M)[1])
    if decode_data(data)!=expected:raise ValueError("terrain or route data changed")
    if [g["step"] for g in expected["grids"]]!=[5,20,60] or len(raw["grids"])!=3 or expected["grids"]!=raw["grids"]:
        raise ValueError("three IGN layers must survive preparation")
    if meta["engineVersion"]!=2 or meta["pbKey"]!=cfg["slug"]+"-v2-preview-pb":raise ValueError("v2 namespace mismatch")
    if "lidar" in expected or re.search(r"^AVZ_DATA\.lidar\s*=",src,re.M):raise ValueError("foreign LiDAR")
    if len(src.encode())>10_000_000:raise ValueError("bundle exceeds 10 MB")
    scripts=re.findall(r"<script\b[^>]*>(.*?)</script\s*>",src,re.S|re.I)
    if len(scripts)!=3:raise ValueError("unexpected upstream script structure")
    with tempfile.TemporaryDirectory() as d:
        for i,code in enumerate(scripts):
            p=Path(d)/f"{i}.js";p.write_text(code,encoding="utf-8")
            subprocess.run(["node","--check",str(p)],check=True)
    return {"resort":cfg["resort"],"engineVersion":2,"upstreamSha256":UPSTREAM_SHA,
            "engineSha256":sha(compiled.encode()),"bytes":len(src.encode()),"routes":len(expected["courses"]),
            "grids":[g["step"] for g in expected["grids"]],"encodedGrids":sum("codec" in g for g in data["grids"]),
            "status":"PASS: deterministic bundle, exact terrain, no foreign LiDAR, JavaScript syntax"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--template",type=Path,required=True)
    p.add_argument("--config",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--engine-out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.engine_out.exists():p.error("outputs must be new")
    cfg=load_config(a.config);raw=json.loads(a.data.read_text(encoding="utf-8"))
    compiled=compile_engine(a.template.read_bytes())
    src=pack_engine(compiled,prepare_data(raw,cfg),cfg)
    report=check_bundle(compiled,src,raw,cfg)
    for path,body in ((a.out,src),(a.engine_out,compiled)):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(body.encode("utf-8"))
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
