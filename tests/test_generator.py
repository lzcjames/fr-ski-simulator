"""Offline synthetic tests: fixtures are not real resorts or gameplay evidence."""
import base64
import copy
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_game import prepare_data
from resort_config import load_config,profile_path
from legacy_adapter import choose_axis

def fixture(name,slug):
    grid={"nx":6,"nz":6,"step":10,"x0":0,"z0":0,"fmt":"f32","h":base64.b64encode(struct.pack("<36f",*[2000-10*j for j in range(6) for i in range(6)])).decode()}
    route={"id":"a","n":"Main run","p":[[10,10],[10,25],[10,40]],"connected":True,"needsGradeReview":False,"d":1}
    cfg={"resort":name,"slug":slug,"sector":"Synthetic test fixture","bbox":[6,44,6.1,44.1],"origin":[6.05,44.05],"skillCommit":"a"*40,"dem":{"source":"terrarium","step":10,"zoom":13,"padding":0},"preview":{"primaryCourse":None,"includeGradeReview":False}}
    data={"schemaVersion":2,"resort":name,"bbox":cfg["bbox"],"origin":{"lon":6.05,"lat":44.05},"grids":[grid],"courses":[route],"pistes":[{"n":"Main run","d":1,"p":route["p"]}],"lifts":[],"buildings":[{"x":5,"z":5}],"mask":{},"streets":[],"pois":[],"startPoints":[]}
    return cfg,data

class GeneratorTests(unittest.TestCase):
    def test_two_profiles_and_variable_route_counts(self):
        for name,slug,count in [("Test Alpha","test-alpha",1),("Test Beta","test-beta",3)]:
            cfg,raw=fixture(name,slug)
            for i in range(1,count):
                extra=copy.deepcopy(raw["courses"][0]);extra.update(id=str(i),n="Run "+str(i))
                raw["courses"].append(extra)
            before=copy.deepcopy(raw)
            result=prepare_data(raw,cfg)
            self.assertEqual(result["resort"],name)
            self.assertEqual(len(result["courses"]),count)
            self.assertEqual(result["integration"]["primaryCourse"],"Main run")
            self.assertEqual(result["buildings"],raw["buildings"])
            self.assertEqual(raw,before)
    def test_grade_review_and_invalid_axis(self):
        cfg,raw=fixture("Test Alpha","test-alpha")
        flagged=copy.deepcopy(raw["courses"][0]);flagged.update(id="flag",n="Flagged",needsGradeReview=True)
        raw["courses"].insert(0,flagged)
        self.assertEqual(len(prepare_data(raw,cfg)["courses"]),1)
        cfg["preview"]["includeGradeReview"]=True
        self.assertEqual(len(prepare_data(raw,cfg)["courses"]),2)
        with self.assertRaises(ValueError): choose_axis(raw,"Flagged")
    def test_reject_mismatched_data(self):
        cfg,raw=fixture("Test Alpha","test-alpha")
        raw["resort"]="Test Beta"
        with self.assertRaises(ValueError): prepare_data(raw,cfg)
    def test_profile_and_path(self):
        cfg,_=fixture("Test Alpha","test-alpha")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"config.json";p.write_text(json.dumps(cfg))
            self.assertEqual(load_config(p)["build"]["maxCourses"],8)
            cfg["slug"]="../unsafe";p.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError): load_config(p)
        self.assertEqual(load_config(profile_path("les-deux-alpes"))["preview"]["primaryCourse"],"Thuit 2")
        with self.assertRaises(ValueError): profile_path("../unsafe")

if __name__=="__main__": unittest.main()
