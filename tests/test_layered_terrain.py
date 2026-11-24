"""Synthetic unit tests, not evidence of real geographic accuracy."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from layered_terrain import validate_layers, merge, pack_grid

def demo(step,pad):
    n=int(2*pad/step)+1
    return {"bbox":[6,45,6.1,45.1],"origin":{"lon":6.05,"lat":45.05},"projection":{"mx":78000,"mz":111000},"x0":-pad,"z0":-pad,"step":step,"nx":n,"nz":n,"h":[1500.0]*(n*n),"_meta":{"sourceCounts":{"terrarium":n*n}}}

class Layers(unittest.TestCase):
    def test_nested_grid_roundtrip(self):
        ds=[demo(10,100),demo(20,700),demo(60,1200)]
        data={k:ds[0][k] for k in ("bbox","origin","projection")}
        data.update(grids=[pack_grid(ds[0])],sources={})
        result=merge(data,ds)
        self.assertEqual([g["step"] for g in result["grids"]],[10,20,60])
        self.assertEqual(len(result["sources"]["terrainLayers"]),3)
    def test_reject_duplicate_and_mixed_source(self):
        ds=[demo(10,100),demo(20,700),demo(60,1200)]
        with self.assertRaises(ValueError): validate_layers([ds[0]]*3)
        ds[1]["_meta"]["sourceCounts"]={"ign":len(ds[1]["h"])}
        with self.assertRaises(ValueError): validate_layers(ds)
    def test_reject_bad_coverage(self):
        with self.assertRaises(ValueError): validate_layers([demo(10,100),demo(20,200),demo(60,1200)])
    def test_reject_wrong_projection(self):
        ds=[demo(10,100),demo(20,700),demo(60,1200)]
        ds[2]["projection"]={"mx":1,"mz":1}
        with self.assertRaises(ValueError): validate_layers(ds)

if __name__=="__main__": unittest.main()
