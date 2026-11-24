#!/usr/bin/env python3
"""Config-driven HTML engineering preview. Reuses the authorized legacy engine."""
import argparse
import copy
import html
import json
import math
import re
from pathlib import Path
from legacy_adapter import choose_axis
from resort_config import load_config

def js(value):
    return json.dumps(value,ensure_ascii=False,separators=(",",":"),allow_nan=False).replace("<","\\u003c").replace("\u2028","\\u2028").replace("\u2029","\\u2029")

def prepare_data(raw,cfg):
    if raw.get("resort")!=cfg["resort"] or list(raw.get("bbox",[]))!=cfg["bbox"]:
        raise ValueError("data does not match resort profile")
    if raw.get("origin")!={"lon":cfg["origin"][0],"lat":cfg["origin"][1]}:
        raise ValueError("data origin does not match profile")
    data=choose_axis(raw,cfg["preview"]["primaryCourse"])
    courses=[c for c in data["courses"] if c.get("connected") and len(c["p"])>=2 and (cfg["preview"]["includeGradeReview"] or not c.get("needsGradeReview"))]
    if not courses or len({c["id"] for c in courses})!=len(courses):
        raise ValueError("missing or duplicate courses")
    data["courses"]=courses
    for c in courses:
        c["sub"]="Experimental route — DEM grade review pending" if c.get("needsGradeReview") else "Experimental timed run — not gameplay validated"
    data["pistes"]=[p for p in data["pistes"] if p["d"] in (0,1,2,3) and len(p["p"])>=2]
    for p in data["pistes"]: p["n"]=p["n"] or ""
    data["lifts"]=[l for l in data["lifts"] if len(l["p"])>=2 and l["n"] and not l.get("clipped")]
    data["integration"]["status"]="config-driven engineering preview; gameplay not certified"
    return data

def patch(src,data,cfg):
    def rep(old,new):
        nonlocal src
        if src.count(old)!=1: raise ValueError("template anchor mismatch: "+old[:100])
        src=src.replace(old,new,1)
    def line(prefix,new):
        matches=[x for x in src.splitlines() if x.startswith(prefix)]
        if len(matches)!=1: raise ValueError("line anchor mismatch: "+prefix)
        rep(matches[0],new)
    def pattern(rx,new):
        matches=list(re.finditer(rx,src,re.S))
        if len(matches)!=1: raise ValueError("pattern anchor mismatch: "+rx)
        rep(matches[0].group(),new)
    name=html.escape(cfg["resort"],quote=True)
    # The legacy locale strings contain both HTML and JS literals. Escape both contexts.
    label=html.escape(cfg["preview"]["regionLabel"],quote=True)
    count=len(data["courses"]); countlabel=f"{count} ROUTES"
    step=data["grids"][0]["step"]
    sources=data.get("sources",{}).get("dem",{}).get("sourceCounts",{})
    dem_label=html.escape(" / ".join(sorted(sources)) or "DEM source unreported")
    # Branding replacements precede data injection, preserving actual OSM names.
    src=src.replace("FRANCE / PORTES DU SOLEIL",label).replace("1800 M · FRENCH ALPS",countlabel+" · FRENCH ALPS")
    src=src.replace("Avoriaz 滑雪 · 基于 雪迹 Cold Smoke",name+" · Cold Smoke / Avoriaz")
    src=src.replace(">Avoriaz<",">"+name+"<").replace("Avoriaz · 1800 m",name+" · "+countlabel).replace("Avoriaz · Mountain map",name+" · Mountain map")
    src=src.replace("<strong>"+name+"</strong><small>1800 M</small>","<strong>"+name+"</strong><small>"+countlabel+" · PREVIEW</small>")
    wet=cfg["preview"].get("wetBelow",1420)
    rep("resort: 'Avoriaz', wetBelow: 1420","resort: "+js(cfg["resort"])+", wetBelow: "+js(wet))
    line("const AVZ_DATA = ","const AVZ_DATA = "+js(data)+";")
    for p in ("AVZ_DATA.pois =","AVZ_DATA.streets =","AVZ_DATA.courses.splice("):
        line(p,"// Removed old-resort data mutation.")
    pattern(r"const AVZ_FUN_ROUTES = \[.*?\n\];","const AVZ_FUN_ROUTES = [];")
    rep("const originals = D.courses.filter(c => !c.fun && !c.town && !/^town/.test(c.id));","const originals = [];")
    line("  const SPOTS = ","  const SPOTS = [];")
    line("  starts.push({ n: '小镇上方","  { for (const c of D.courses) { const p=c.p[0]; starts.push({n:c.n+' start',x:p[0],z:p[1],alt:Math.round(c.a0)}); } }")
    line("    const landmarks=[['AVORIAZ'","    const landmarks=[];")
    pattern(r'<div class="ld-scene">.*?(?=<div class="ld-snow">)','<div class="ld-scene" style="background:linear-gradient(145deg,#1a344b,#07131d 70%)"></div>')
    rep("const Ps = (D.pistes || []).filter(p => p.p && p.p.length >= 2);","const Ps = (D.pistes || []).filter(p => D.courses.some(c => !c.needsGradeReview && c.n === p.n) && p.p && p.p.length >= 2);")
    rep("h += (hg - h) * w;","h += Math.max(-2, Math.min(2, hg - h)) * w;")
    rep("Math.max(-7, Math.min(7, bv[k] - g[ii]))","Math.max(-2, Math.min(2, bv[k] - g[ii]))")
    rep("Math.max(-6, Math.min(6, Dl[o] + num[o] / den[o] * wmx[o]))","Math.max(-2, Math.min(2, Dl[o] + num[o] / den[o] * wmx[o]))")
    rep("if (gradeY && sg > -30 && sg < L + 30)","if (false && gradeY && sg > -30 && sg < L + 30)")
    line("  const EN_NAMES = ","  const EN_NAMES = {};")
    old=[x for x in src.splitlines() if x.startswith("  const D_LOOK=")]
    if len(old)!=1 or ",D_LV=" not in old[0]: raise ValueError("missing D_LOOK anchor")
    rep(old[0],"  const D_LOOK={}"+old[0][old[0].index(",D_LV="):])
    rep("'Timed line with start and finish markers';","(c.needsGradeReview?'EXPERIMENTAL · DEM grade review pending · PB disabled':'Experimental timed run · gameplay not yet validated');")
    rep("'Timed run · '+RUN_LEVEL[it.c.d]","(it.c.needsGradeReview?'Grade review pending · ':'Test run · ')+RUN_LEVEL[it.c.d]")
    rep("if (runRescue) pbLine =","if (course.needsGradeReview) pbLine = '<p class=\"finish-pb\">Experimental DEM grade review · PB disabled</p>'; else if (runRescue) pbLine =")
    src=src.replace("'avz-pb'",js(cfg["slug"]+"-preview-pb")).replace("'avz-onboard'",js(cfg["slug"]+"-preview-onboard"))
    warn=f'<div style="position:fixed;z-index:99999;top:4px;left:50%;transform:translateX(-50%);padding:4px 9px;background:#07131dcc;color:#fff;font:11px system-ui;pointer-events:none;text-align:center">{name} · {countlabel} · ENGINE PREVIEW · {step:g} m grid · OSM / {dem_label} · Avoriaz / Cold Smoke adaptation · Not for navigation</div>'
    if "</body>" in src: rep("</body>",warn+"</body>")
    else: src+=warn
    return src

def build(template,raw,cfg):
    return patch(template,prepare_data(raw,cfg),cfg)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("config","template","data","out"):
        p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args()
    if a.out.resolve() in (a.template.resolve(),a.data.resolve(),a.config.resolve()):
        p.error("refuse to overwrite input")
    cfg=load_config(a.config)
    output=build(a.template.read_text(encoding="utf-8"),json.loads(a.data.read_text(encoding="utf-8")),cfg)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(output,encoding="utf-8")
    print(json.dumps({"resort":cfg["resort"],"output":str(a.out),"bytes":a.out.stat().st_size,"status":"engineering preview, browser QA required"},ensure_ascii=False))

if __name__=="__main__": main()
