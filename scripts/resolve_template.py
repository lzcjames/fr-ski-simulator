#!/usr/bin/env python3
"""Resolve the exact authorized Avoriaz snapshot; fail closed on any change."""
import argparse
import hashlib
import re
import urllib.request
from pathlib import Path

URL = "https://avoriaz.manus.space/"
SHA256 = "9c2300bee3e393df0138d9ebce37272580e16a308d69b90fb3a498ec7f20f024"
MAX_BYTES = 12_000_000
TRACKER = rb'<script defer nonce="[0-9a-f-]+" src="https://manus-analytics\.com/script\.js" data-website-id="332aad2c-f802-4192-b66f-d3b429cfed47"></script>\r?\n?'

def normalize(raw):
    if len(raw)>MAX_BYTES:
        raise ValueError("template exceeds size limit")
    clean=re.sub(TRACKER,b"",raw)
    actual=hashlib.sha256(clean).hexdigest()
    if actual!=SHA256:
        raise ValueError("template snapshot changed; use the authorized local copy. SHA256="+actual)
    return clean

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--input",type=Path)
    g.add_argument("--download",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.input:
        if a.input.resolve()==a.out.resolve():
            p.error("refuse to overwrite input")
        raw=a.input.read_bytes()
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":"FR-Ski-Simulator/1.0 (authorized template snapshot verification)"})
        with urllib.request.urlopen(req,timeout=60) as response:
            raw=response.read(MAX_BYTES+1)
    clean=normalize(raw)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(clean)
    print("Verified template SHA256:",SHA256,"bytes:",len(clean))

if __name__=="__main__": main()
