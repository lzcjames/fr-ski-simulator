#!/usr/bin/env python3
"""Build a v2 lobby from a successful full regression run."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from build_lobby import collect, passed, render, verify_game
from check_lobby import main as check_lobby
from engine_v2 import UPSTREAM_SHA, REVISION, compile_engine, pack_engine
from grid_codec import decode_data
from resort_config import load_config

ENGINE_SHA="87a47362d898bb8485bdb231199f7c93dd2f021de6cb42caa7238458cd418de3"
EXPECTED={"les-deux-alpes","alpe-d-huez","val-thorens"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifacts",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--stage",type=Path,required=True)
    p.add_argument("--four",action="store_true",help="require Galibier-Thabor and repaired-engine feature evidence")
    p.add_argument("--upstream",type=Path,help="pinned upstream for independent repaired template check")
    a=p.parse_args()
    if a.four and not a.upstream:p.error("--four requires pinned --upstream")
    expected=EXPECTED|({"galibier-thabor"} if a.four else set())
    compiled=compile_engine(a.upstream.read_bytes()) if a.four else None
    engine_sha=hashlib.sha256(compiled.encode("utf-8")).hexdigest() if a.four else ENGINE_SHA
    if a.out.exists() or a.stage.exists():p.error("output/staging must be new")
    a.stage.mkdir(parents=True)
    inputs={d.name.removesuffix("-v2-candidate"):d for d in a.artifacts.iterdir() if d.is_dir() and d.name.endswith("-v2-candidate")}
    if set(inputs)!=expected:raise ValueError("unexpected resort artifacts: "+str(sorted(inputs)))
    for slug,d in sorted(inputs.items()):
        game=d/"v2"/(slug+".html")
        template=d/"shared-v2.html"
        if hashlib.sha256(template.read_bytes()).hexdigest()!=engine_sha:raise ValueError("unexpected compiled engine")
        src=game.read_text(encoding="utf-8")
        meta=json.loads(re.search(r"^const FR_RESORT = (.*);$",src,re.M)[1])
        if meta["slug"]!=slug or meta["engineVersion"]!=2 or meta["upstreamSha256"]!=UPSTREAM_SHA:raise ValueError("v2 provenance mismatch")
        if meta["pbKey"]!=slug+"-v2-preview-pb":raise ValueError("PB namespace mismatch")
        if a.four:
            if meta.get("engineRevision")!=REVISION:raise ValueError("repair revision missing")
            data=decode_data(json.loads(re.search(r"^const AVZ_DATA = (.*);$",src,re.M)[1]))
            cfg=load_config(Path("resorts")/slug/"config.json")
            if pack_engine(compiled,data,cfg)!=src:raise ValueError("game differs from independently packed shared engine")
        modes=[("desktop",(960,540),False),("portrait",(390,844),True),("landscape",(844,390),True)]
        if a.four:modes += [("features-desktop",(960,540),False),("features-mobile",(390,844),True),("lift-portrait",(390,844),True),("lift-landscape",(844,390),True)]
        for mode,size,mobile in modes:
            r=passed(d/mode)
            if (r["width"],r["height"])!=size or r["mobile"]!=mobile or r["bytes"]!=game.stat().st_size:raise ValueError("unexpected test dimensions or game size")
            if r["game"]["title"]!=meta["title"]:raise ValueError("QA title mismatch")
            if mode.startswith("features"):
                checks={c["label"]:c["passed"] for c in r["probe"]["checks"]}
                required={"First-person regular mesh renders without fallback","First-person goofy mesh renders without fallback","First-person ski mesh renders without fallback","Return to skis","Ready after mode changes"}
                if not required<=checks.keys() or not all(checks[k] is True for k in required) or r.get("consoleErrors"):
                    raise ValueError("missing first-person regression evidence")
            if mode.startswith("lift-"):
                checks={c["label"]:c["passed"] for c in r["probe"]["checks"]}
                required={"Hidden away from station","Correct nearby lift","Hidden in menu","Board touch target hit test","Actual lift riding","Summit touch target hit test","Arrived near actual upper station","Simulation running"}
                if not required<=checks.keys() or not all(checks[k] is True for k in required) or r.get("consoleErrors"):
                    raise ValueError("missing actual mobile lift interaction evidence")
        for mode in ("portrait","landscape"):
            dst=a.stage/slug/mode
            shutil.copytree(d/mode,dst)
            shutil.copyfile(game,dst/game.name)
    a.out.mkdir(parents=True)
    rows=collect(a.stage,Path("resorts"),a.out)
    for r in rows:
        r["engineVersion"]=2;r["engineSha256"]=engine_sha;r["upstreamSha256"]=UPSTREAM_SHA
        if a.four:r["engineRevision"]=REVISION;r["qa"]["firstPersonDesktop"]=True;r["qa"]["firstPersonMobile"]=True;r["qa"]["liftPortrait"]=True;r["qa"]["liftLandscape"]=True
        r["qa"]["desktop"]=True
    template=Path("site/index.html").read_text(encoding="utf-8").replace("ENGINE PREVIEW","ENGINE V2.0 PREVIEW").replace("轻量模式调整部分视觉纹理分辨率，保持地形与滑雪物理不变，目前仅通过桌面模拟验证。","新版引擎基于作者最新授权版本，已通过桌面和手机横竖屏模拟测试。")
    if a.four:template=template.replace("ENGINE V2.0 PREVIEW","ENGINE V"+REVISION+" PREVIEW")
    (a.out/"catalog.json").write_text(json.dumps({"schemaVersion":1,"engineVersion":2,"resorts":rows},ensure_ascii=False,indent=2),encoding="utf-8")
    (a.out/"index.html").write_text(render(template,rows),encoding="utf-8")
    check_lobby(a.out)
    print(json.dumps({"engineVersion":2,"resorts":[{"slug":r["slug"],"routes":r["routes"],"bytes":r["bytes"]} for r in rows],"engineSha256":engine_sha},ensure_ascii=False))
if __name__=="__main__":main()
