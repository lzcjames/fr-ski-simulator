"""Check both variants on the exact validated HTML, not a synthetic anchor fixture."""
import argparse
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from engine_performance import instrument

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    before=a.input.read_text(encoding="utf-8"); after=a.output.read_text(encoding="utf-8")
    if after!=instrument(before):raise ValueError("unexpected HTML changes")
    for prefix in ("const AVZ_DATA = ","const FR_RESORT = "):
        pattern=r"^"+re.escape(prefix)+r".*;$"
        x=re.search(pattern,before,re.M);y=re.search(pattern,after,re.M)
        if not x or not y or x.group()!=y.group():raise ValueError("resort metadata or data changed")
    with tempfile.TemporaryDirectory() as d:
        for i,code in enumerate(re.findall(r"<script\b[^>]*>(.*?)</script\s*>",after,re.S|re.I)):
            path=Path(d)/f"script-{i}.js";path.write_text(code,encoding="utf-8")
            subprocess.run(["node","--check",str(path)],check=True)
    print("PASS: exact resort data retained, deterministic patch, JavaScript syntax")
if __name__=="__main__":main()
