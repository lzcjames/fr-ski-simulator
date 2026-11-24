#!/usr/bin/env python3
"""Build a bounded Les Deux Alpes engineering preview from authorized template + legacy JSON."""
import argparse, json, re
from pathlib import Path

def build(src, data):
    def rep(old,new):
        nonlocal src
        if src.count(old)!=1: raise ValueError('anchor count mismatch: '+old[:100])
        src=src.replace(old,new,1)
    def line(prefix,new):
        old=[x for x in src.splitlines() if x.startswith(prefix)]
        if len(old)!=1: raise ValueError('line anchor mismatch: '+prefix)
        rep(old[0],new)
    assert data['resort']=='Les Deux Alpes' and data['integration']['primaryCourse']=='Thuit 2'
    data['courses']=[c for c in data['courses'] if c['n']=='Thuit 2' and not c['needsGradeReview']]
    assert len(data['courses'])==1
    data['pistes']=[p for p in data['pistes'] if p['d'] in (0,1,2,3) and len(p['p'])>=2]
    for p in data['pistes']:
        p['n']=p['n'] or ''
    data['lifts']=[l for l in data['lifts'] if len(l['p'])>=2 and l['n'] and not l['clipped']]
    data['integration']['status']='engineering preview; coarse terrain; gameplay not certified'
    line('const AVZ_DATA = ', 'const AVZ_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')+';')
    for p in ('AVZ_DATA.pois =','AVZ_DATA.streets =','AVZ_DATA.courses.splice('): line(p,'// Removed old-resort data mutation.')
    m=re.search(r'const AVZ_FUN_ROUTES = \[.*?\n\];',src,re.S)
    if not m: raise ValueError('park anchor missing')
    rep(m.group(),'const AVZ_FUN_ROUTES = [];')
    rep('const originals = D.courses.filter(c => !c.fun && !c.town && !/^town/.test(c.id));','const originals = []; // No invented park or piste features in this preview.')
    line('  const SPOTS = ', '  const SPOTS = [];')
    line("  starts.push({ n: '小镇上方", "  { const c = D.courses[0], p = c.p[0]; starts.push({n:c.n+' start', x:p[0], z:p[1], alt:Math.round(c.a0)}); }")
    line("    const landmarks=[['AVORIAZ'", "    const landmarks=[['THUIT 2',startReal(starts[0]),0,20]];")
    old=re.search(r'<div class="ld-scene">.*?(?=<div class="ld-snow">)',src,re.S)
    if not old: raise ValueError('loading art anchor missing')
    rep(old.group(),'<div class="ld-scene" style="background:linear-gradient(145deg,#1a344b,#07131d 70%)"></div>')
    src=src.replace('FRANCE / PORTES DU SOLEIL','FRANCE / OISANS').replace('1800 M · FRENCH ALPS','THUIT 2 · FRENCH ALPS')
    src=src.replace('Avoriaz 滑雪 · 基于 雪迹 Cold Smoke','Les Deux Alpes · Cold Smoke / Avoriaz')
    src=src.replace('>Avoriaz<','>Les Deux Alpes<').replace('Avoriaz · 1800 m','Les Deux Alpes · Thuit 2').replace('Avoriaz · Mountain map','Les Deux Alpes · Mountain map')
    src=src.replace("<strong>Les Deux Alpes</strong><small>1800 M</small>","<strong>Les Deux Alpes</strong><small>THUIT 2</small>")
    src=src.replace("resort: 'Avoriaz', wetBelow: 1420", "resort: 'Les Deux Alpes', wetBelow: 1650")
    rep('const Ps = (D.pistes || []).filter(p => p.p && p.p.length >= 2);','const Ps = (D.pistes || []).filter(p => p.n === "Thuit 2" && p.p && p.p.length >= 2);')
    rep('h += (hg - h) * w;', 'h += Math.max(-2, Math.min(2, hg - h)) * w;')
    src=src.replace("'avz-pb'","'l2a-preview-pb'").replace("'avz-onboard'","'l2a-preview-onboard'")
    line('  const EN_NAMES = ', '  const EN_NAMES = {};')
    old=[x for x in src.splitlines() if x.startswith('  const D_LOOK=')][0]
    tail=old[old.index(',D_LV='):];rep(old,'  const D_LOOK={}'+tail)
    # Warning only: gameplay boundaries remain unaudited.
    warn='<div style="position:fixed;z-index:99999;top:4px;left:50%;transform:translateX(-50%);padding:4px 9px;background:#07131dcc;color:#fff;font:11px system-ui;pointer-events:none;text-align:center">Les Deux Alpes · ENGINE PREVIEW · 30 m DEM · OSM / Terrarium · Avoriaz / Cold Smoke adaptation · Not for navigation</div>'
    if '</body>' in src: rep('</body>',warn+'</body>')
    else: src+=warn
    return src

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--template',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.resolve()==a.template.resolve(): raise ValueError('refuse to overwrite template')
    a.out.write_text(build(a.template.read_text(),json.loads(a.data.read_text())),encoding='utf-8')
    print(a.out, a.out.stat().st_size)
