#!/usr/bin/env python3
"""Read-only inventory of the authorized legacy HTML. Never changes source."""
import argparse
import hashlib
import json
import re
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("html", type=Path)
    a=p.parse_args()
    raw=a.html.read_bytes()
    source=raw.decode("utf-8")
    matches=list(re.finditer(r"\bconst AVZ_DATA\s*=\s*",source))
    if len(matches)!=1: p.error("expected one AVZ_DATA declaration")
    d,end=json.JSONDecoder().raw_decode(source,matches[0].end())
    print(json.dumps({
        "sha256":hashlib.sha256(raw).hexdigest(),
        "bytes":len(raw),"origin":d["origin"],"fields":list(d),
        "grids":[{k:g.get(k) for k in ("nx","nz","step","fmt")} for g in d["grids"]],
        "counts":{k:len(d[k]) for k in ("pistes","lifts","buildings","courses")},
        "anchors":{k:source.count(k) for k in ("AVZ_DATA.pois","AVZ_DATA.streets","AVZ_DATA.courses.splice","AVZ_FUN_ROUTES","A.SNOW","window.__ski","createGPU","createGL")},
    },indent=2,ensure_ascii=False))

if __name__=="__main__": main()
