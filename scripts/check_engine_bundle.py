"""Check packed HTML against its verified inputs and JS syntax."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from build_game import prepare_data
from engine_v1 import pack_engine, validate_slots
from resort_config import load_config
from grid_codec import decode_data

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("engine","game","config","data"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--compact-heights",action="store_true")
    a=p.parse_args()
    engine=a.engine.read_text(encoding="utf-8")
    validate_slots(engine)
    cfg=load_config(a.config)
    expected=prepare_data(json.loads(a.data.read_text(encoding="utf-8")),cfg)
    src=a.game.read_text(encoding="utf-8")
    if src!=pack_engine(engine,expected,cfg,a.compact_heights):
        raise ValueError("packed HTML differs from deterministic rebuild")
    meta=json.loads(re.search(r"^const FR_RESORT = (.*);$",src,re.M).group(1))
    actual=json.loads(re.search(r"^const AVZ_DATA = (.*);$",src,re.M).group(1))
    encoded_count=sum("codec" in g for g in actual["grids"])
    actual=decode_data(actual)
    if actual!=expected:
        raise ValueError("packed data changed after grid restoration")
    if meta["pbKey"]!=cfg["slug"]+"-preview-pb" or meta["onboardKey"]!=cfg["slug"]+"-preview-onboard":
        raise ValueError("storage namespace mismatch")
    scripts=re.findall(r"<script\b[^>]*>(.*?)</script\s*>",src,re.S|re.I)
    if not scripts or a.game.stat().st_size>10_000_000:
        raise ValueError("missing scripts or oversized game")
    with tempfile.TemporaryDirectory() as tmp:
        for i,code in enumerate(scripts):
            file=Path(tmp)/f"inline-{i}.js"
            file.write_text(code,encoding="utf-8")
            subprocess.run(["node","--check",str(file)],check=True)
    print(json.dumps({"resort":meta["name"],"routes":len(actual["courses"]),"encodedGrids":encoded_count,"grids":len(actual["grids"]),"bytes":a.game.stat().st_size,"engine_sha256":hashlib.sha256(a.engine.read_bytes()).hexdigest(),"status":"PASS: deterministic pack, lossless data, storage namespace, JavaScript syntax"},ensure_ascii=False))

if __name__=="__main__": main()
