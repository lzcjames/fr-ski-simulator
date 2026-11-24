#!/usr/bin/env python3
"""Assemble a static lobby from QA-passed standalone HTML artifacts."""
import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

def unique(root, name):
    matches=list(root.rglob(name))
    if len(matches)!=1 or not matches[0].is_file():
        raise ValueError(f"{root}: expected exactly one {name}, got {len(matches)}")
    return matches[0]

def passed(root):
    report=json.loads(unique(root,"report.json").read_text(encoding="utf-8"))
    if report.get("passed") is not True or report.get("game",{}).get("backend")!="webgl2":
        raise ValueError(f"Browser QA not passed: {root}")
    if report.get("probe",{}).get("passed") is not True:
        raise ValueError(f"Interaction probe not passed: {root}")
    return report

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_game(path, cfg):
    src=path.read_text(encoding="utf-8")
    meta=json.loads(re.search(r"^const FR_RESORT = (.*);$",src,re.M).group(1))
    data=json.loads(re.search(r"^const AVZ_DATA = (.*);$",src,re.M).group(1))
    if meta["slug"]!=cfg["slug"] or meta["name"]!=cfg["resort"] or data["resort"]!=cfg["resort"]:
        raise ValueError("game/profile mismatch")
    grids=data["grids"]
    if [g["step"] for g in grids]!=[5,20,60]:
        raise ValueError("expected validated IGN layered game")
    if not data.get("sources",{}).get("terrainLayers"):
        raise ValueError("missing terrain provenance")
    if path.stat().st_size>10_000_000:
        raise ValueError("standalone game exceeds size gate")
    return len(data["courses"])

def collect(inputs, profiles, out):
    rows=[]
    for folder in sorted(inputs.iterdir()):
        if not folder.is_dir():continue
        slug=folder.name
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",slug):
            raise ValueError("invalid resort slug")
        cfg=json.loads((profiles/slug/"config.json").read_text(encoding="utf-8"))
        if cfg["slug"]!=slug:raise ValueError("profile path mismatch")
        portrait=folder/"portrait";landscape=folder/"landscape";startup=folder/"startup"
        passed(portrait);passed(landscape)
        game=unique(portrait,slug+".html")
        if sha(game)!=sha(unique(landscape,slug+".html")):
            raise ValueError("mobile tests cover different game bytes")
        routes=verify_game(game,cfg)
        dest=out/"games"/slug;dest.mkdir(parents=True)
        shutil.copyfile(game,dest/"index.html")
        row={"slug":slug,"name":cfg["resort"],"sector":cfg["sector"],"routes":routes,"grid":[5,20,60],
             "bytes":game.stat().st_size,"sha256":sha(game),"play":f"games/{slug}/index.html",
             "qa":{"mobilePortrait":True,"mobileLandscape":True,"backend":"webgl2"},
             "status":"engineering-preview"}
        if startup.exists():
            original=unique(startup/"qa"/"original","report.json")
            light=unique(startup/"qa"/"light","report.json")
            a=passed(original.parent);b=passed(light.parent)
            profiled=unique(startup,slug+".html")
            verify_game(profiled,cfg)
            # The performance variant must retain the exact embedded geographic data.
            pattern=r"^const AVZ_DATA = .*;$"
            if re.search(pattern,game.read_text(encoding="utf-8"),re.M).group()!=re.search(pattern,profiled.read_text(encoding="utf-8"),re.M).group():
                raise ValueError("performance variant changed resort data")
            shutil.copyfile(profiled,dest/"experimental.html")
            row["light"]=f"games/{slug}/experimental.html?frlight=1"
            row["lightSha256"]=sha(profiled)
            row["qa"]["lightDesktop"]=True
            row["startupSeconds"]={"original":round(a["readyMs"]/1000,2),"light":round(b["readyMs"]/1000,2)}
        shots=list(portrait.rglob("02-running.png"))
        if len(shots)==1:
            images=out/"images";images.mkdir(exist_ok=True)
            shutil.copyfile(shots[0],images/(slug+".png"))
            row["image"]=f"images/{slug}.png"
        rows.append(row)
    if not rows:raise ValueError("no validated games")
    return rows

def render(template, rows):
    def esc(s):return html.escape(str(s),quote=True)
    cards=[]
    for r in rows:
        name=esc(r["name"]);p=esc(r["play"])
        img=f'<img src="{esc(r["image"])}" alt="{name} 游戏实测截图" loading="lazy">' if "image" in r else '<div class="mountain" aria-hidden="true"></div>'
        light=f'<a class="secondary" href="{esc(r["light"])}">轻量模式 · 桌面实验</a>' if "light" in r else ""
        cards.append(f'<article class="resort">{img}<div class="info"><p class="eyebrow">IGN RGE ALTI · 5 / 20 / 60 m</p><h2>{name}</h2><p class="sector">{esc(r["sector"])}</p><p class="stats">{r["routes"]} 条候选路线 · {r["bytes"]/1_000_000:.2f} MB</p><p class="qa">WebGL2 · 手机横屏及竖屏模拟通过</p><div class="actions"><a class="primary" href="{p}">开始滑雪</a><a class="secondary" href="{p}" download="{esc(r["slug"])}.html">下载离线 HTML</a>{light}</div></div></article>')
    if template.count("<!-- RESORT_CARDS -->")!=1 or template.count("<!-- RESORT_COUNT -->")!=1:raise ValueError("lobby template anchors missing")
    return template.replace("<!-- RESORT_CARDS -->","\n".join(cards)).replace("<!-- RESORT_COUNT -->",str(len(rows)))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    p.add_argument("--profiles",type=Path,default=Path("resorts"));p.add_argument("--template",type=Path,default=Path("site/index.html"))
    a=p.parse_args()
    if a.out.exists():raise ValueError("output must be new")
    a.out.mkdir(parents=True)
    rows=collect(a.inputs,a.profiles,a.out)
    (a.out/"catalog.json").write_text(json.dumps({"schemaVersion":1,"resorts":rows},ensure_ascii=False,indent=2),encoding="utf-8")
    (a.out/"index.html").write_text(render(a.template.read_text(encoding="utf-8"),rows),encoding="utf-8")
    print(json.dumps({"resorts":[{"slug":r["slug"],"routes":r["routes"],"bytes":r["bytes"]} for r in rows],"out":str(a.out)},ensure_ascii=False))
if __name__=="__main__":main()
