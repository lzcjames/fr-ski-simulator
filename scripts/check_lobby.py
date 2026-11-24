#!/usr/bin/env python3
"""Check catalog, local links, file hashes and offline launch entry points."""
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

class Links(HTMLParser):
    def __init__(self):super().__init__();self.local=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ("src","href") and value:
                u=urlsplit(value)
                if not u.scheme and not u.netloc:self.local.append(u.path)

def main(root):
    root=root.resolve()
    catalog=json.loads((root/"catalog.json").read_text(encoding="utf-8"))
    parser=Links();parser.feed((root/"index.html").read_text(encoding="utf-8"))
    for link in parser.local:
        p=(root/link).resolve()
        if not p.is_relative_to(root) or not p.is_file():raise ValueError("broken or unsafe link: "+link)
    for row in catalog["resorts"]:
        p=root/row["play"]
        if row["play"] not in parser.local or p.stat().st_size!=row["bytes"] or hashlib.sha256(p.read_bytes()).hexdigest()!=row["sha256"]:
            raise ValueError("invalid catalog game")
        if "light" in row:
            link=urlsplit(row["light"]).path
            if link not in parser.local or hashlib.sha256((root/link).read_bytes()).hexdigest()!=row["lightSha256"]:
                raise ValueError("invalid experimental game")
    print(f"PASS: {len(catalog['resorts'])} validated entries and {len(parser.local)} local links")
if __name__=="__main__":main(Path(sys.argv[1]))
