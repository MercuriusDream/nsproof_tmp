#!/usr/bin/env python3
from pathlib import Path
import json, math, hashlib
import numpy as np

ROOT = Path.cwd()
OUT = ROOT / 'rp4_label_output'
OUT.mkdir(exist_ok=True)

values_files = [p for p in ROOT.rglob('values.json') if 'rp4' in str(p).lower()]
facets_files = [p for p in ROOT.rglob('facets.json') if 'rp4' in str(p).lower()]

if values_files:
    values = list(map(int, json.loads(values_files[0].read_text())))
elif facets_files:
    facets = json.loads(facets_files[0].read_text())
    # Accept either a raw list or a dictionary field.
    if isinstance(facets, dict):
        facets = facets.get('facets') or facets.get('maximal_facets') or facets.get('maximal_faces')
    # Normalize 1-based vertex labels to 0-based.
    flat = [int(v) for F in facets for v in F]
    shift = 1 if min(flat) == 1 else 0
    facets = [tuple(sorted(int(v)-shift for v in F)) for F in facets]
    n = max(max(F) for F in facets) + 1
    faces = set()
    for F in facets:
        for mask in range(1, 1 << len(F)):
            face = 0
            for j, v in enumerate(F):
                if mask >> j & 1:
                    face |= 1 << v
            faces.add(face)
    values = [0] * (1 << n)
    for S in range(1 << n):
        values[S] = sum((1 if (f.bit_count() & 1) else -1) for f in faces if f & ~S == 0)
else:
    raise SystemExit('No RP4 values.json or facets.json produced by rp4_exact.py')

n = (len(values)).bit_length() - 1
assert 1 << n == len(values)
classes = sorted(set(values))
assert values[0] == 0
assert all(values[1 << i] == 1 for i in range(n))

class_coeff = {}
for val in classes:
    a = np.fromiter((1 if x == val else 0 for x in values), dtype=np.int64, count=1 << n)
    for i in range(n):
        bit = 1 << i
        for base in range(0, 1 << n, 2 * bit):
            a[base+bit:base+2*bit] -= a[base:base+bit]
    class_coeff[val] = a

free = [v for v in classes if v not in (0,1)]
best = None
hit = None
for bits in range(1 << len(free)):
    selected = [1] + [v for j,v in enumerate(free) if bits >> j & 1]
    c = np.zeros(1 << n, dtype=np.int64)
    for v in selected:
        c += class_coeff[v]
    nz = np.flatnonzero(c)
    degree = max((int(m).bit_count() for m in nz), default=0)
    rec = {'selected_euler_values': selected, 'degree': degree,
           'nonzero_coefficients': int(nz.size),
           'max_abs_coefficient': int(np.max(np.abs(c[nz]))) if nz.size else 0}
    if best is None or (degree,rec['nonzero_coefficients']) < (best['degree'],best['nonzero_coefficients']):
        best = rec
    if degree <= 5:
        truth = np.fromiter((1 if x in selected else 0 for x in values), dtype=np.uint8, count=1 << n)
        s0 = sum(int(truth[1 << i]) != int(truth[0]) for i in range(n))
        margin = math.log(s0)*math.log(3)-math.log(6)*math.log(degree)
        if s0 == n and margin > 0:
            hit = (rec,c,truth,margin)
            break

if hit is None:
    report = {'status':'NO_BOOLEAN_EULER_VALUE_LABELING','n':n,'classes':classes,
              'mappings_checked':1 << len(free),'best':best}
    (OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FINAL_STATUS',json.dumps(report,separators=(',',':')))
else:
    rec,c,truth,margin = hit
    natural=[]; literal=[]
    for mask in np.flatnonzero(c):
        cc=int(c[mask]); mon='*'.join(f'x{i+1}' for i in range(n) if int(mask)>>i&1) or '1'
        natural.append((cc,mon)); literal += [(1 if cc>0 else -1,mon)]*abs(cc)
    ns=''
    for j,(cc,mon) in enumerate(natural):
        sg=1 if cc>0 else -1; body=mon if abs(cc)==1 else f'{abs(cc)}*{mon}'
        ns=(body if sg>0 else '-'+body) if j==0 else ns+(' + ' if sg>0 else ' - ')+body
    ls=''
    for j,(sg,mon) in enumerate(literal):
        ls=(mon if sg>0 else '-'+mon) if j==0 else ls+(' + ' if sg>0 else ' - ')+mon
    (OUT/'submission_natural.txt').write_text(ns+'\n')
    (OUT/'submission.txt').write_text(ls+'\n')
    report={'status':'VERIFIED_BREAKTHROUGH','construction':'RP4 Euler-value labeling',
            'n':n,'degree':rec['degree'],'s0':n,'selected_euler_values':rec['selected_euler_values'],
            'boolean_points_checked':1<<n,'log_margin':margin,
            'achieved_a':math.log(n)/math.log(rec['degree']),
            'threshold_c':math.log(6)/math.log(3),
            'submission_sha256':hashlib.sha256((ls+'\n').encode()).hexdigest()}
    (OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FINAL_STATUS',json.dumps(report,separators=(',',':')))
