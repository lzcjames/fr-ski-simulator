#!/usr/bin/env python3
"""Build and validate real resort data with the pinned upstream Skill."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from resort_config import load_config

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=ROOT/"resorts/les-deux-alpes/config.json")
    p.add_argument("--skill", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--source", choices=["terrarium", "ign"])
    p.add_argument("--step", type=float)
    p.add_argument("--osm-export", type=Path)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    cfg = load_config(a.config)
    skill, work = a.skill.resolve(), a.work.resolve()
    if work == skill or skill in work.parents:
        p.error("work must be outside the Skill checkout")
    w,s,e,n = cfg["bbox"]
    lon,lat = cfg["origin"]
    if not (w < lon < e and s < lat < n):
        p.error("origin outside bbox")
    step = a.step if a.step is not None else cfg["dem"]["step"]
    if not __import__('math').isfinite(step) or step <= 0:
        p.error("step must be positive")
    bbox,origin = ",".join(map(str,cfg["bbox"])), ",".join(map(str,cfg["origin"]))
    osm,dem,data,js,report = [work/f for f in ("osm.json","dem.json","resort-data.json","resort-data.js","data-report.json")]
    def py(file,*args):
        return [sys.executable,str(skill/"scripts"/file),*map(str,args)]
    commands = [
        py("fetch_osm.py","--bbox",bbox,"--out",osm,* (["--from-file",a.osm_export.resolve()] if a.osm_export else [])),
        py("fetch_dem.py","--bbox",bbox,"--origin",origin,"--source",a.source or cfg["dem"]["source"],"--step",step,"--zoom",cfg["dem"]["zoom"],"--padding",cfg["dem"]["padding"],"--cache",work/"cache","--out",dem),
        py("build_data.py","--osm",osm,"--dem",dem,"--name",cfg["resort"],"--out",js,"--json-out",data,"--report",report,"--max-courses",cfg["build"]["maxCourses"],"--max-starts",cfg["build"]["maxStarts"],"--join-gap",2),
        ["node","--check",str(js)],
        py("test_pipeline.py","--data",data,"--osm",osm,"--dem",dem),
    ]
    if a.dry_run:
        for command in commands: print(json.dumps(command))
        return
    commit = subprocess.check_output(["git","-C",str(skill),"rev-parse","HEAD"],text=True).strip()
    if commit != cfg["skillCommit"]:
        p.error("unexpected upstream Skill revision")
    work.mkdir(parents=True,exist_ok=True)
    if any(x.exists() for x in (osm,dem,data,js,report)):
        p.error("use a fresh output directory")
    env = dict(os.environ,PYTHONDONTWRITEBYTECODE="1")
    for command in commands:
        print(json.dumps(command),flush=True)
        subprocess.run(command,cwd=work,env=env,check=True)
    print("Data validation passed; inspect route completeness before engine integration.")

if __name__ == "__main__":
    main()
