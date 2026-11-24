#!/usr/bin/env python3
"""Schema v2 -> legacy AVZ data, for bounded integration tests only."""
import argparse
import base64
import copy
import json
import math
import struct
from pathlib import Path


def f32(values):
    return base64.b64encode(struct.pack('<%df' % len(values), *values)).decode('ascii')


def sampler(g):
    nx,nz,step=g['nx'],g['nz'],g['step']
    raw=base64.b64decode(g['h'],validate=True)
    if g['fmt']!='f32' or len(raw)!=nx*nz*4 or min(nx,nz)<4 or step<=0:
        raise ValueError('invalid f32 grid')
    a=struct.unpack('<%df'%(nx*nz),raw)
    if not all(map(math.isfinite,a)):
        raise ValueError('non-finite DEM')
    def height(x,z):
        u,v=(x-g['x0'])/step,(z-g['z0'])/step
        if not (0<=u<=nx-1 and 0<=v<=nz-1):
            raise ValueError('route outside DEM')
        i,j=min(int(u),nx-2),min(int(v),nz-2)
        t,q=u-i,v-j
        return (1-q)*((1-t)*a[j*nx+i]+t*a[j*nx+i+1])+q*((1-t)*a[(j+1)*nx+i]+t*a[(j+1)*nx+i+1])
    return height


def adapt(data, course_name):
    if data.get('schemaVersion')!=2 or not data.get('resort'):
        raise ValueError('expected a named schema v2 resort')
    matches=[c for c in data['courses'] if c['n']==course_name and c['connected'] and not c['needsGradeReview']]
    if len(matches)!=1: raise ValueError('need one connected, unflagged course')
    c=matches[0]; p=c['p']
    if len(p)<2: raise ValueError('course too short')
    x0,z0=p[0]; ex,ez=p[-1][0]-x0,p[-1][1]-z0
    span=math.hypot(ex,ez)
    if not math.isfinite(span) or span<10: raise ValueError('invalid or short route axis')
    if not all(len(q)==2 and all(map(math.isfinite,q)) for q in p): raise ValueError('invalid course coordinates')
    dx,dz=ex/span,ez/span
    def game(q):
        x,z=q[0]-x0,q[1]-z0
        return [-dz*x+dx*z,-(dx*x+dz*z)]
    def real(q):
        x,z=q; return [x0-dx*z-dz*x,z0-dz*z+dx*x]
    route=[game(q) for q in p]; ss=[-q[1] for q in route]
    if any(b<=a for a,b in zip(ss,ss[1:])):
        raise ValueError('route not strictly monotone along legacy axis')
    L=math.floor(span)
    if L<10: raise ValueError('route too short')
    h=sampler(data['grids'][0]); alt0=h(*p[0]); cx=[]; gy=[]; i=0
    for s in range(L+1):
        while i+1<len(ss)-1 and ss[i+1]<s: i+=1
        t=(s-ss[i])/(ss[i+1]-ss[i]); x=route[i][0]*(1-t)+route[i+1][0]*t
        cx.append(x); gy.append(h(*real([x,-s]))-alt0)
    if gy[-1]>=gy[0]: raise ValueError('main route does not descend')
    # No artificial grading: gy follows the real sampled DEM; the engine's grade overlay must be reviewed.
    out=copy.deepcopy(data); out.update(P0=[x0,z0],dir=[dx,dz],alt0=alt0,L=L,meanSlope=(gy[0]-gy[-1])/L,cx=f32(cx),hw=f32([15.0]*(L+1)),gy=f32(gy),segs=[{'name':course_name,'s0':0,'type':'bowl'}])
    # Legacy renderer dereferences three grids. Duplicates do not add resolution or coverage.
    if len(out['grids'])==1: out['grids']*=3
    for k in ('pistes','lifts','courses'):
        for feature in out[k]:
            orig=feature['p']; feature['p']=[game(q) for q in orig]
            if any(math.dist(q,real(v))>1e-7 for q,v in zip(orig,feature['p'])): raise ValueError('coordinate round-trip failed')
    # Forest/mask/buildings/POIs/streets/startPoints stay in real X/Z.
    out['integration']={'status':'data-only; not a playable build','primaryCourse':course_name,'legacyLongitudinalLength':L,'halfWidthEstimatedM':15,'duplicateGrids':len(data['grids'])==1,'gradingApplied':False,'warning':'No extended terrain; do not enable free travel until bounds and scene overrides are audited.'}
    return out


def choose_axis(data, preferred=None):
    """Use an explicitly configured axis, or first compatible unflagged candidate."""
    if preferred is not None:
        return adapt(data, preferred)
    failures=[]
    for c in data.get("courses",[]):
        if not c.get("connected") or c.get("needsGradeReview"): continue
        try:
            return adapt(data,c["n"])
        except ValueError as exc:
            failures.append(c["n"]+": "+str(exc))
    raise ValueError("No compatible course axis: "+"; ".join(failures))


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--data',type=Path,required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--course',default='Thuit 2'); a=p.parse_args()
    d=adapt(json.loads(a.data.read_text()),a.course)
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'primaryCourse':a.course,'L':d['L'],'alt0':d['alt0'],'meanSlope':d['meanSlope'],'grids':len(d['grids']),'bytes':a.out.stat().st_size},ensure_ascii=False))

if __name__=='__main__': main()
