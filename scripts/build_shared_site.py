#!/usr/bin/env python3
"""Extract identical cacheable resources from already verified standalone games.

No game logic, data, CSS rules or offline artifacts are changed.
Online documents keep their own inline FR_RESORT and AVZ_DATA declarations.
"""
import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from check_lobby import main as check_lobby

def digest(raw):return hashlib.sha256(raw).hexdigest()

def extract(src):
    blocks=list(re.finditer(r"<(script|style)\b([^>]*)>(.*?)</\1\s*>",src,re.S|re.I))
    if [m[1] for m in blocks]!=["style","script","script"] or any(m[2] for m in blocks):
        raise ValueError("unexpected standalone block structure")
    style,bootstrap,engine=blocks
    match=re.fullmatch(r"(\nconst FR_RESORT = [^\n]+;\nconst AVZ_DATA = [^\n]+;\n)(.*)",bootstrap[3],re.S)
    if not match or not match[2].strip():raise ValueError("unexpected data/bootstrap boundary")
    # Only data URLs are present in this CSS snapshot. Moving relative URLs
    # to another directory would change their resolution.
    for url in re.findall(r"url\((.*?)\)",style[3],re.S|re.I):
        if not url.strip().strip("\"'").startswith("data:"):
            raise ValueError("unexpected relative or network CSS URL")
    if re.search(r"@import\b",style[3],re.I):raise ValueError("unexpected CSS import")
    for code in (match[2],engine[3]):
        if re.search(r"\b(?:currentScript|import\.meta)\b",code):
            raise ValueError("script depends on original script location")
    resources={"style":style[3].encode("utf-8"),"bootstrap":match[2].encode("utf-8"),"engine":engine[3].encode("utf-8")}
    names={k:f"assets/{k}-{digest(v)}."+("css" if k=="style" else "js") for k,v in resources.items()}
    tags={"style":f'<link rel="stylesheet" href="../../{names["style"]}">',
          "bootstrap":f'<script>{match[1]}</script><script src="../../{names["bootstrap"]}"></script>',
          "engine":f'<script src="../../{names["engine"]}"></script>'}
    # Work in reverse source order to preserve exact text outside the blocks.
    online=src
    for m,key in reversed(list(zip(blocks,("style","bootstrap","engine")))):
        online=online[:m.start()]+tags[key]+online[m.end():]
    # Prove the externalization is reversible, including the original data.
    restored=online
    for key,m in zip(("style","bootstrap","engine"),blocks):
        if restored.count(tags[key])!=1:raise ValueError("ambiguous external tag")
        restored=restored.replace(tags[key],m[0],1)
    if restored!=src:raise ValueError("non-reversible extraction")
    return online,resources,names

def expected_entries(root, write=False):
    catalog=json.loads((root/"catalog.json").read_text(encoding="utf-8"))
    rows=[]; assets={}
    for row in catalog["resorts"]:
        slug=row["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",slug) or row["play"]!=f"games/{slug}/index.html":
            raise ValueError("invalid catalog route")
        p=root/row["play"]; original=p.read_bytes()
        if digest(original)!=row["sha256"]:raise ValueError("offline artifact changed")
        online,resources,names=extract(original.decode("utf-8"))
        raw=online.encode("utf-8"); rel=f"games/{slug}/online.html"
        for key,data in resources.items():
            name=names[key]
            if name in assets and assets[name]!=data:raise ValueError("content hash collision")
            assets[name]=data
        if write:(root/rel).write_bytes(raw)
        elif (root/rel).read_bytes()!=raw:raise ValueError("online source mismatch")
        rows.append({"slug":slug,"play":rel,"offline":row["play"],"offlineBytes":len(original),"onlineBytes":len(raw),
                     "onlineSha256":digest(raw),"assets":[names[k] for k in ("style","bootstrap","engine")]})
    if not rows:raise ValueError("empty online catalog")
    for name,data in assets.items():
        path=root/name
        if write:
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
        elif path.read_bytes()!=data:raise ValueError("shared asset mismatch")
    return {"schemaVersion":1,"resorts":rows,"assets":[{"path":name,"sha256":digest(data),"bytes":len(data)} for name,data in sorted(assets.items())]}

def lobby_links(root,manifest):
    path=root/"index.html";src=path.read_text(encoding="utf-8")
    for row in manifest["resorts"]:
        offline=html.escape(row["offline"],quote=True)
        online=html.escape(row["play"],quote=True)
        anchor=f'<a class="primary" href="{offline}">开始滑雪</a>'
        if src.count(anchor)!=1:raise ValueError("lobby link anchor mismatch")
        src=src.replace(anchor,anchor+f'<a class="secondary" href="{online}">在线共享引擎版</a>',1)
    path.write_text(src,encoding="utf-8")

def check(root):
    check_lobby(root)
    manifest=json.loads((root/"online-catalog.json").read_text(encoding="utf-8"))
    if expected_entries(root)!=manifest:raise ValueError("online manifest mismatch")
    lobby=(root/"index.html").read_text(encoding="utf-8")
    for row in manifest["resorts"]:
        if lobby.count(f'href="{row["play"]}"')!=1:raise ValueError("missing online link")
    print(json.dumps({"passed":True,"resorts":manifest["resorts"],"uniqueAssets":len(manifest["assets"]),
                      "sharedBytes":sum(a["bytes"] for a in manifest["assets"])},ensure_ascii=False))
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path);p.add_argument("--out",type=Path,required=True)
    p.add_argument("--check-only",action="store_true")
    a=p.parse_args()
    if a.check_only:
        check(a.out);return
    if not a.input or a.out.exists():p.error("input required; output must be new")
    if a.out.resolve().is_relative_to(a.input.resolve()):p.error("output inside input")
    check_lobby(a.input)
    shutil.copytree(a.input,a.out)
    manifest=expected_entries(a.out,write=True)
    (a.out/"online-catalog.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    lobby_links(a.out,manifest)
    check(a.out)
if __name__=="__main__":main()
