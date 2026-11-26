#!/usr/bin/env python3
"""Capture an authorized public upstream snapshot for review, never promote it."""
import argparse
import datetime
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from resolve_template import URL, SHA256, TRACKER

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    limit=30_000_000
    req=urllib.request.Request(URL,headers={"User-Agent":"FR-Ski-Simulator/1.0 (authorized template snapshot verification)"})
    with urllib.request.urlopen(req,timeout=60) as response:
        raw=response.read(limit+1)
        final_url=response.geturl()
        content_type=response.headers.get("Content-Type","")
    if len(raw)>limit:raise ValueError("snapshot exceeds review size cap")
    if "text/html" not in content_type.lower():raise ValueError("expected HTML response")
    html_document=bool(re.search(rb"<!doctype html|<html\b",raw,re.I))
    game_markers={k.decode():raw.count(k) for k in (b"AVZ_DATA",b"Cold Smoke",b"requestAdapter",b"</script>")}
    print("Response diagnostics:",json.dumps({"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"prefix":raw[:300].decode("utf-8","replace"),"htmlDocument":html_document,"gameMarkers":game_markers},ensure_ascii=True))
    clean,count=re.subn(TRACKER,b"",raw)
    raw_sha=hashlib.sha256(raw).hexdigest()
    clean_sha=hashlib.sha256(clean).hexdigest()
    meta={"url":URL,"finalUrl":final_url,"capturedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"contentType":content_type,"rawBytes":len(raw),"normalizedBytes":len(clean),"rawSha256":raw_sha,"normalizedSha256":clean_sha,"previousNormalizedSha256":SHA256,"knownTrackerRemoved":count,"changed":clean_sha!=SHA256,"htmlDocument":html_document,"gameMarkers":game_markers,"status":"review only; no execution or engine promotion"}
    (a.out/"avoriaz-current.raw.html").write_bytes(raw)
    (a.out/"avoriaz-current.review.html").write_bytes(clean)
    (a.out/"snapshot.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":main()
