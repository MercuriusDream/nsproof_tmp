# Subagent validation for v112 and v113-base

Validated files:

- `profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json`
- `profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json`

No finalized `v113` JSON/MD file was present under `profile-seeds`; only `gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json` matched `*v113*`.

## Identity check

Command:

```sh
PYTHONPATH=tools python3 - <<'PY'
from compactified_profile import load_seed_json_profile, grid
_,_,p112 = load_seed_json_profile('profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json')
_,_,p113 = load_seed_json_profile('profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json')
max_f=max_g=0.0
max_at=(None,None,0.0,0.0)
for q in grid(0.155,0.895,23):
    for b in grid(-0.875,0.925,21):
        df=abs(p112.F_total(q,b)-p113.F_total(q,b))
        dg=abs(p112.G_total(q,b)-p113.G_total(q,b))
        if max(df,dg)>max(max_f,max_g):
            max_at=(q,b,df,dg)
        max_f=max(max_f,df)
        max_g=max(max_g,dg)
print(f'max_abs_F_total_diff={max_f:.12e}')
print(f'max_abs_G_total_diff={max_g:.12e}')
print(f'worst_sample={max_at}')
PY
```

Result:

```text
max_abs_F_total_diff=0.000000000000e+00
max_abs_G_total_diff=0.000000000000e+00
worst_sample=(None, None, 0.0, 0.0)
```

The two files have different SHA-256 hashes, but the sampled total profile values agree exactly on this 23x21 shifted grid.

## Shifted h-sweep gates

Commands:

```sh
python3 tools/profile_gates.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --h-values 1.6e-3,8e-4,4e-4 --wide-q-min 0.365 --wide-q-max 0.895 --wide-b-min -0.775 --wide-b-max 0.825 --wide-n-q 17 --wide-n-b 19 --interior-q-min 0.462 --interior-q-max 0.842 --interior-b-min -0.617 --interior-b-max 0.683 --interior-n-q 19 --interior-n-b 17 --local-r-min 0.83 --local-r-max 1.97 --local-z-min -0.93 --local-z-max 1.07 --local-n 31
python3 tools/profile_gates.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --h-values 1.6e-3,8e-4,4e-4 --wide-q-min 0.365 --wide-q-max 0.895 --wide-b-min -0.775 --wide-b-max 0.825 --wide-n-q 17 --wide-n-b 19 --interior-q-min 0.462 --interior-q-max 0.842 --interior-b-min -0.617 --interior-b-max 0.683 --interior-n-q 19 --interior-n-b 17 --local-r-min 0.83 --local-r-max 1.97 --local-z-min -0.93 --local-z-max 1.07 --local-n 31
```

Both files produced identical values:

```text
h=1.6e-3  wide max=4.393311694755e-01 rms=2.134978116261e-01
h=1.6e-3  interior max=4.391279978399e-01 rms=2.332695163081e-01
h=1.6e-3  local max=4.397114750600e-01 rms=2.639772663318e-01
h=8e-4    wide max=4.393332870999e-01 rms=2.134975200281e-01
h=8e-4    interior max=4.391261380395e-01 rms=2.332691763934e-01
h=8e-4    local max=4.397134443514e-01 rms=2.639766462845e-01
h=4e-4    wide max=4.393334223190e-01 rms=2.134978134683e-01
h=4e-4    interior max=4.391238011953e-01 rms=2.332690292651e-01
h=4e-4    local max=4.397131379235e-01 rms=2.639765463925e-01
```

## Shifted topology scans

Broad shifted topology commands:

```sh
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --q-min 0.351 --q-max 0.891 --b-min -0.831 --b-max 0.831 --n-q 43 --n-b 39 --h 8e-4 --top 8 --slice-top 5
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --q-min 0.351 --q-max 0.891 --b-min -0.831 --b-max 0.831 --n-q 43 --n-b 39 --h 8e-4 --top 8 --slice-top 5
```

Both files:

```text
global rms=2.151751379934e-01
max=4.388979320474e-01 at q=0.492429 b=-0.612316 r=1.397385 z=-1.082250
paired symmetric point at b=+0.612316 has the same max.
```

Refined `q ~= 0.48`, `b ~= 0.64` lobe commands:

```sh
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --q-min 0.472 --q-max 0.505 --b-min 0.585 --b-max 0.675 --n-q 35 --n-b 37 --h 1.6e-3 --top 3 --slice-top 2
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --q-min 0.472 --q-max 0.505 --b-min 0.585 --b-max 0.675 --n-q 35 --n-b 37 --h 8e-4 --top 6 --slice-top 3
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --q-min 0.472 --q-max 0.505 --b-min 0.585 --b-max 0.675 --n-q 35 --n-b 37 --h 4e-4 --top 3 --slice-top 2
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --q-min 0.472 --q-max 0.505 --b-min 0.585 --b-max 0.675 --n-q 35 --n-b 37 --h 1.6e-3 --top 3 --slice-top 2
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --q-min 0.472 --q-max 0.505 --b-min 0.585 --b-max 0.675 --n-q 35 --n-b 37 --h 8e-4 --top 6 --slice-top 3
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --q-min 0.472 --q-max 0.505 --b-min 0.585 --b-max 0.675 --n-q 35 --n-b 37 --h 4e-4 --top 3 --slice-top 2
```

Both files:

```text
h=1.6e-3  rms=3.090465813621e-01 max=4.400618204262e-01 at q=0.481706 b=0.642500
h=8e-4    rms=3.090471569425e-01 max=4.400635460091e-01 at q=0.481706 b=0.642500
h=4e-4    rms=3.090471840850e-01 max=4.400609598714e-01 at q=0.482676 b=0.642500
```

Refined `q ~= 0.607`, `b ~= -0.245` lobe commands:

```sh
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --q-min 0.575 --q-max 0.612 --b-min -0.290 --b-max -0.205 --n-q 37 --n-b 35 --h 8e-4 --top 6 --slice-top 3
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --q-min 0.575 --q-max 0.612 --b-min -0.290 --b-max -0.205 --n-q 37 --n-b 35 --h 8e-4 --top 6 --slice-top 3
```

Both files:

```text
rms=3.168117360689e-01
max=4.398213313719e-01 at q=0.606861 b=-0.245000 r=1.269787 z=-0.320877
```

Shifted far-tail topology command:

```sh
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --q-min 0.155 --q-max 0.295 --b-min -0.875 --b-max 0.925 --n-q 19 --n-b 41 --h 8e-4 --top 1 --slice-top 0
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --q-min 0.155 --q-max 0.295 --b-min -0.875 --b-max 0.925 --n-q 19 --n-b 41 --h 8e-4 --top 1 --slice-top 0
```

Both files:

```text
global rms=1.278491103557e-01
max=3.751430454117e-01 at q=0.295000 b=-0.380000 r=2.996007 z=-1.230810
```

## Discrepancy

The shifted/refined `q in [0.472,0.505]`, `b in [0.585,0.675]` topology scan gives a stable maximum around `4.4006e-01`, larger than the v112 note's listed `fine local = 4.397800969258e-01` and `41x41 topology max = 4.393817079326e-01`. This does not prove a new qualitative failure, since all residuals remain `O(1)`, but it does invalidate treating the listed v112 maxima as exhaustive. Because `v113-base` is functionally identical to v112 on sampled shifted grids, the same lobe should be included as an active/scoring point before any v113 search is considered validated.
