import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_shared_site import extract

def fixture(name):
    return '<html><style>body{background:url(data:image/png;base64,abc)}</style><script>\nconst FR_RESORT = {"name":"'+name+'"};\nconst AVZ_DATA = {};\nlet boot=1;\n</script><script>\nconsole.log(boot);\n</script></html>'

class SharedTests(unittest.TestCase):
    def test_equal_assets(self):
        a,ar,an=extract(fixture("A"));b,br,bn=extract(fixture("B"))
        self.assertEqual(ar,br);self.assertEqual(an,bn)
        self.assertIn('{"name":"A"}',a);self.assertIn('{"name":"B"}',b)
        self.assertNotEqual(a,b)
        self.assertIn('<script src="../../assets/engine-',a)
        self.assertNotIn('console.log(boot)',a)
    def test_v2_early_locale_stays_inline(self):
        early="<script>let language=navigator.language;</script>"
        source=fixture("A").replace("<html>","<html>"+early)
        online,resources,names=extract(source)
        self.assertIn(early,online)
        self.assertEqual(resources,extract(fixture("A"))[1])
    def test_reject_relative_css(self):
        with self.assertRaises(ValueError):extract(fixture("A").replace("data:image/png;base64,abc","../image.png"))
    def test_reject_unknown_script_structure(self):
        with self.assertRaises(ValueError):extract(fixture("A").replace("<script>","<script type='module'>",1))
    def test_reject_script_location_dependency(self):
        with self.assertRaises(ValueError):extract(fixture("A").replace("console.log(boot)","console.log(document.currentScript)"))
if __name__=="__main__":unittest.main()
