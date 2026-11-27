#!/usr/bin/env python3
"""Check deployed public files against a verified static release, not just READY."""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import urllib.parse
import urllib.request

ORIGIN = "https://fr-ski-simulator.vercel.app"
def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(root, path):
    name=path.relative_to(root).as_posix()
    expected=path.read_bytes()
    url=ORIGIN+"/"+urllib.parse.quote(name,safe="/")
    request=urllib.request.Request(url,headers={"Accept-Encoding":"identity","User-Agent":"FR-Ski-Simulator-release-QA/1.0"})
    try:
        with urllib.request.urlopen(request,timeout=60) as response:
            if urllib.parse.urlsplit(response.geturl()).netloc!=urllib.parse.urlsplit(ORIGIN).netloc:
                raise ValueError("unexpected redirect host")
            raw=response.read(len(expected)+1)
            cache=response.headers.get("Cache-Control","")
            mime=response.headers.get("Content-Type","")
            if response.status!=200 or raw!=expected:
                raise ValueError("HTTP response differs from release; status="+str(response.status)+" actual SHA256="+sha(raw))
            if name.startswith("assets/"):
                directives={d.strip().lower() for d in cache.split(",")}
                if not {"immutable","max-age=31536000"}<=directives:
                    raise ValueError("shared asset cache policy differs: "+cache)
            elif name.startswith("games/") or name in ("catalog.json","online-catalog.json"):
                directives={d.strip().lower() for d in cache.split(",")}
                if not ("no-store" in directives or {"max-age=0","must-revalidate"}<=directives):
                    raise ValueError("game/catalog revalidation policy differs: "+cache)
            if name.endswith(".html") and "text/html" not in mime.lower():
                raise ValueError("expected HTML media type: "+mime)
            return {"path":name,"passed":True,"bytes":len(raw),"sha256":sha(raw),"cacheControl":cache,"contentType":mime}
    except Exception as e:
        return {"path":name,"passed":False,"error":str(e),"expectedSha256":sha(expected)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    root=a.site.resolve()
    release=json.loads((root/"release.json").read_text())
    catalog=json.loads((root/"catalog.json").read_text())
    assert len(catalog["resorts"]) in (3,4)
    assert sorted(release["resorts"])==sorted(r["slug"] for r in catalog["resorts"])
    files=sorted(p for p in root.rglob("*") if p.is_file() and p.relative_to(root).as_posix()!="vercel.json")
    assert len(files)==7+3*len(catalog["resorts"])
    # The lobby root is a distinct public route; verify it resolves to index.html too.
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda p:verify(root,p),files))
    try:
        with urllib.request.urlopen(urllib.request.Request(ORIGIN+"/",headers={"Accept-Encoding":"identity"}),timeout=60) as r:
            expected=(root/"index.html").read_bytes()
            raw=r.read(len(expected)+1)
            if r.status!=200 or urllib.parse.urlsplit(r.geturl()).netloc!=urllib.parse.urlsplit(ORIGIN).netloc or raw!=expected:
                raise ValueError("lobby root differs from published index.html")
            rows.append({"path":"/","passed":True,"sha256":sha(raw),"bytes":len(raw)})
    except Exception as e:
        rows.append({"path":"/","passed":False,"error":str(e)})
    report={"origin":ORIGIN,"sourceRun":release["sourceRun"],"resorts":release["resorts"],
            "engineRevisions":sorted(set(r.get("engineRevision","2.0") for r in catalog["resorts"])),
            "passed":all(r["passed"] for r in rows),"files":rows}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,ensure_ascii=False))
    if not report["passed"]:raise SystemExit("public release verification failed")
if __name__=="__main__":main()
