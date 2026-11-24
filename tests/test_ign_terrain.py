"""Synthetic raster format tests; no live IGN claims."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds
from ign_terrain import inspect_tiff

def tiff(dtype="float32",count=1,crs="EPSG:2154",nodata=None,missing=False):
    bounds=(900000,6400000,900050,6400050)
    vals=np.linspace(1400,1800,100).reshape(10,10).astype(dtype)
    if missing: vals[0,0]=nodata
    with MemoryFile() as mem:
        with mem.open(driver="GTiff",width=10,height=10,count=count,dtype=dtype,crs=crs,transform=from_bounds(*bounds,10,10),nodata=nodata) as ds:
            for n in range(1,count+1): ds.write(vals,n)
        return mem.read()

class IgnTests(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(inspect_tiff(tiff(),(900000,6400000,900050,6400050),10,10,5)["dtype"],"float32")
    def test_reject_rgb(self):
        with self.assertRaises(ValueError): inspect_tiff(tiff(count=3),(900000,6400000,900050,6400050),10,10,5)
    def test_reject_missing(self):
        with self.assertRaises(ValueError): inspect_tiff(tiff(nodata=-9999,missing=True),(900000,6400000,900050,6400050),10,10,5)
    def test_reject_wrong_location(self):
        with self.assertRaises(ValueError): inspect_tiff(tiff(),(900100,6400000,900150,6400050),10,10,5)
    def test_reject_non_tiff(self):
        with self.assertRaises(ValueError): inspect_tiff(b"<ServiceException>",(0,0,50,50),10,10,5)

if __name__=="__main__": unittest.main()
