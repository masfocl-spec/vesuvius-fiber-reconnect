"""Real-data benchmark (PHercParis4): official fiber prediction -> fragments
-> unchanged B1 reconnection -> scored against eval_fibers GT.

Data (see data_plan.md): region cubes data/pred/region_{presence,nx,ny}.npy
(256^3 level-3 voxels, 19.2 um) + eval_fibers JSON (fiber-level GT, same space).

Pipeline:
  1. threshold presence -> binary mask
  2. skeletonize -> graph -> chains (fragments), dangling endpoints
  3. assign fragments to GT fibers (eval_fibers) [GT-only info]
  4. run methods: A0 greedy / A1 dist+Hungarian / B1a hard tangent /
     B1b soft tangent / B1c both / B2 +curvature / B3 +crossing
     (code imported unchanged from fiber_reconnect.experiment; only the
      resolution-dependent D_MAX is rescaled: 34 vox * 7.91um = 14 vox * 19.2um)
  5. classify every proposal: true (same GT fiber) / false cross-fiber /
     unjudgeable (fragment not covered by GT); tau sweep.

Usage:
  python run_real_experiment.py [--threshold 128] [--dmax 14.0] [--inventory-only]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage.morphology import skeletonize

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import fiber_reconnect.experiment as fx
from fiber_reconnect.experiment import (
    EndPoint, Piece, World, collect_endpoints, method_a, method_a1,
    method_scored, method_scored_sweep,
)
from fiber_reconnect.eval_gt import load_eval_fibers
from fiber_reconnect.nml_io import resample_polyline


def fast_candidate_pairs(ends, world):
    """Same semantics as fx.candidate_pairs (i<j, D_MIN<=d<=D_MAX, different
    piece), but via KD-tree so a 7k-endpoint real region stays feasible."""
    n = len(ends)
    if n < 2:
        return []
    P = np.asarray([e.pos for e in ends])
    tree = cKDTree(P)
    prs = tree.query_pairs(fx.D_MAX, output_type="ndarray")
    out = []
    if len(prs):
        d = np.linalg.norm(P[prs[:, 0]] - P[prs[:, 1]], axis=1)
        pid = np.array([e.pid for e in ends])
        ok = (d >= fx.D_MIN) & (pid[prs[:, 0]] != pid[prs[:, 1]])
        for (i, j), dd in zip(prs[ok], d[ok]):
            out.append((int(i), int(j), float(dd)))
    return out


fx.candidate_pairs = fast_candidate_pairs

OUT = "outputs_real"
DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))


# ---------------------------------------------------------------------------
# fragmentation
# ---------------------------------------------------------------------------
def extract_chains(mask: np.ndarray, min_len: int = 6) -> list[list[int]]:
    """Skeletonize mask, split the skeleton graph at junctions into chains."""
    sk = skeletonize(mask.astype(bool))
    vox = np.argwhere(sk)
    if len(vox) == 0:
        return []
    tree = cKDTree(vox)
    pairs = tree.query_pairs(1.8, output_type="ndarray")
    n = len(vox)
    adj = [[] for _ in range(n)]
    for a, b in pairs:
        adj[a].append(b)
        adj[b].append(a)
    deg = np.array([len(a) for a in adj])
    terminals = set(np.where(deg != 2)[0].tolist())

    chains: list[list[int]] = []
    consumed = np.zeros(n, bool)          # interior nodes already in a chain
    done_pairs: set[frozenset] = set()
    for s in sorted(terminals):
        for nb in adj[s]:
            if nb in terminals and frozenset((s, nb)) in done_pairs:
                continue
            if not nb in terminals and consumed[nb]:
                continue
            path = [s]
            prev, cur = s, nb
            while True:
                path.append(cur)
                if cur in terminals:
                    if cur != s:
                        done_pairs.add(frozenset((s, cur)))
                    break
                consumed[cur] = True
                nxts = [u for u in adj[cur] if u != prev]
                if len(nxts) != 1:
                    break
                prev, cur = cur, nxts[0]
            if len(path) >= 2:
                chains.append(path)
    # keep long chains; return voxel coords
    out = []
    for p in chains:
        if len(p) >= min_len:
            out.append(vox[np.array(p)])
    return out


# ---------------------------------------------------------------------------
# GT assignment
# ---------------------------------------------------------------------------
def assign_gt_fibers(pieces: list[Piece], gt: list[dict], r: float = 3.0,
                     cov: float = 0.6) -> None:
    trees = [cKDTree(f["pts"]) for f in gt]
    for p in pieces:
        best_cov, best_i = 0.0, -1
        for i, tr in enumerate(trees):
            d, _ = tr.query(p.pts[::2], k=1, workers=-1)
            c = float((d <= r).mean())
            if c > best_cov:
                best_cov, best_i = c, i
        if best_cov >= cov:
            p.fiber_id = best_i


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------
def classify_real(props, ends):
    true_l, false_l, unj = [], [], []
    for pr in props:
        fi, fj = ends[pr.ei].fiber_id, ends[pr.ej].fiber_id
        if fi < 0 or fj < 0:
            unj.append(pr)
        elif fi == fj:
            true_l.append(pr)
        else:
            false_l.append(pr)
    return true_l, false_l, unj


def repair_stats(true_props, ends, pieces):
    """Per GT fiber: baseline fragmentation k_f, components after true joins."""
    by_fiber = defaultdict(set)
    for p in pieces:
        if p.fiber_id >= 0:
            by_fiber[p.fiber_id].add(p.pid)
    parent = {}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    def union(u, v):
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv

    for p in by_fiber.values():
        for pid in p:
            parent[pid] = pid
    for pr in true_props:
        fi = ends[pr.ei].fiber_id
        union(ends[pr.ei].pid, ends[pr.ej].pid)
    gaps = 0
    repaired = 0
    for f, pids in by_fiber.items():
        k = len(pids)
        if k < 2:
            continue
        comp = len({find(pid) for pid in pids})
        gaps += k - 1
        repaired += k - comp
    return gaps, repaired


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=128)
    ap.add_argument("--dmax", type=float, default=None,
                    help="override D_MAX in L3 voxels (default: physical "
                         "parity 34*7.91/19.2 = 14.0)")
    ap.add_argument("--min-len", type=int, default=6)
    ap.add_argument("--tau", type=float, default=1.2)
    ap.add_argument("--gt-r", type=float, default=4.0,
                    help="GT assignment radius, L3 voxels")
    ap.add_argument("--gt-cov", type=float, default=0.5,
                    help="min fraction of chain points within gt-r of a GT "
                         "fiber to assign it (0.5 balanced: see report)")
    ap.add_argument("--world", choices=("gt", "all"), default="gt",
                    help="gt: only GT-assigned fragments visible (synthetic-"
                         "protocol analogue); all: whole noisy region")
    ap.add_argument("--ox", type=int, default=16384, help="region corner x, base vox")
    ap.add_argument("--oy", type=int, default=9216, help="region corner y, base vox")
    ap.add_argument("--oz", type=int, default=44544, help="region corner z, base vox")
    ap.add_argument("--region-prefix", default=None,
                    help="dir with region_{presence,nx,ny}.npy "
                         "(default: DATA/pred)")
    ap.add_argument("--inventory-only", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    rdir = args.region_prefix or os.path.join(DATA, "pred")
    pres = np.load(os.path.join(rdir, "region_presence.npy"))
    origin_l3 = (args.ox // 8, args.oy // 8, args.oz // 8)

    # Physical-parity rescale of SCENE constants (not the B1 method itself):
    # the synthetic benchmark ran at 7.91 um/vox, the real prediction grid is
    # 19.2 um/vox, so all spatial scene constants shrink by 7.91/19.2 = 0.412
    # to describe the same physical world to the methods.
    SCALE = 7.91 / 19.2
    fx.D_MIN = 3.0 * SCALE
    fx.D_MAX = float(args.dmax) if args.dmax else 34.0 * SCALE
    fx.BORDER_MARGIN = 3.0 * SCALE
    fx.TIP_FWD = 3.0 * SCALE
    fx.TIP_DIST_THR = 1.5 * SCALE
    fx.TANGENT_K = max(3, round(6 * SCALE))
    print(f"scene constants (L3 vox): D_MIN={fx.D_MIN:.2f} D_MAX={fx.D_MAX:.2f} "
          f"BORDER={fx.BORDER_MARGIN:.2f} TIP_FWD={fx.TIP_FWD:.2f} "
          f"TIP_THR={fx.TIP_DIST_THR:.2f} TANGENT_K={fx.TANGENT_K}")
    gt = load_eval_fibers(os.path.join(DATA, "spiral", "eval_fibers"), origin_l3)
    print(f"region presence 256^3 loaded; GT fibers: {len(gt)} "
          f"({sum(len(f['pts']) for f in gt)} points)")

    # --- threshold analysis: GT coverage vs mask volume -------------------
    gt_pts = np.vstack([f["pts"] for f in gt])
    gin = ((gt_pts[:, 0] >= 0) & (gt_pts[:, 0] < 256) &
           (gt_pts[:, 1] >= 0) & (gt_pts[:, 1] < 256) &
           (gt_pts[:, 2] >= 0) & (gt_pts[:, 2] < 256))
    gp = gt_pts[gin].astype(int)
    gt_vals = pres[gp[:, 0], gp[:, 1], gp[:, 2]]
    print("threshold  mask%%   GT-point coverage")
    for t in (64, 96, 128, 160, 192):
        print(f"  >= {t:3d}   {(pres >= t).mean() * 100:5.1f}%%   "
              f"{(gt_vals >= t).mean() * 100:5.1f}%%")
    thr = args.threshold
    mask = pres >= thr
    print(f"chosen threshold {thr}: mask {(mask).mean() * 100:.1f}% of cube, "
          f"GT coverage {(gt_vals >= thr).mean() * 100:.1f}%")

    # --- fragmentation ----------------------------------------------------
    chains = extract_chains(mask, min_len=args.min_len)
    print(f"skeleton chains: {len(chains)}, total voxels "
          f"{sum(len(c) for c in chains)}")

    pieces: list[Piece] = []
    for i, c in enumerate(chains):
        pts = resample_polyline(c.astype(float), 1.0)
        pieces.append(Piece(pid=i, fiber_id=-1, pts=pts))
    # --- GT assignment BEFORE endpoint creation: EndPoint copies fiber_id
    # at construction time (same order as the synthetic pipeline).
    assign_gt_fibers(pieces, gt, r=args.gt_r, cov=args.gt_cov)
    n_assigned = sum(1 for p in pieces if p.fiber_id >= 0)
    covered_fibers = sorted({p.fiber_id for p in pieces if p.fiber_id >= 0})
    print(f"fragments assigned to GT fibers: {n_assigned}/{len(pieces)}; "
          f"GT fibers present: {len(covered_fibers)}")

    if args.world == "gt":
        pieces = [p for p in pieces if p.fiber_id >= 0]
        print(f"world=gt: method-visible fragments restricted to GT-assigned "
              f"ones ({len(pieces)})")

    dist_fiber = ndimage.distance_transform_edt(~mask)
    ends: list[EndPoint] = collect_endpoints(pieces, dist_fiber, 256)
    print(f"dangling endpoints visible to methods: {len(ends)}")
    frag_hist = defaultdict(int)
    for f in covered_fibers:
        k = sum(1 for p in pieces if p.fiber_id == f)
        frag_hist[k] += 1
    print("fragments-per-GT-fiber histogram {k: n_fibers}:",
          dict(sorted(frag_hist.items())))
    baseline_gaps = sum((k - 1) * n for k, n in frag_hist.items() if k >= 2)
    print(f"baseline fragmentation gaps (k-1 over fibers with k>=2): "
          f"{baseline_gaps}")

    if args.inventory_only:
        return

    # --- methods ----------------------------------------------------------
    world = World(pieces, mask)

    # funnel diagnostics: judgeable events available
    gt_ends = [e for e in ends if e.fiber_id >= 0]
    same_pairs = 0
    P = np.array([e.pos for e in gt_ends]) if gt_ends else np.zeros((0, 3))
    for i in range(len(gt_ends)):
        for j in range(i + 1, len(gt_ends)):
            if gt_ends[i].pid == gt_ends[j].pid:
                continue
            d = float(np.linalg.norm(P[j] - P[i]))
            if fx.D_MIN <= d <= fx.D_MAX:
                same_pairs += 1
    print(f"funnel: GT-dangling-endpoints={len(gt_ends)}, "
          f"same-fiber candidate pairs in window={same_pairs}")
    variants = [
        ("A0_nearest_greedy", lambda: method_a(ends, world)),
        ("A1_dist_hungarian", lambda: method_a1(ends, world)),
        ("B1a_hard_tangent", lambda: method_scored(
            ends, world, use_align_hard=True, use_align_soft=False,
            use_curv=False, use_cross=False, name="B1a")),
        ("B1b_soft_tangent", lambda: method_scored(
            ends, world, use_align_hard=False, use_align_soft=True,
            use_curv=False, use_cross=False, name="B1b")),
        ("B1c_tangent", lambda: method_scored(
            ends, world, use_align_hard=True, use_align_soft=True,
            use_curv=False, use_cross=False, name="B1c")),
        ("B2_tangent_curv", lambda: method_scored(
            ends, world, use_align_hard=True, use_align_soft=True,
            use_curv=True, use_cross=False, name="B2")),
        ("B3_full", lambda: method_scored(
            ends, world, name="B3")),
    ]

    rows = []
    for name, fn in variants:
        props = fn()
        tr, fl, unj = classify_real(props, ends)
        gaps, rep = repair_stats(tr, ends, pieces)
        rows.append({"method": name, "proposals": len(props),
                     "true": len(tr), "false_cross_fiber": len(fl),
                     "unjudgeable": len(unj),
                     "gaps_closed": rep, "gaps_baseline": baseline_gaps,
                     "events_available": same_pairs})
        print(f"  {name:20s} props={len(props):3d} true={len(tr):3d} "
              f"false={len(fl):3d} unjudgeable={len(unj):3d} "
              f"gaps_closed={rep}/{baseline_gaps}")

    with open(f"{OUT}/results_real.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # --- tau sweep --------------------------------------------------------
    taus = [0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
    sweep_specs = [("A1", False, False, False, False),
                   ("B1a", True, False, False, False),
                   ("B1b", False, True, False, False),
                   ("B1c", True, True, False, False),
                   ("B2", True, True, True, False),
                   ("B3", True, True, True, True)]
    sweep_rows = []
    for name, ah, asft, uc, ux in sweep_specs:
        per_tau = method_scored_sweep(ends, world, taus, use_align_hard=ah,
                                      use_align_soft=asft, use_curv=uc,
                                      use_cross=ux, name=name)
        for tau in taus:
            tr, fl, unj = classify_real(per_tau[tau], ends)
            _, rep = repair_stats(tr, ends, pieces)
            sweep_rows.append({"method": name, "tau": tau, "proposals": len(tr) + len(fl) + len(unj),
                               "true": len(tr), "false_cross_fiber": len(fl),
                               "unjudgeable": len(unj), "gaps_closed": rep})
    with open(f"{OUT}/tau_sweep_real.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sweep_rows[0].keys()))
        w.writeheader()
        w.writerows(sweep_rows)
    print(f"\nwritten {OUT}/results_real.csv and {OUT}/tau_sweep_real.csv")


if __name__ == "__main__":
    main()
