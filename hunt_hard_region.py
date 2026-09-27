"""Hunt for a HARD region: where does the official detector fail along GT fibers?

Stage A (no downloads): rank 2048^3-base-voxel windows (= 256^3 L3) by fiber
curvature/tangent wander computed from the 65 eval_fibers GT polylines
(villa#191: models fail in "compressed or highly curved" areas).
Stage B (--probe): for top windows, download ONLY the presence chunks that
contain GT fiber points and measure hole statistics along the polylines.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

import numpy as np
import requests
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from fiber_reconnect.eval_gt import load_eval_fibers  # noqa: E402

DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
S3 = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/"
PRESENCE = (S3 + "PHercParis4/representations/predictions/fibers/"
            "20260411134726-fibers-20260915212757-L1/"
            "PHercParis4-20260411134726-las-sd1-7ff0ce6c_presence.ome.zarr/3/")
W = 2048          # window size, base voxels (= 256 L3)
STEP = 1024       # sliding step, base voxels
THR = 128         # presence threshold for hole measurement


def load_fibers():
    """All 65 GT fibers in base-voxel (x,y,z) coords, subsampled."""
    out = []
    # eval_gt loader converts to L3 local; here we want raw base coords, so
    # re-read the JSONs directly.
    import glob, json
    for fp in sorted(glob.glob(os.path.join(DATA, "spiral", "eval_fibers", "*.json"))):
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        lp = np.asarray(d["line_points"], dtype=float)   # (x,y,z) base vox
        if len(lp) < 60:
            continue
        out.append(lp)
    return out


def tangent_wander(lp: np.ndarray, chord: int = 8) -> np.ndarray:
    """Per-point turn angle (rad) between successive chord directions."""
    n = len(lp)
    w = np.zeros(n)
    if n < 2 * chord + 1:
        return w
    d1 = lp[2 * chord:] - lp[:n - 2 * chord]          # long chord direction
    d2 = lp[chord:] - lp[:n - chord]                  # short chord direction
    m = min(len(d1), len(d2))
    d1, d2 = d1[:m], d2[:m]
    n1 = np.linalg.norm(d1, axis=1)
    n2 = np.linalg.norm(d2, axis=1)
    ok = (n1 > 1e-9) & (n2 > 1e-9)
    cosang = np.clip((d1[ok] * d2[ok]).sum(1) / (n1[ok] * n2[ok]), -1, 1)
    ang = np.degrees(np.arccos(cosang))
    idx = np.where(ok)[0] + chord
    w[idx] = ang
    return w


def stage_a(fibers):
    """Rank windows by mean wander of GT points inside (with fiber count)."""
    all_pts = []
    pt_wander = []
    for lp in fibers:
        w = tangent_wander(lp)
        all_pts.append(lp)
        pt_wander.append(w)
    pts = np.vstack(all_pts)
    wnd = np.concatenate([np.full(len(p), i) for i, p in enumerate(all_pts)])
    wander = np.concatenate(pt_wander)

    best = []
    x0s = range(int(pts[:, 0].min()) // STEP * STEP, int(pts[:, 0].max()) + 1, STEP)
    y0s = range(int(pts[:, 1].min()) // STEP * STEP, int(pts[:, 1].max()) + 1, STEP)
    z0s = range(int(pts[:, 2].min()) // STEP * STEP, int(pts[:, 2].max()) + 1, STEP)
    for x0 in x0s:
        for y0 in y0s:
            for z0 in z0s:
                m = ((pts[:, 0] >= x0) & (pts[:, 0] < x0 + W) &
                     (pts[:, 1] >= y0) & (pts[:, 1] < y0 + W) &
                     (pts[:, 2] >= z0) & (pts[:, 2] < z0 + W))
                if m.sum() < 400:
                    continue
                nf = len(set(wnd[m].tolist()))
                mw = float(np.mean(wander[m]))
                hi = float((wander[m] > 20).mean())
                best.append((mw, hi, nf, int(m.sum()), x0, y0, z0))
    best.sort(reverse=True)
    return best


def fetch_presence_chunks(chunks, outdir, workers=16):
    """chunks are (cz, cy, cx) in ARRAY (z,y,x) order."""
    import concurrent.futures as cf
    import time
    os.makedirs(outdir, exist_ok=True)
    got = {}

    def fetch_one(ck):
        cz, cy, cx = ck
        path = os.path.join(outdir, f"{cz}_{cy}_{cx}.chunk")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return ck, path
        url = PRESENCE + f"{cz}/{cy}/{cx}"
        for a in range(5):
            try:
                r = requests.get(url, timeout=(15, 60))
                if r.status_code == 200:
                    open(path, "wb").write(r.content)
                    return ck, path
                if r.status_code == 404:
                    return ck, None
            except Exception:
                pass
            time.sleep(1 + a)
        return ck, None

    with cf.ThreadPoolExecutor(workers) as ex:
        for ck, path in ex.map(fetch_one, chunks):
            if path:
                got[ck] = path
    return got


def stage_b(fibers, wins, max_windows=6):
    """Probe top windows: sparse chunk download, hole stats along fibers."""
    from numcodecs import Blosc
    codec = Blosc(cname="zstd", clevel=3, shuffle=1, blocksize=0)
    results = []
    for (mw, hi, nf, npts, x0, y0, z0) in wins[:max_windows]:
        # fibers with enough points inside
        sel = []
        for lp in fibers:
            m = ((lp[:, 0] >= x0) & (lp[:, 0] < x0 + W) &
                 (lp[:, 1] >= y0) & (lp[:, 1] < y0 + W) &
                 (lp[:, 2] >= z0) & (lp[:, 2] < z0 + W))
            if m.sum() >= 50:
                sel.append((lp, m))
        if len(sel) < 4:
            continue
        # chunks containing GT points (base vox -> L3 chunk: base//8//64 = base//512)
        need = set()
        for lp, m in sel:
            pp = lp[m]
            cxs = (pp[:, 0] // 512).astype(int)
            cys = (pp[:, 1] // 512).astype(int)
            czs = (pp[:, 2] // 512).astype(int)
            for x, y, z in zip(cxs, cys, czs):
                need.add((int(z), int(y), int(x)))   # array order (z,y,x)
        outdir = os.path.join(DATA, "probe", f"{x0}_{y0}_{z0}")
        got = fetch_presence_chunks(sorted(need), outdir)
        # hole stats along fibers
        tot_holes = tot_pts = covered = 0
        hole_dens_per100 = []
        for lp, m in sel:
            pp = lp[m]
            vals = np.zeros(len(pp), bool)
            ok = np.ones(len(pp), bool)
            for k, (x, y, z) in enumerate(pp):
                ck = (int(z // 512), int(y // 512), int(x // 512))
                if ck not in got:
                    ok[k] = False
                    continue
                arr = np.frombuffer(codec.decode(open(got[ck], "rb").read()),
                                    dtype=np.uint8).reshape(64, 64, 64)
                vals[k] = arr[int(z // 8 % 64), int(y // 8 % 64), int(x // 8 % 64)] >= THR
            if ok.sum() < 40:
                continue
            v = vals[ok]
            runs, cur = 0, 0
            for vv in v:
                if not vv:
                    cur += 1
                else:
                    if cur >= 3:
                        runs += 1
                    cur = 0
            tot_holes += runs
            tot_pts += len(v)
            covered += v.mean()
            hole_dens_per100.append(100.0 * runs / max(len(v), 1))
        results.append(dict(x0=x0, y0=y0, z0=z0, wander=mw, nfib=len(sel),
                            holes100=float(np.mean(hole_dens_per100)) if hole_dens_per100 else 0,
                            cov100=100 * covered / max(len(hole_dens_per100), 1),
                            chunks=len(got)))
        print(f"window x[{x0},{x0+W}] y[{y0},{y0+W}] z[{z0},{z0+W}]: "
              f"fibers={len(sel)} mean_wander={mw:.1f}deg "
              f"holes>=3vox per100pts={results[-1]['holes100']:.2f} "
              f"coverage={results[-1]['cov100']:.1f}% chunks={len(got)}")
    return results


def main():
    probe = "--probe" in sys.argv
    fibers = load_fibers()
    print(f"GT fibers used: {len(fibers)}")
    best = stage_a(fibers)
    print("\nTop-12 windows by tangent wander (villa#191 proxy):")
    print("mean_wander  %>20deg  fibers  points   window base (x,y,z)")
    for mw, hi, nf, npts, x0, y0, z0 in best[:12]:
        print(f"{mw:9.1f}deg {hi * 100:6.1f}% {nf:6d} {npts:7d}  "
              f"x[{x0},{x0 + W}] y[{y0},{y0 + W}] z[{z0},{z0 + W}]")
    if probe:
        print("\n--- Stage B: presence probing of top windows ---")
        res = stage_b(fibers, best, max_windows=6)
        res.sort(key=lambda r: -r["holes100"])
        print("\nRanking by hole density (hard-region score):")
        for r in res:
            print(f"  x[{r['x0']},{r['x0']+W}] y[{r['y0']},{r['y0']+W}] "
                  f"z[{r['z0']},{r['z0']+W}]: holes100={r['holes100']:.2f} "
                  f"cov={r['cov100']:.1f}% fibers={r['nfib']}")


if __name__ == "__main__":
    main()
