import base64
import json
import random
import struct
import subprocess
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from grid_codec import encode_grid,decode_grid,decode_data,CODEC

def grid(words):
    return {"fmt":"f32","nx":len(words),"nz":1,"step":5,"x0":0,"z0":0,"h":base64.b64encode(struct.pack("<%dI"%len(words),*words)).decode()}

class CodecTests(unittest.TestCase):
    def test_bit_exact_and_javascript(self):
        # Smooth terrain plus negative values, signed zero and extreme bit patterns.
        words=[0x45000000+i*8 for i in range(4000)]+[0,0x80000000,0xffffffff,0x7f800000,1]
        raw=grid(words);packed=encode_grid(raw)
        self.assertEqual(packed["codec"],CODEC)
        self.assertEqual(decode_grid(packed),raw)
        js=(Path(__file__).resolve().parents[1]/"scripts/grid_codec.js").read_text()
        out=subprocess.check_output(["node","-e",js+"\nconsole.log(JSON.stringify(frRestoreHeights(JSON.parse(require('fs').readFileSync(0,'utf8')))))"],input=json.dumps(packed),text=True)
        self.assertEqual(json.loads(out),raw)
        self.assertEqual(decode_data({"grids":[packed],"gridRefs":[0,0]})["grids"],[raw,raw])
    def test_no_expansion(self):
        rng=random.Random(123);raw=grid([rng.getrandbits(32) for _ in range(1000)])
        self.assertEqual(encode_grid(raw),raw)
    def test_invalid(self):
        for payload in (b"",b"\xff"*5,b"\x00\x00"):
            g=dict(grid([0]),codec=CODEC,h=base64.b64encode(payload).decode())
            with self.assertRaises(ValueError):decode_grid(g)
if __name__=="__main__":unittest.main()
