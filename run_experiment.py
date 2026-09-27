"""Run the fiber-break reconnection experiment on one Vesuvius fiber-skeletons cube.

Runs the ablation ladder on the SAME corruption (same seed -> same breaks):
  A0  nearest endpoint, greedy                 (baseline)
  A1  distance only + Hungarian assignment
  B1  distance + tangent alignment
  B2  distance + tangent + curvature
  B3  distance + tangent + curvature + crossing (full method)

Usage:
  python run_experiment.py [--cube s1_00497_01497_03997_256] [--seed 20260926]

Inputs  (data/raw):  labels_<cube>.tif, fibers_..._<cube>.nml
Outputs (outputs/):  results.csv, results_seeds.csv, breaks_per_case.csv,
                     figures/fig1..fig6 *.png
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import numpy as np
import tifffile
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fiber_reconnect.experiment import (  # noqa: E402
    World, attach_gt_breaks, classify_proposals, collect_endpoints, corrupt,
    load_pieces, method_a, method_a1, method_b, method_scored,
    method_scored_sweep, near_parallel_flags, position_errors,
)
from fiber_reconnect.nml_io import cube_name_to_origin  # noqa: E402
from fiber_reconnect import viz  # noqa: E402

RAW = "data/raw"
OUT = "outputs"

VARIANTS = [
    ("A0_nearest_greedy", method_a),
    ("A1_dist_hungarian", method_a1),
    ("B1a_dist_hard_tangent",
     lambda e, w: method_scored(e, w, use_align_hard=True,
                                use_align_soft=False, use_curv=False,
                                use_cross=False)),
    ("B1b_dist_soft_tangent",
     lambda e, w: method_scored(e, w, use_align_hard=False,
                                use_align_soft=True, use_curv=False,
                                use_cross=False)),
    ("B1c_dist_tangent",
     lambda e, w: method_scored(e, w, use_align_hard=True,
                                use_align_soft=True, use_curv=False,
                                use_cross=False)),
    ("B2_dist_tangent_curv",
     lambda e, w: method_scored(e, w, use_align_hard=True,
                                use_align_soft=True, use_curv=True,
                                use_cross=False)),
    ("B3_full_geometry", method_b),
]


def find_nml(cube: str) -> str:
    z0, y0, x0, size = cube_name_to_origin(cube)
    for f in os.listdir(RAW):
        if f.endswith(".nml") and f"{z0:05d}z" in f and f"{y0:05d}y" in f \
                and f"{x0:05d}x" in f and f"_{size}_" in f:
            return os.path.join(RAW, f)
    raise FileNotFoundError(f"no NML for cube {cube} in {RAW}")


def coverage_stats(pieces, mask):
    """NML <-> mask agreement (sanity, printed)."""
    pts = np.vstack([p.pts for p in pieces])
    inside = np.all((pts >= 0) & (pts < np.asarray(mask.shape)), axis=1)
    mtree = cKDTree(np.argwhere(mask > 0))
    d, _ = mtree.query(pts[inside], k=1, workers=-1)
    mv = np.argwhere(mask > 0)
    ptree = cKDTree(pts[inside])
    d2, _ = ptree.query(mv, k=1, workers=-1)
    return {
        "n_pieces": len(pieces),
        "total_arc": int(len(pts)),
        "pieces_on_mask_r2": float((d <= 2.0).mean()),
        "mask_on_pieces_r3": float((d2 <= 3.0).mean()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cube", default="s1_00497_01497_03997_256")
    ap.add_argument("--seed", type=int, default=20260926)
    args = ap.parse_args()
    cube = args.cube

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(f"{OUT}/figures", exist_ok=True)

    tif = f"{RAW}/labels_{cube}.tif"
    nml = find_nml(cube)
    print(f"cube   : {cube}\nlabel  : {tif}\nnml    : {nml}")

    mask = tifffile.imread(tif)
    print(f"mask   : {mask.shape} {mask.dtype}, fiber voxels "
          f"{int((mask > 0).sum())}")

    pieces = load_pieces(nml, cube)
    cov = coverage_stats(pieces, mask)
    print(f"pieces : {cov['n_pieces']} (total arc {cov['total_arc']} vox), "
          f"pieces on mask(r2) {cov['pieces_on_mask_r2'] * 100:.1f}%, "
          f"mask on pieces(r3) {cov['mask_on_pieces_r3'] * 100:.1f}%")

    # ------------------------------------------------------------------ break
    cmask, breaks, pieces_after = corrupt(pieces, mask, seed=args.seed)
    print(f"breaks : {len(breaks)} artificial gaps, "
          f"{len(pieces_after)} pieces after corruption")
    removed = int((mask.astype(bool) & ~cmask.astype(bool)).sum())
    print(f"removed voxels: {removed}")

    # -------------------------------------------------------------- endpoints
    dist_fiber = ndimage.distance_transform_edt(cmask == 0)
    ends = collect_endpoints(pieces_after, dist_fiber, mask.shape[0])
    attach_gt_breaks(ends, breaks)
    n_marked = sum(1 for e in ends if e.is_break_end)
    print(f"endpoints: {len(ends)} dangling tips visible to methods "
          f"({n_marked} are the two sides of inserted breaks)")

    world = World(pieces_after, cmask)

    # ---------------------------------------------------------------- methods
    variants = []
    for name, fn in VARIANTS:
        props = fn(ends, world)
        res = classify_proposals(props, ends, breaks)
        merr, xerr = position_errors(props, ends, breaks)
        variants.append((name, props, res, merr, xerr))
        print(f"  {name:24s} proposals={len(props):3d} "
              f"repaired={len(res['repaired']):3d} "
              f"false_cross={len(res['false_cross']):3d} "
              f"extra_same={len(res['extra_same'])}")

    np_flag = near_parallel_flags(breaks, pieces)

    # ---------------------------------------------------------------- summary
    def summarize(name, res, merr, xerr):
        n = len(breaks)
        rep = res["repaired"]
        hard = [b for b in breaks if np_flag[b.bid]]
        easy = [b for b in breaks if not np_flag[b.bid]]
        rep_h = [b for b in hard if b.bid in rep]
        rep_e = [b for b in easy if b.bid in rep]
        return {
            "method": name,
            "seed": args.seed,
            "n_breaks": n,
            "repaired": len(rep),
            "repaired_pct": round(100.0 * len(rep) / n, 1) if n else None,
            "unrepaired": n - len(rep),
            "false_cross_fiber": len(res["false_cross"]),
            "extra_same_fiber": len(res["extra_same"]),
            "pos_err_mean_vox": round(float(np.mean(list(merr.values()))), 2)
            if merr else None,
            "pos_err_p95_vox": round(float(np.percentile(list(merr.values()), 95)), 2)
            if merr else None,
            "pos_err_max_vox": round(float(np.max(list(xerr.values()))), 2)
            if xerr else None,
            "hard_breaks_near_parallel": len(hard),
            "hard_repaired": f"{len(rep_h)}/{len(hard)}",
            "easy_repaired": f"{len(rep_e)}/{len(easy)}",
            "proposals_total": len(res["repaired"]) + len(res["false_cross"])
            + len(res["extra_same"]),
        }

    rows = [summarize(name, res, merr, xerr)
            for name, props, res, merr, xerr in variants]

    print("\n=== ablation summary ===")
    for r in rows:
        print(r)

    # -------------------------------------------------------------- csv files
    with open(f"{OUT}/results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with open(f"{OUT}/breaks_per_case.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        names = [name for name, _, _, _, _ in variants]
        w.writerow(["break_id", "fiber_id", "piece_id", "gap_len_vox",
                    "near_parallel"]
                   + [f"{name}_repaired" for name in names]
                   + [f"{name}_pos_err_mean" for name in names])
        rep_sets = {name: set(res["repaired"])
                    for name, _, res, _, _ in variants}
        err_maps = {name: merr for name, _, _, merr, _ in variants}
        for b in breaks:
            row = [b.bid, b.fiber_id, b.piece_id, len(b.gap_pts),
                   int(np_flag[b.bid])]
            row += [int(b.bid in rep_sets[name]) for name in names]
            row += [round(err_maps[name][b.bid], 2)
                    if b.bid in err_maps[name] else "" for name in names]
            w.writerow(row)

    # ------------------------------------------------------------- figures
    props_a0 = variants[0][1]
    props_b3 = variants[-1][1]
    viz.fig_gt_corrupted(mask, cmask, breaks, ends,
                         f"{OUT}/figures/fig1_gt_vs_corrupted.png",
                         mask.shape[0])
    viz.fig_method(mask, cmask, breaks, props_a0, ends, "A0 (nearest)",
                   f"{OUT}/figures/fig2_method_A0_nearest.png")
    viz.fig_method(mask, cmask, breaks, props_b3, ends, "B3 (geometry-aware)",
                   f"{OUT}/figures/fig3_method_B3_geometry_aware.png")
    viz.fig_compare(mask, cmask, breaks, props_a0, props_b3, ends,
                    f"{OUT}/figures/fig4_A0_vs_B3.png")
    drew = viz.fig_hard_case(mask, cmask, breaks, props_a0, props_b3, ends,
                             f"{OUT}/figures/fig5_hard_cases.png", np_flag)
    viz.fig_ablation(rows, f"{OUT}/figures/fig6_ablation.png")
    print(f"\nfigures written to {OUT}/figures/ (hard-case figure: {drew})")

    # ------------------------------------------------------------ tau sweep
    # Same cost matrices, varying acceptance threshold tau: shows the
    # repaired/false-links trade-off of each feature set without a single
    # fixed operating point.
    taus = [0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
    sweep_specs = [("A1", False, False, False, False),
                   ("B1a", True, False, False, False),
                   ("B1b", False, True, False, False),
                   ("B1c", True, True, False, False),
                   ("B2", True, True, True, False),
                   ("B3", True, True, True, True)]
    sweep_rows, sweep_series = [], {}
    for name, ah, asft, uc, ux in sweep_specs:
        per_tau = method_scored_sweep(ends, world, taus, use_align_hard=ah,
                                      use_align_soft=asft, use_curv=uc,
                                      use_cross=ux, name=name)
        rep_s, fl_s = [], []
        for tau in taus:
            res = classify_proposals(per_tau[tau], ends, breaks)
            rep_s.append(100.0 * len(res["repaired"]) / len(breaks))
            fl_s.append(len(res["false_cross"]))
            sweep_rows.append({"method": name, "tau": tau,
                               "repaired": len(res["repaired"]),
                               "repaired_pct": round(rep_s[-1], 1),
                               "false_cross_fiber": len(res["false_cross"])})
        sweep_series[name] = (rep_s, fl_s)
    with open(f"{OUT}/tau_sweep.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["method", "tau", "repaired",
                                          "repaired_pct",
                                          "false_cross_fiber"])
        w.writeheader()
        w.writerows(sweep_rows)
    viz.fig_tau_sweep(sweep_series, taus, len(breaks),
                      f"{OUT}/figures/fig7_tau_sweep.png")
    print("tau sweep written to outputs/tau_sweep.csv + fig7")

    # ------------------------------------------------------------- verdict
    a0, b3 = rows[0], rows[-1]
    print("\n=== verdict (ablation ladder, same breaks) ===")
    for r in rows:
        print(f"{r['method']:24s} repaired {r['repaired']:3d}/{r['n_breaks']} "
              f"({r['repaired_pct']}%)  false_cross={r['false_cross_fiber']}")
    print(f"\nA0 -> B3 : repaired +{b3['repaired'] - a0['repaired']}, "
          f"false links {a0['false_cross_fiber']} -> {b3['false_cross_fiber']}")


if __name__ == "__main__":
    main()
