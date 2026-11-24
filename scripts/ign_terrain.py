#!/usr/bin/env python3
"""Bounded numeric RGE ALTI WMS experiment; fail closed, never use RGB or fallback DEM."""
import hashlib
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

WMS="https://data.geopf.fr/wms-r"
LAYER="ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES"
ALT="https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json"
CREDIT="IGN RGE ALTI / Géoplateforme, Licence Ouverte 2.0; elevations in metres, altitude normale (NGF-IGN69 for metropolitan mainland); output spacing is not source accuracy."
MAX_BYTES=20_000_000

def request(base,params,limit=MAX_BYTES):
    url=base+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"FR-Ski-Simulator/1.2 (bounded elevation integration test)"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req,timeout=60) as response:
                raw=response.read(limit+1)
            if len(raw)>limit: raise ValueError("response exceeds size cap")
            return raw,url
        except (OSError,TimeoutError):
            if attempt: raise
            time.sleep(2)

def grid_request(cfg,step,padding,pr):
    # Cover all local-grid samples, with interpolation margin and projected bbox.
    from rasterio.warp import transform_bounds
    w,z0,e,z1=pr.bounds(cfg["bbox"])
    w=math.floor((w-padding)/step)*step-3*step
    z0=math.floor((z0-padding)/step)*step-3*step
    e=math.ceil((e+padding)/step)*step+4*step
    z1=math.ceil((z1+padding)/step)*step+4*step
    lon0,lat1=pr.inverse(w,z0);lon1,lat0=pr.inverse(e,z1)
    b=transform_bounds("EPSG:4326","EPSG:2154",lon0,lat0,lon1,lat1,densify_pts=21)
    west,south=map(lambda n: math.floor(n/step)*step,b[:2])
    east,north=map(lambda n: math.ceil(n/step)*step,b[2:])
    width,height=round((east-west)/step),round((north-south)/step)
    if min(width,height)<4 or max(width,height)>1500 or width*height>1_500_000:
        raise ValueError("WMS request exceeds bounded test size")
    return (west,south,east,north),width,height

def lambert93_alias(crs):
    """Recognize only the observed WMS Lambert-93 alias with missing datum label."""
    if crs is None or 'PROJCS["EPSG:2154"' not in crs.to_wkt():
        return False
    p=crs.to_dict()
    expected={"lat_0":46.5,"lon_0":3,"lat_1":49,"lat_2":44,"x_0":700000,"y_0":6600000}
    return (p.get("proj")=="lcc" and p.get("units")=="m"
        and p.get("ellps") in ("WGS84","GRS80")
        and all(k in p and abs(float(p[k])-v)<1e-8 for k,v in expected.items())
        and not p.get("towgs84") and not p.get("nadgrids"))

def inspect_tiff(raw,bbox,width,height,step,allow_untagged=False):
    import numpy as np
    from rasterio.io import MemoryFile
    from rasterio.crs import CRS
    from rasterio.transform import Affine
    if raw[:4] not in (b"II*\x00",b"MM\x00*"):
        raise ValueError("IGN response is not a numeric GeoTIFF: "+raw[:160].decode("utf-8","replace"))
    with MemoryFile(raw) as mem, mem.open() as ds:
        if ds.driver!="GTiff" or ds.count!=1 or ds.dtypes[0] not in ("float32","float64","int16","int32"):
            raise ValueError("not a single-band numeric elevation TIFF")
        actual={"crs":str(ds.crs),"bounds":list(ds.bounds),"dimensions":[ds.width,ds.height],"transform":list(ds.transform),"dtype":ds.dtypes[0]}
        print("WMS TIFF metadata:",json.dumps(actual),flush=True)
        if (ds.width,ds.height)!=(width,height):
            raise ValueError("unexpected GeoTIFF dimensions: "+json.dumps(actual))
        # GetMap defines bounds and pixel size even if its TIFF omits all geotags.
        # Never override conflicting explicit coordinates; untagged images must
        # still pass numeric checks and independent IGN elevation comparisons.
        untagged=ds.crs is None and ds.transform==Affine.identity()
        if untagged and not allow_untagged:
            raise ValueError("missing GeoTIFF georeferencing")
        alias=not untagged and ds.crs!=CRS.from_epsg(2154) and lambert93_alias(ds.crs)
        if not untagged:
            if ds.crs!=CRS.from_epsg(2154) and not alias:
                raise ValueError("unexpected GeoTIFF CRS: "+json.dumps(actual))
            if max(abs(a-b) for a,b in zip(ds.bounds,bbox))>0.05 or max(abs(a-step) for a in ds.res)>0.05:
                raise ValueError("GeoTIFF bounds or resolution mismatch: "+json.dumps(actual))
        values=ds.read(1,masked=True)
        if np.ma.getmaskarray(values).any() or not np.isfinite(values).all():
            raise ValueError("missing elevations; no fallback permitted")
        if float(values.min())< -100 or float(values.max())>5000 or float(values.max()-values.min())<50:
            raise ValueError("implausible alpine elevation values")
        return {"dtype":ds.dtypes[0],"crs":str(ds.crs),"bounds":list(ds.bounds),"dimensions":[width,height],"pixelSize":list(ds.res),"range":[float(values.min()),float(values.max())],"georeferencing":"request-derived pending point checks" if untagged else ("Lambert-93 alias pending point checks" if alias else "embedded")}

def verify_points(dem,pr,step):
    # Compare nine actual grid nodes to the independent point elevation endpoint.
    nx,nz=dem["nx"],dem["nz"]
    indices=[(round((nx-1)*u),round((nz-1)*v)) for v in (.2,.5,.8) for u in (.2,.5,.8)]
    points=[pr.inverse(dem["x0"]+i*step,dem["z0"]+j*step) for i,j in indices]
    params={"lon":"|".join("%.7f"%p[0] for p in points),"lat":"|".join("%.7f"%p[1] for p in points),"resource":"ign_rge_alti_wld","zonly":"true"}
    raw,url=request(ALT,params,100000)
    actual=json.loads(raw)["elevations"]
    if len(actual)!=len(points) or any(v is None or not math.isfinite(float(v)) or not -100<float(v)<5000 for v in actual):
        raise ValueError("independent IGN point comparison unavailable")
    comparisons=[{"lon":p[0],"lat":p[1],"raster":dem["h"][j*nx+i],"point":float(v),"absError":abs(dem["h"][j*nx+i]-float(v))}
        for p,(i,j),v in zip(points,indices,actual)]
    maxerr=max(c["absError"] for c in comparisons); mean=sum(c["absError"] for c in comparisons)/len(comparisons)
    # Coarser WMS sampling can differ on steep slopes. Explicit engineering gates,
    # not a claim of survey accuracy. Near must agree more closely.
    max_limit=max(12,1.5*step);mean_limit=max(4,0.4*step)
    if maxerr>max_limit or mean>mean_limit:
        raise ValueError(f"IGN point cross-check failed: max {maxerr:.2f} m, mean {mean:.2f} m")
    return {"pointResource":"ign_rge_alti_wld","url":url,"meanAbsError":mean,"maxAbsError":maxerr,"thresholds":[mean_limit,max_limit],"samples":comparisons}

def fetch_ign_layer(cfg,step,padding,skill,work,role):
    from layered_terrain import sample_raster
    sys.path.insert(0,str(skill/"scripts"))
    from common import Projection
    pr=Projection(dict(zip(("lon","lat"),cfg["origin"])))
    bbox,width,height=grid_request(cfg,step,padding,pr)
    params={"SERVICE":"WMS","VERSION":"1.3.0","REQUEST":"GetMap","LAYERS":LAYER,"STYLES":"normal","FORMAT":"image/geotiff","CRS":"EPSG:2154","BBOX":",".join(map(str,bbox)),"WIDTH":width,"HEIGHT":height}
    raw,url=request(WMS,params)
    path=Path(work)/(role+"-ign.tif");path.write_bytes(raw)
    info=inspect_tiff(raw,bbox,width,height,step,allow_untagged=True)
    sample_path=path
    if info["georeferencing"]!="embedded":
        import rasterio
        from rasterio.transform import from_bounds
        sample_path=Path(work)/(role+"-georeferenced-ign.tif")
        with rasterio.open(path) as ds:
            profile=ds.profile.copy()
            profile.update(crs="EPSG:2154",transform=from_bounds(*bbox,width,height))
            with rasterio.open(sample_path,"w",**profile) as dst:
                dst.write(ds.read())
    dem=sample_raster(sample_path,CREDIT,cfg,step,padding,skill)
    check=verify_points(dem,pr,step)
    if info["georeferencing"]=="request-derived pending point checks":
        info["georeferencing"]=info["georeferencing"].replace(" pending point checks","; independent point checks passed")
    meta=dem["_meta"]
    meta.update(requestedSource="ign-wms",sourceCounts={"ign-wms":len(dem["h"])},
        wms={"url":url,"layer":LAYER,"sha256":hashlib.sha256(raw).hexdigest(),"numericRaster":info},
        pointComparison=check,warning="WMS output spacing; independent point checks are not a native-resolution or survey-accuracy guarantee.")
    print(json.dumps({"role":role,"source":"IGN numeric WMS","step":step,"dimensions":[dem["nx"],dem["nz"]],"pointComparison":{"meanAbsError":check["meanAbsError"],"maxAbsError":check["maxAbsError"]}},ensure_ascii=False),flush=True)
    return dem
