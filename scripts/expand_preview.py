#!/usr/bin/env python3
"""Expand the existing engineering preview to all eight real OSM candidates."""
import argparse, json, re
from pathlib import Path

def expand(src, data):
    def rep(old,new):
        if src.count(old)!=1: raise ValueError('anchor mismatch: '+old[:100])
        return src.replace(old,new,1)
    assert data['resort']=='Les Deux Alpes' and data['integration']['primaryCourse']=='Thuit 2'
    courses=data['courses']; assert len(courses)==8 and len({c['id'] for c in courses})==8
    assert all(c['connected'] and len(c['p'])>=2 for c in courses)
    for c in courses:
        c['sub']='Experimental route — DEM grade review pending' if c['needsGradeReview'] else 'Experimental timed run — not gameplay validated'
    data['pistes']=[p for p in data['pistes'] if p['d'] in (0,1,2,3) and len(p['p'])>=2]
    for p in data['pistes']: p['n']=p['n'] or ''
    data['lifts']=[l for l in data['lifts'] if len(l['p'])>=2 and l['n'] and not l['clipped']]
    data['integration']['status']='multi-route engineering preview; all courses experimental; no certified gameplay'
    old=re.search(r'^const AVZ_DATA = .*?;$',src,re.M)
    if not old: raise ValueError('missing data')
    src=rep(old.group(), 'const AVZ_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')+';')
    # Global axes stay fixed; the route picker follows per-course arc length rather than rebuilding the axis.
    src=rep('const Ps = (D.pistes || []).filter(p => p.n === "Thuit 2" && p.p && p.p.length >= 2);','const Ps = (D.pistes || []).filter(p => D.courses.some(c => !c.needsGradeReview && c.n === p.n) && p.p && p.p.length >= 2);')
    src=rep('Math.max(-7, Math.min(7, bv[k] - g[ii]))','Math.max(-2, Math.min(2, bv[k] - g[ii]))')
    src=rep('Math.max(-6, Math.min(6, Dl[o] + num[o] / den[o] * wmx[o]))','Math.max(-2, Math.min(2, Dl[o] + num[o] / den[o] * wmx[o]))')
    src=rep('if (gradeY && sg > -30 && sg < L + 30)', 'if (false && gradeY && sg > -30 && sg < L + 30)') # avoid preferential main-axis grade overlay
    src=rep("{ const c = D.courses[0], p = c.p[0]; starts.push({n:c.n+' start', x:p[0], z:p[1], alt:Math.round(c.a0)}); }", "{ for (const c of D.courses) { const p=c.p[0]; starts.push({n:c.n+' start',x:p[0],z:p[1],alt:Math.round(c.a0)}); } }")
    src=rep("const landmarks=[['THUIT 2',startReal(starts[0]),0,20]];", "const landmarks=[];")
    src=src.replace('THUIT 2 · FRENCH ALPS','8 ROUTES · FRENCH ALPS').replace('<small>THUIT 2</small>','<small>8 ROUTES · PREVIEW</small>').replace('Les Deux Alpes · Thuit 2','Les Deux Alpes · 8 routes')
    src=rep("'Timed line with start and finish markers';", "(c.needsGradeReview?'EXPERIMENTAL · DEM grade review pending · PB disabled':'Experimental timed run · gameplay not yet validated');")
    src=rep("'Timed run · '+RUN_LEVEL[it.c.d]", "(it.c.needsGradeReview?'Grade review pending · ':'Test run · ')+RUN_LEVEL[it.c.d]")
    src=rep("if (runRescue) pbLine =", "if (course.needsGradeReview) pbLine = '<p class=\"finish-pb\">Experimental DEM grade review · PB disabled</p>'; else if (runRescue) pbLine =")
    src=src.replace('l2a-preview-pb','l2a-multiroute-preview-pb')
    src=src.replace('ENGINE PREVIEW · 30 m DEM','8-ROUTE ENGINE PREVIEW · 30 m DEM')
    return src

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preview',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.resolve()==a.preview.resolve(): raise ValueError('refuse to overwrite input')
    a.out.write_text(expand(a.preview.read_text(),json.loads(a.data.read_text())),encoding='utf-8')
if __name__=='__main__': main()
