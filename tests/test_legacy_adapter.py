#!/usr/bin/env python3
"""Validate the legacy compatibility layer on generated real data."""
import base64
import json
import math
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from legacy_adapter import adapt

x=json.loads(Path(sys.argv[1]).read_text())
y=adapt(x,"Thuit 2")
for k in ("cx","hw","gy"):
    v=base64.b64decode(y[k],validate=True)
    assert len(v)==4*(y["L"]+1)
    assert all(map(math.isfinite,struct.unpack("<%df"%(y["L"]+1),v)))
for k in ("mask","buildings","pois","streets","startPoints"):
    assert x[k]==y[k]
assert len(y["grids"])>=3 and y["grids"][0]==x["grids"][0]
for name in ("Thuit 2","Clot des Fonds","Diable 1"):
    print(name,adapt(x,name)["L"])
try:
    adapt(x,"Demoiselles")
except ValueError:
    pass
else:
    raise AssertionError("flagged or non-monotone route accepted")
print("PASS: packed arrays, unchanged geography, three monotone routes, rejection")
