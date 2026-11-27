#!/usr/bin/env python3
"""Build a three-resort v2 lobby from a successful full regression run."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from build_lobby import collect, passed, render, verify_game
from check_lobby import main as check_lobby
from engine_v2 import UPSTREAM_SHA

ENGINE_SHA="87a47362d898bb8485bdb231199f7c93dd2f021de6cb42caa7238458cd418de3"
EXPECTED={"les-deux-alpes","alpe-d-huez","val-thorens"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifacts",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--stage",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.stage.exists():p.error("output/staging must be new")
    a.stage.mkdir(parents=True)
    inputs={d.name.removesuffix("-v2-candidate"):d for d in a.artifacts.iterdir() if d.is_dir() and d.name.endswith("-v2-candidate")}
    if set(inputs)!=EXPECTED:raise ValueError("expected three tested resort artifacts")
    for slug,d in sorted(inputs.items()):
        game=d/"v2"/(slug+".html")
        template=d/"shared-v2.html"
        if hashlib.sha256(template.read_bytes()).hexdigest()!=ENGINE_SHA:raise ValueError("unexpected compiled engine")
        src=game.read_text(encoding="utf-8")
        meta=json.loads(re.search(r"^const FR_RESORT = (.*);$",src,re.M)[1])
        if meta["slug"]!=slug or meta["engineVersion"]!=2 or meta["upstreamSha256"]!=UPSTREAM_SHA:raise ValueError("v2 provenance mismatch")
        if meta["pbKey"]!=slug+"-v2-preview-pb":raise ValueError("PB namespace mismatch")
        for mode,size,mobile in (("desktop",(960,540),False),("portrait",(390,844),True),("landscape",(844,390),True)):
            r=passed(d/mode)
            if (r["width"],r["height"])!=size or r["mobile"]!=mobile or r["bytes"]!=game.stat().st_size:raise ValueError("unexpected test dimensions or game size")
            if r["game"]["title"]!=meta["title"]:raise ValueError("QA title mismatch")
        for mode in ("portrait","landscape"):
            dst=a.stage/slug/mode
            shutil.copytree(d/mode,dst)
            shutil.copyfile(game,dst/game.name)
    a.out.mkdir(parents=True)
    rows=collect(a.stage,Path("resorts"),a.out)
    for r in rows:
        r["engineVersion"]=2;r["engineSha256"]=ENGINE_SHA;r["upstreamSha256"]=UPSTREAM_SHA
        r["qa"]["desktop"]=True
    template=Path("site/index.html").read_text(encoding="utf-8").replace("ENGINE PREVIEW","ENGINE V2.0 PREVIEW").replace("轻量模式调整部分视觉纹理分辨率，保持地形与滑雪物理不变，目前仅通过桌面模拟验证。","新版引擎基于作者最新授权版本，已通过桌面和手机横竖屏模拟测试。")
    (a.out/"catalog.json").write_text(json.dumps({"schemaVersion":1,"engineVersion":2,"resorts":rows},ensure_ascii=False,indent=2),encoding="utf-8")
    (a.out/"index.html").write_text(render(template,rows),encoding="utf-8")
    check_lobby(a.out)
    print(json.dumps({"engineVersion":2,"resorts":[{"slug":r["slug"],"routes":r["routes"],"bytes":r["bytes"]} for r in rows],"engineSha256":ENGINE_SHA},ensure_ascii=False))
if __name__=="__main__":main()
