#!/usr/bin/env python3
"""Deterministic synthetic GIS fixture and independent QA; Python standard library."""
import csv, json, math, random, subprocess, argparse
from pathlib import Path
from collections import Counter, defaultdict, deque
ROOT=Path(__file__).resolve().parents[1]
SRID=32638
TOL=2.0
BASE=(670000,2740000)
def xy(x,y): return [BASE[0]+x,BASE[1]+y]
def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def length(c): return sum(dist(a,b) for a,b in zip(c,c[1:]))
def point_line(p,c):
    result=float('inf')
    for a,b in zip(c,c[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1]; den=dx*dx+dy*dy
        t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
        result=min(result,dist(p,[a[0]+t*dx,a[1]+t*dy]))
    return result

def fixture():
    rng=random.Random(42); pipes=[]
    def add(code,a,b,diameter=None,terminal=False):
        pipes.append(dict(row_id=len(pipes)+1,asset_id=code,diameter_mm=diameter if diameter is not None else rng.choice([100,150,200]),terminal_end=terminal,coords=[xy(*a),xy(*b)]))
    for y in range(4):
        for x in range(4): add(f'H{x}{y}',(x*100,y*100),((x+1)*100,y*100),terminal=x==3)
    for x in range(4):
        for y in range(3): add(f'V{x}{y}',(x*100,y*100),(x*100,(y+1)*100))
    # Known anomalies: explicit ground truth is separate from the checker.
    pipes[0]['asset_id']='DUP-ID'; pipes[1]['asset_id']='DUP-ID'
    pipes[2]['diameter_mm']=None; pipes[3]['diameter_mm']=-100
    add('ZERO',(600,300),(600,300))
    add('DUP-GEOM',(0,100),(100,100))
    add('GAP',(400,0),(499,0),terminal=True)
    add('GAP-NEXT',(500,0),(600,0),terminal=True)
    add('ISLAND',(600,100),(700,100),terminal=True)
    # A crossing without an endpoint junction must remain disconnected.
    add('CROSSING',(150,-50),(150,50),terminal=True)
    valves=[dict(row_id=1,asset_id='VALVE-01',coords=xy(50,0)),dict(row_id=2,asset_id='VALVE-02',coords=xy(50,10))]
    sources=[dict(row_id=1,asset_id='SOURCE-01',coords=xy(0,0))]
    return pipes,valves,sources

def check(pipes,valves,sources):
    issues=[]
    def issue(code,p,description,severity='high',layer='pipes'):
        c=p['coords']; pos=c[0] if layer=='pipes' else c
        issues.append(dict(issue_id=len(issues)+1,code=code,layer=layer,row_id=p['row_id'],asset_id=p['asset_id'],severity=severity,description=description,coords=pos))
    counts=Counter(p['asset_id'] for p in pipes)
    for p in pipes:
        if not p['asset_id']: issue('MISSING_ID',p,'Required asset ID is missing')
        elif counts[p['asset_id']]>1: issue('DUPLICATE_ID',p,'Asset ID occurs more than once')
        d=p['diameter_mm']
        if d is None: issue('MISSING_DIAMETER',p,'Required diameter is missing')
        elif d<=0: issue('INVALID_DIAMETER',p,'Diameter must be positive')
        if length(p['coords'])==0: issue('ZERO_LENGTH',p,'Pipe has zero length')
    seen={}
    for p in pipes:
        c=p['coords']; key=min(tuple(map(tuple,c)),tuple(map(tuple,reversed(c))))
        if key in seen: issue('DUPLICATE_GEOMETRY',p,f"Same line as row {seen[key]}")
        else: seen[key]=p['row_id']
    valid=[p for p in pipes if length(p['coords'])>0]
    for i,p in enumerate(valid):
        for q in valid[i+1:]:
            ds=[dist(a,b) for a in [p['coords'][0],p['coords'][-1]] for b in [q['coords'][0],q['coords'][-1]]]
            if any(0<d<=TOL for d in ds): issue('NEAR_GAP',q,f"Endpoint within {TOL} m of pipe row {p['row_id']}; review before snapping",'medium')
    # Exact endpoint graph. Interior crossings and near gaps do not connect.
    graph=defaultdict(set)
    for p in valid:
        a,b=map(tuple,[p['coords'][0],p['coords'][-1]]); graph[a].add(b); graph[b].add(a)
    reached=set(tuple(s['coords']) for s in sources); queue=deque(reached)
    while queue:
        for n in graph[queue.popleft()]:
            if n not in reached: reached.add(n); queue.append(n)
    for p in valid:
        if tuple(p['coords'][0]) not in reached: issue('DISCONNECTED',p,'No endpoint path to a source')
    for v in valves:
        if min(point_line(v['coords'],p['coords']) for p in valid)>TOL: issue('OFF_NETWORK_VALVE',v,f'Valve farther than {TOL} m from every usable pipe','high','valves')
    return issues

def geojson(name,rows,kind):
    features=[]
    for r in rows:
        props={k:v for k,v in r.items() if k!='coords'}
        features.append(dict(type='Feature',properties=props,geometry=dict(type=kind,coordinates=r['coords'])))
    obj=dict(type='FeatureCollection',name=name,crs=dict(type='name',properties=dict(name=f'EPSG:{SRID}')),features=features)
    (ROOT/'data'/f'{name}.geojson').write_text(json.dumps(obj,indent=2)+'\n')

def render(pipes,issues):
    def pos(p): return (70+(p[0]-BASE[0])*1.1,520-(p[1]-BASE[1])*1.1)
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="720" viewBox="0 0 1100 720">','<rect width="1100" height="720" fill="#101d30"/>','<g font-family="Arial,sans-serif" fill="#e9f1fa">','<text x="48" y="58" font-size="29" font-weight="bold">Riyadh | Water Network Quality</text>','<text x="48" y="90" font-size="16" fill="#a5bbd1">SYNTHETIC DEMONSTRATION — not an actual utility network</text>']
    for p in pipes:
        a,b=map(pos,[p['coords'][0],p['coords'][-1]])
        s.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#4bb8cf" stroke-width="3"/>')
    for p in issues:
        x,y=pos(p['coords']); color='#ffbd59' if p['severity']=='medium' else '#ff6b78'
        s.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{color}" fill-opacity="0.75"/>')
    x,y=pos(xy(0,0)); s.append(f'<rect x="{x-6}" y="{y-6}" width="12" height="12" fill="#7de0a1"/>')
    s+=['<text x="870" y="155" font-size="18" font-weight="bold">QA findings</text>']
    for i,(code,n) in enumerate(sorted(Counter(p['code'] for p in issues).items())):
        s.append(f'<text x="870" y="{190+i*28}" font-size="12">{code}: {n}</text>')
    s+=['<text x="48" y="610" font-size="14">Cyan: pipes   •   Red: high priority   •   Amber: review gap   •   Green: source</text>','<path d="M70 650 H180 M70 645 V655 M180 645 V655" stroke="white" stroke-width="2"/>','<text x="92" y="678" font-size="13">100 metres</text>','<text x="730" y="655" font-size="13">EPSG:32638 • North ↑ • Seed 42</text>','<text x="48" y="705" font-size="12" fill="#a5bbd1">Flags may overlap. Exact endpoint connectivity; crossings alone do not form junctions.</text>','</g></svg>']
    (ROOT/'figures'/'overview.svg').write_text('\n'.join(s))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--ogr2ogr'); args=parser.parse_args()
    pipes,valves,sources=fixture(); before=check(pipes,valves,sources)
    # Only deterministic administrative repairs; retain uncertain geometry for review.
    cleaned=json.loads(json.dumps(pipes)); cleaned[0]['asset_id']='H00'; cleaned[1]['asset_id']='H10'
    after=check(cleaned,valves,sources)
    for name,rows,kind in [('pipes_raw',pipes,'LineString'),('pipes_clean',cleaned,'LineString'),('valves',valves,'Point'),('sources',sources,'Point'),('qa_before',before,'Point'),('qa_after',after,'Point')]: geojson(name,rows,kind)
    with (ROOT/'data'/'repair_log.csv').open('w') as f:
        w=csv.writer(f); w.writerow(['row_id','field','old_value','new_value','reason']); w.writerows([[1,'asset_id','DUP-ID','H00','Recover known ID from synthetic fixture specification'],[2,'asset_id','DUP-ID','H10','Recover known ID from synthetic fixture specification']])
    report=dict(seed=42,srid=SRID,tolerance_m=TOL,pipes=len(pipes),valves=len(valves),before=dict(sorted(Counter(i['code'] for i in before).items())),after=dict(sorted(Counter(i['code'] for i in after).items())),before_total=len(before),after_total=len(after))
    (ROOT/'data'/'summary.json').write_text(json.dumps(report,indent=2)+'\n'); render(pipes,before)
    if args.ogr2ogr:
        gpkg=ROOT/'data'/'network.gpkg'
        if gpkg.exists(): gpkg.unlink()
        for n,name in enumerate(['pipes_raw','pipes_clean','valves','sources','qa_before','qa_after']):
            subprocess.run([args.ogr2ogr,'-f','GPKG',str(gpkg),str(ROOT/'data'/f'{name}.geojson'),'-nln',name,'-a_srs',f'EPSG:{SRID}']+(['-update'] if n else []),check=True)
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
