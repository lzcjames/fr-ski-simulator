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
    if not re.search(rb"<!doctype html|<html\b",raw[:4096],re.I):raise ValueError("not an HTML document")
    clean,count=re.subn(TRACKER,b"",raw)
    raw_sha=hashlib.sha256(raw).hexdigest()
    clean_sha=hashlib.sha256(clean).hexdigest()
    meta={"url":URL,"finalUrl":final_url,"capturedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"contentType":content_type,"rawBytes":len(raw),"normalizedBytes":len(clean),"rawSha256":raw_sha,"normalizedSha256":clean_sha,"previousNormalizedSha256":SHA256,"knownTrackerRemoved":count,"changed":clean_sha!=SHA256,"status":"review only; no execution or engine promotion"}
    (a.out/"avoriaz-current.raw.html").write_bytes(raw)
    (a.out/"avoriaz-current.review.html").write_bytes(clean)
    (a.out/"snapshot.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":main()
