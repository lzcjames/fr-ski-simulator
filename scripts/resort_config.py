"""Validate a resort profile; all coordinates and metadata are explicit."""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("resort", "slug", "sector", "skillCommit"):
        if not isinstance(cfg.get(key), str) or not cfg[key].strip():
            raise ValueError("missing " + key)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", cfg["slug"]):
        raise ValueError("invalid resort slug")
    if not re.fullmatch(r"[0-9a-f]{40}", cfg["skillCommit"]):
        raise ValueError("Skill revision must be a full commit SHA")
    w,s,e,n = cfg["bbox"]
    lon,lat = cfg["origin"]
    if not (-180 <= w < lon < e <= 180 and -90 <= s < lat < n <= 90):
        raise ValueError("invalid bbox or origin")
    dem = cfg["dem"]
    if dem["source"] not in ("terrarium", "ign") or not math.isfinite(dem["step"]) or dem["step"] <= 0:
        raise ValueError("invalid DEM source or spacing")
    if not isinstance(dem["zoom"],int) or not 0 <= dem["zoom"] <= 18 or not 0 <= dem["padding"] <= 5000:
        raise ValueError("invalid DEM zoom or padding")
    build = cfg.setdefault("build", {})
    for key, default, lo, hi in (("maxCourses",8,1,30),("maxStarts",12,1,50)):
        v=build.setdefault(key,default)
        if type(v) is not int or not lo<=v<=hi:
            raise ValueError("invalid "+key)
    preview=cfg.setdefault("preview",{})
    primary=preview.setdefault("primaryCourse",None)
    if primary is not None and (not isinstance(primary,str) or not primary.strip()):
        raise ValueError("invalid primaryCourse")
    if type(preview.setdefault("includeGradeReview",False)) is not bool:
        raise ValueError("invalid includeGradeReview")
    if "wetBelow" in preview and (not isinstance(preview["wetBelow"],(float,int)) or not math.isfinite(preview["wetBelow"])):
        raise ValueError("invalid wetBelow")
    if not isinstance(preview.setdefault("regionLabel","FRANCE / ALPS"),str):
        raise ValueError("invalid regionLabel")
    return cfg

def profile_path(slug):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("invalid resort slug")
    path=ROOT/"resorts"/slug/"config.json"
    if load_config(path)["slug"] != slug:
        raise ValueError("profile slug mismatch")
    return path

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("slug")
    args=p.parse_args()
    print(profile_path(args.slug))
