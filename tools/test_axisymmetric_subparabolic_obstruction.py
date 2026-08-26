#!/usr/bin/env python3
"""Regression test: the frozen case passes; gamma=1/2 and B=0 are rejected."""
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'tools/validate_axisymmetric_subparabolic_obstruction.py'
P=ROOT/'work/twochart_stage0_current_profile_top8pde128_rowlocal_densemortar_step22_nativebatch.json'
def run(p,o,m): return subprocess.run([sys.executable,str(V),'--profile',str(p),'--out',str(o),'--manifest-out',str(m)],cwd=ROOT).returncode
def main():
 d=json.loads(P.read_text())
 with tempfile.TemporaryDirectory() as td:
  t=Path(td); assert run(P,t/'a.json',t/'am.json')==0
  x=json.loads(json.dumps(d)); x['gamma']=.5; x['p']=2.; x['requested_options']['gamma_override']='1/2'; (t/'h.json').write_text(json.dumps(x)); assert run(t/'h.json',t/'b.json',t/'bm.json')==1
  x=json.loads(json.dumps(d)); x['B']=0.; (t/'z.json').write_text(json.dumps(x)); assert run(t/'z.json',t/'c.json',t/'cm.json')==1
 print('axisymmetric_subparabolic_obstruction regression tests: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
