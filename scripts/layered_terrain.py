#!/usr/bin/env python3
"""Build real nested terrain layers and recompile route data on the near DEM.

Default is a Terrarium integration pilot (10/20/60 m output spacing).
A supplied georeferenced elevation raster can provide 5/20/60 m grids.
Never fabricate heights or silently mix elevation sources.
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from legacy_adapter import f32, sampler
from resort_config import load_config

def bounds(g):
    return (g["x0"],g["z0"],g["x0"]+(g["nx"]-1)*g["step"],g["z0"]+(g["nz"]-1)*g["step"])

def contains(outer, inner, margin=0):
    a,b,c,d=bounds(outer); w,s,e,n=bounds(inner)
    return a+margin<=w and b+margin<=s and c-margin>=e and d-margin>=n

def validate_layers(dems):
    if len(dems)!=3: raise ValueError("expected near, mid, far")
    first=dems[0]
    for d in dems:
        if any(d[k]!=first[k] for k in ("bbox","origin","projection")):
            raise ValueError("terrain coordinate mismatch")
        if d["nx"]<4 or d["nz"]<4 or len(d["h"])!=d["nx"]*d["nz"]:
            raise ValueError("invalid grid dimensions")
        if not all(math.isfinite(h) and -12000<h<9000 for h in d["h"]):
            raise ValueError("invalid elevation")
        counts=d["_meta"]["sourceCounts"]
        if len(counts)!=1 or sum(counts.values())!=len(d["h"]) or set(counts)!=set(first["_meta"]["sourceCounts"]):
            raise ValueError("mixed or incomplete elevation sources")
    if not first["step"]<dems[1]["step"]<dems[2]["step"]:
        raise ValueError("grid spacings must increase")
    if not contains(dems[1],first,400+2*dems[1]["step"]) or not contains(dems[2],dems[1],2*dems[2]["step"]):
        raise ValueError("insufficient nested coverage for legacy blending")

def pack_grid(d):
    return dict(**{k:d[k] for k in ("x0","z0","step","nx","nz")},fmt="f32",h=f32(d["h"]))

def merge(data,dems):
    validate_layers(dems)
    if any(data[k]!=dems[0][k] for k in ("bbox","origin","projection")):
        raise ValueError("data and terrain coordinate mismatch")
    if data["grids"]!=[pack_grid(dems[0])]:
        raise ValueError("near grid differs from validated route-data grid")
    data["grids"]=[pack_grid(d) for d in dems]
    for grid in data["grids"]: sampler(grid)
    data["sources"]["terrainLayers"]=[
        {"role":role,"step":d["step"],"bounds":bounds(d),"nx":d["nx"],"nz":d["nz"],"provenance":d["_meta"]}
        for role,d in zip(("near","mid","far"),dems)]
    data["terrainStatus"]="three independently sampled nested grids; output spacing is not native accuracy"
    return data

def sample_raster(raster,credit,cfg,step,padding,skill):
    # Reproject the real raster into the exact local tangent grid used by the Skill.
    # Grid samples are pixel centres; no fill, extrapolation, or Terrarium fallback.
    import numpy as np
    import rasterio
    from rasterio.transform import Affine
    from rasterio.warp import reproject, Resampling
    sys.path.insert(0,str(skill/"scripts"))
    from common import Projection, utcnow
    origin=dict(zip(("lon","lat"),cfg["origin"]))
    pr=Projection(origin)
    west,north,east,south=pr.bounds(cfg["bbox"])
    x0=math.floor((west-padding)/step)*step; z0=math.floor((north-padding)/step)*step
    nx=math.ceil((east+padding-x0)/step)+1; nz=math.ceil((south+padding-z0)/step)+1
    if nx*nz>900000: raise ValueError("raster grid too large; narrow sector or increase spacing")
    lon,lat=pr.inverse(x0,z0)
    dx=step/pr.mx; dy=step/pr.mz
    transform=Affine(dx,0,lon-dx/2,0,-dy,lat+dy/2)
    out=np.full((nz,nx),np.nan,dtype=np.float32)
    with rasterio.open(raster) as ds:
        if ds.crs is None or ds.count!=1:
            raise ValueError("expected single-band georeferenced elevation raster")
        reproject(rasterio.band(ds,1),out,src_transform=ds.transform,src_crs=ds.crs,src_nodata=ds.nodata,
                  dst_transform=transform,dst_crs="EPSG:4326",dst_nodata=np.nan,resampling=Resampling.bilinear)
        native={"file":raster.name,"crs":str(ds.crs),"pixelSize":list(ds.res)}
    if not np.isfinite(out).all(): raise ValueError("raster does not cover all requested terrain; no fabricated fill")
    return {"origin":origin,"bbox":cfg["bbox"],"projection":{"kind":"WGS84 local tangent approximation","mx":pr.mx,"mz":pr.mz,"axes":"X east, Z south, heights metres ASL"},
        "x0":x0,"z0":z0,"step":step,"nx":nx,"nz":nz,"h":np.round(out.astype("float64"),2).ravel().tolist(),
        "_meta":{"fetchedAt":utcnow(),"requestedSource":"raster","sourceCounts":{"raster":nx*nz},"attribution":[credit],"nativeRaster":native,"warning":"Output spacing does not establish native accuracy; verify datum and raster licence."}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("config","skill","osm","work"): p.add_argument("--"+k,type=Path,required=True)
    sources=p.add_mutually_exclusive_group()
    sources.add_argument("--raster",type=Path)
    sources.add_argument("--ign-wms",action="store_true",help="Fetch and independently cross-check numeric IGN GeoTIFFs")
    p.add_argument("--source-credit")
    p.add_argument("--near-step",type=int,choices=(5,10,15),default=None)
    a=p.parse_args(); cfg=load_config(a.config); skill=a.skill.resolve(); work=a.work.resolve()
    if work.exists() and any(work.iterdir()): p.error("use a fresh output directory")
    if a.raster and not a.source_credit: p.error("raster requires source credit and vertical datum")
    if a.near_step==5 and not (a.raster or a.ign_wms): p.error("5 m mode requires real elevation raster; do not label Terrarium as high resolution")
    step=a.near_step or (5 if (a.raster or a.ign_wms) else 10)
    revision=subprocess.check_output(["git","-C",str(skill),"rev-parse","HEAD"],text=True).strip()
    if revision!=cfg["skillCommit"]: p.error("unexpected Skill revision")
    osm=a.osm.resolve()
    if json.loads(osm.read_text(encoding="utf-8"))["_meta"]["bbox"]!=cfg["bbox"]:
        p.error("OSM artifact does not match profile bbox")
    work.mkdir(parents=True,exist_ok=True)
    def run(script,*args):
        subprocess.run([sys.executable,str(skill/"scripts"/script),*map(str,args)],check=True)
    dems=[]
    for role,spacing,padding in (("near",step,150),("mid",20,900),("far",60,7500)):
        path=work/(role+".json")
        if a.ign_wms:
            from ign_terrain import fetch_ign_layer
            dem=fetch_ign_layer(cfg,spacing,padding,skill,work,role)
            path.write_text(json.dumps(dem,separators=(",",":")),encoding="utf-8")
        elif a.raster:
            dem=sample_raster(a.raster.resolve(),a.source_credit,cfg,spacing,padding,skill)
            path.write_text(json.dumps(dem,separators=(",",":")),encoding="utf-8")
        else:
            run("fetch_dem.py","--bbox",",".join(map(str,cfg["bbox"])),"--origin",",".join(map(str,cfg["origin"])),"--step",spacing,"--padding",padding,"--zoom",13,"--source","terrarium","--cache",work/"cache","--out",path)
            dem=json.loads(path.read_text(encoding="utf-8"))
        dems.append(dem)
    validate_layers(dems)
    # Recompute courses, lift tops, grade flags, and main axis on the new near DEM.
    data=work/"resort-data.json"; js=work/"resort-data.js"
    run("build_data.py","--osm",osm,"--dem",work/"near.json","--name",cfg["resort"],"--out",js,"--json-out",data,"--report",work/"data-report.json","--max-courses",cfg["build"]["maxCourses"],"--max-starts",cfg["build"]["maxStarts"],"--join-gap",2)
    run("test_pipeline.py","--data",data,"--osm",osm,"--dem",work/"near.json")
    result=merge(json.loads(data.read_text(encoding="utf-8")),dems)
    out=work/"layered-data.json";out.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    report=[{"role":r["role"],"spacing":r["step"],"dimensions":[r["nx"],r["nz"]],"bounds":r["bounds"],"source":r["provenance"]["sourceCounts"]} for r in result["sources"]["terrainLayers"]]
    (work/"layers-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"resort":cfg["resort"],"layers":report,"bytes":out.stat().st_size},ensure_ascii=False))

if __name__=="__main__": main()
