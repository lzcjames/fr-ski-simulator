"""Structural tests for independent engine/data packing (not browser QA)."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from engine_v1 import compact_grids, pack_engine, slot, validate_slots
from build_game import prepare_data
from test_generator import fixture

def test_template():
    return "\n".join(slot(k) for k,n in (("DATA",1),("CONFIG",1),("NAME",2),("TITLE",1),("REGION",2),("COUNT",2),("WARNING",1)) for _ in range(n))

class EngineTests(unittest.TestCase):
    def test_grid_roundtrip(self):
        cfg,raw=fixture("Test Alpha","test-alpha")
        data=prepare_data(raw,cfg)
        original=copy.deepcopy(data)
        packed=compact_grids(data)
        self.assertEqual(len(packed["grids"]),1)
        self.assertEqual([packed["grids"][i] for i in packed["gridRefs"]],data["grids"])
        self.assertEqual(data,original)
        data["grids"][1]=dict(data["grids"][1],x0=5)
        packed=compact_grids(data)
        self.assertEqual(len(packed["grids"]),2)
        self.assertEqual([packed["grids"][i] for i in packed["gridRefs"]],data["grids"])
    def test_resort_metadata_and_escaping(self):
        t=test_template()
        for name,slug in [("Test Alpha","test-alpha"),("Alpe d'Huez <test>","test-beta")]:
            cfg,raw=fixture(name,slug)
            cfg["preview"]["regionLabel"]="FRANCE / ALPS"
            packed=pack_engine(t,prepare_data(raw,cfg),cfg)
            data,meta=map(json.loads,packed.splitlines()[:2])
            self.assertEqual(meta["name"],name)
            self.assertEqual(meta["pbKey"],slug+"-preview-pb")
            self.assertEqual(data["resort"],name)
            self.assertNotIn("<test>",packed)
            self.assertNotIn("__FRSKI_V1_",packed)
    def test_missing_slot(self):
        with self.assertRaises(ValueError): validate_slots(test_template().replace(slot("DATA"),""))

if __name__=="__main__": unittest.main()
