#!/usr/bin/env python3
"""Compile a resort-independent engine once, then pack independent resort data.

The shared template is derived from the verified original using the existing
reviewed patch set. No rendering or physics rewrite is introduced.
"""
import argparse
import copy
import hashlib
import html
import json
import re
from pathlib import Path
from build_game import js, patch, prepare_data
from resort_config import load_config
from grid_codec import encode_grid

VERSION = 1
PREFIX = "__FRSKI_V1_"
SLOTS = ("DATA","CONFIG","NAME","TITLE","REGION","COUNT","WARNING")
def slot(key): return PREFIX+key+"__"

def replace_exact(text,old,new,count=1):
    if text.count(old)!=count:
        raise ValueError("engine anchor count mismatch: "+old[:100])
    return text.replace(old,new)

def compile_engine(original):
    if PREFIX in original:
        raise ValueError("input already contains engine slots")
    # The sentinel profile is build-time metadata, not a playable fake resort.
    marker=PREFIX+"COMPILE__"
    cfg={"resort":marker,"slug":"frski-engine-sentinel","preview":{"regionLabel":PREFIX+"REGION_SENTINEL__","wetBelow":-987654}}
    raw={"resort":marker,"courses":[{}],"grids":[{"step":987654}],"sources":{"dem":{"sourceCounts":{PREFIX+"DEM_SENTINEL__":1}}}}
    src=patch(original,raw,cfg)
    old="const AVZ_DATA = "+js(raw)+";"
    src=replace_exact(src,old,"const FR_RESORT = "+slot("CONFIG")+";\nconst AVZ_DATA = "+slot("DATA")+";\n"
        +Path(__file__).with_name("grid_codec.js").read_text(encoding="utf-8")+"\nAVZ_DATA.grids=AVZ_DATA.grids.map(frRestoreHeights);\n"
        +"if (AVZ_DATA.gridRefs) { const g=AVZ_DATA.grids; AVZ_DATA.grids=AVZ_DATA.gridRefs.map(i=>g[i]); delete AVZ_DATA.gridRefs; }")
    src=replace_exact(src,"document.title = L.t('"+marker+" · Cold Smoke / Avoriaz');","document.title = FR_RESORT.title;")
    src=replace_exact(src,'resort: '+js(marker)+', wetBelow: -987654','resort: FR_RESORT.name, wetBelow: FR_RESORT.wetBelow')
    src=replace_exact(src,"const brand = '<div class=\"avz-brand\"><strong>"+marker+"</strong><small>1 ROUTES · PREVIEW</small></div>';",
        "const brand = '<div class=\"avz-brand\"><strong>' + FR_RESORT.nameHtml + '</strong><small>' + FR_RESORT.countLabel + ' · PREVIEW</small></div>';")
    src=replace_exact(src,"capB.textContent = '"+marker+" · 1 ROUTES';","capB.textContent = FR_RESORT.name + ' · ' + FR_RESORT.countLabel;")
    src=replace_exact(src,"sel<0?'"+marker+" · Mountain map'","sel<0?FR_RESORT.name + ' · Mountain map'")
    # These are resort-specific keys, not general user preferences (language, suit, view).
    src=replace_exact(src,js("frski-engine-sentinel-preview-pb"),"FR_RESORT.pbKey",2)
    src=replace_exact(src,js("frski-engine-sentinel-preview-onboard"),"FR_RESORT.onboardKey",2)
    # Remove stale localized branding entries, preserving all ordinary UI strings.
    for key in (marker+" · 1 ROUTES",marker+" · Cold Smoke / Avoriaz",marker+" · Mountain map",PREFIX+"REGION_SENTINEL__","1 ROUTES · FRENCH ALPS"):
        src,n=re.subn(re.escape(js(key))+r':"(?:[^"\\]|\\.)*",',"",src)
        if n!=7: raise ValueError("locale branding anchor count mismatch: "+key)
    # Replace remaining visible HTML, not JS code.
    src=replace_exact(src,"<title>"+marker+" · Cold Smoke / Avoriaz</title>","<title>"+slot("TITLE")+"</title>")
    src=replace_exact(src,">"+marker+"<",">"+slot("NAME")+"<",2)
    src=replace_exact(src,PREFIX+"REGION_SENTINEL__",slot("REGION"),2)
    src=replace_exact(src,"1 ROUTES · FRENCH ALPS",slot("COUNT")+" · FRENCH ALPS",2)
    warn=marker+" · 1 ROUTES · ENGINE PREVIEW · 987654 m grid · OSM / "+PREFIX+"DEM_SENTINEL__"+" · Avoriaz / Cold Smoke adaptation · Not for navigation"
    src=replace_exact(src,warn,slot("WARNING"))
    if marker in src or "frski-engine-sentinel" in src or "987654 m grid" in src:
        raise ValueError("unresolved compile sentinel")
    validate_slots(src)
    return src

def validate_slots(src):
    expected={"DATA":1,"CONFIG":1,"NAME":2,"TITLE":1,"REGION":2,"COUNT":2,"WARNING":1}
    found=re.findall(PREFIX+r"([A-Z_]+)__",src)
    if sorted(found)!=sorted(k for k,n in expected.items() for _ in range(n)):
        raise ValueError("engine slot contract mismatch")
    return True

def compact_grids(data):
    """Serialize each identical grid once, restore legacy ordering before boot."""
    out=copy.deepcopy(data)
    unique=[]; refs=[]; seen={}
    for grid in out["grids"]:
        key=json.dumps(grid,sort_keys=True,separators=(",",":"),allow_nan=False)
        if key not in seen:
            seen[key]=len(unique);unique.append(grid)
        refs.append(seen[key])
    if len(unique)<len(refs):
        out["grids"]=unique;out["gridRefs"]=refs
    return out

def pack_engine(compiled, data, cfg, compact_heights=False):
    validate_slots(compiled)
    if data["resort"]!=cfg["resort"]:
        raise ValueError("resort name mismatch")
    name=cfg["resort"]; slug=cfg["slug"]; count=len(data["courses"])
    count_label=f"{count} ROUTE"+("S" if count!=1 else "")
    title=name+" · Cold Smoke / Avoriaz"
    metadata={"engineVersion":VERSION,"name":name,"nameHtml":html.escape(name,quote=True),"slug":slug,"title":title,"countLabel":count_label,
        "wetBelow":cfg["preview"].get("wetBelow",1420),"pbKey":slug+"-preview-pb","onboardKey":slug+"-preview-onboard"}
    sources=data.get("sources",{}).get("dem",{}).get("sourceCounts",{})
    dem=" / ".join(sorted(sources)) or "DEM source unreported"
    warning=f"{name} · {count_label} · ENGINE PREVIEW · {data['grids'][0]['step']:g} m grid · OSM / {dem} · Avoriaz / Cold Smoke adaptation · Not for navigation"
    packed=compact_grids(data)
    if compact_heights:
        if "function frRestoreHeights(" not in compiled: raise ValueError("engine lacks grid decoder")
        packed["grids"]=[encode_grid(g) for g in packed["grids"]]
    values={"DATA":js(packed),"CONFIG":js(metadata),"NAME":html.escape(name,quote=True),"TITLE":html.escape(title,quote=True),"REGION":html.escape(cfg["preview"]["regionLabel"],quote=True),"COUNT":count_label,"WARNING":html.escape(warning,quote=True)}
    # Substitute in a single pass: no accidental replacement inside resort data.
    return re.sub(PREFIX+r"([A-Z_]+)__",lambda m:values[m.group(1)],compiled)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="action",required=True)
    c=sub.add_parser("compile")
    c.add_argument("--template",type=Path,required=True)
    c.add_argument("--out",type=Path,required=True)
    b=sub.add_parser("pack")
    for x in ("engine","config","data","out"): b.add_argument("--"+x,type=Path,required=True)
    b.add_argument("--compact-heights",action="store_true")
    a=p.parse_args()
    inputs=[a.template] if a.action=="compile" else [a.engine,a.config,a.data]
    if a.out.resolve() in [f.resolve() for f in inputs]:
        p.error("refuse to overwrite inputs")
    if a.action=="compile":
        from resolve_template import normalize
        result=compile_engine(normalize(a.template.read_bytes()).decode("utf-8"))
    else:
        cfg=load_config(a.config)
        data=prepare_data(json.loads(a.data.read_text(encoding="utf-8")),cfg)
        result=pack_engine(a.engine.read_text(encoding="utf-8"),data,cfg,a.compact_heights)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(result,encoding="utf-8")
    print(json.dumps({"action":a.action,"engineVersion":VERSION,"output":str(a.out),"bytes":a.out.stat().st_size,"sha256":hashlib.sha256(a.out.read_bytes()).hexdigest()}))

if __name__=="__main__": main()
