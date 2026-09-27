"""Self-test of the pipeline on a tiny synthetic scene (no real data needed).

Builds a 96^3 mask with:
  - one gently CURVED fiber with an artificial gap,
  - one STRAIGHT fiber crossing near the gap (parallel decoy),
then runs corruption + both methods and prints what happened.

Run:  python test_synthetic.py
"""

import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "src")
from fiber_reconnect import experiment as ex  # noqa: E402
from fiber_reconnect.experiment import (  # noqa: E402
    Break, EndPoint, Piece, World, attach_gt_breaks, classify_proposals,
    collect_endpoints, corrupt, method_a, method_b, position_errors,
)
from fiber_reconnect.nml_io import resample_polyline  # noqa: E402

SIZE = 96


def fiber_line(t0, t1, n, bend=0.0):
    """Sample a slightly curved line from t0 to t1 with n points."""
    t = np.linspace(0, 1, n)[:, None]
    base = np.asarray(t0) * (1 - t) + np.asarray(t1) * t
    if bend:
        base[:, 1] += bend * np.sin(np.pi * t[:, 0])  # gentle bow in y
    return base


def paint(mask, pts, r=2.0):
    z, y, x = np.ogrid[-3:4, -3:4, -3:4]
    ball = (z**2 + y**2 + x**2) <= r * r
    offs = np.stack(np.where(ball), axis=1) - 3
    for p in pts:
        c = np.round(p).astype(int)
        vox = c[None, :] + offs
        ok = np.all((vox >= 0) & (vox < SIZE), axis=1)
        mask[tuple(vox[ok].T)] = 1


def main():
    mask = np.zeros((SIZE, SIZE, SIZE), np.uint8)
    # curved fiber: left half only (we will cut its middle by hand)
    f1 = fiber_line((10, 20, 10), (10, 70, 80), 90, bend=8.0)  # diagonal in xz
    f2 = fiber_line((50, 20, 12), (50, 70, 12), 60)            # straight decoy
    paint(mask, f1)
    paint(mask, f2)

    pieces = [Piece(pid=0, fiber_id=1, pts=f1.copy()),
              Piece(pid=1, fiber_id=2, pts=f2.copy())]

    # hand-crafted break in the middle of f1 (arc 40..52)
    g0, g1 = 40, 52
    gap_pts = f1[g0:g1].copy()
    breaks = [Break(bid=0, piece_id=0, fiber_id=1, gap_pts=gap_pts,
                    left_end=f1[g0 - 1].copy(), right_end=f1[g1].copy())]
    cmask = mask.copy()
    # delete a tube around the gap (voxels owned by fiber 1 only)
    decoy_tree = cKDTree(f2)
    del_pts, r_used = ex.delete_gap_voxels(cmask, f1, g0, g1, decoy_tree, r0=3.0)
    assert len(del_pts), "gap deletion failed to sever the fiber"
    cmask[tuple(del_pts.T)] = 0

    pieces_after = [Piece(pid=10, fiber_id=1, pts=f1[:g0].copy()),
                    Piece(pid=11, fiber_id=1, pts=f1[g1:].copy()),
                    Piece(pid=12, fiber_id=2, pts=f2.copy())]

    from scipy import ndimage
    dist_fiber = ndimage.distance_transform_edt(cmask == 0)
    ends = collect_endpoints(pieces_after, dist_fiber, SIZE)
    attach_gt_breaks(ends, breaks)
    world = World(pieces_after, cmask)

    print(f"endpoints: {len(ends)}, break ends marked: "
          f"{sum(e.is_break_end for e in ends)}")
    for e in ends:
        print(f"  e{e.eid} pid={e.pid} pos={np.round(e.pos, 1)} "
              f"t={np.round(e.tangent, 2)} k={e.kappa:.3f} "
              f"break={e.is_break_end}/{e.bid}/{e.side}")

    for name, fn in (("A", method_a), ("B", method_b)):
        props = fn(ends, world)
        res = classify_proposals(props, ends, breaks)
        merr, xerr = position_errors(props, ends, breaks)
        print(f"[method {name}] proposals={len(props)} repaired={res['repaired']} "
              f"false_cross={len(res['false_cross'])} extra_same={len(res['extra_same'])} "
              f"unrepaired={res['unrepaired']} mean_err={merr}")
        for pr in props:
            ei, ej = ends[pr.ei], ends[pr.ej]
            print(f"    pair e{pr.ei}(f{ei.fiber_id}) - e{pr.ej}(f{ej.fiber_id}) "
                  f"cost={pr.cost:.3f}")

    # also exercise the full corrupt() path on a longer synthetic
    long_f = fiber_line((30, 10, 40), (30, 85, 40), 110, bend=4.0)
    mask2 = np.zeros((SIZE, SIZE, SIZE), np.uint8)
    paint(mask2, long_f)
    p2 = [Piece(pid=0, fiber_id=7, pts=long_f.copy())]
    cmask2, brks, pafts = ex.corrupt(p2, mask2, seed=1)
    print(f"[corrupt] breaks={len(brks)} pieces_after={len(pafts)} "
          f"removed_voxels={int((mask2.astype(bool) & ~cmask2.astype(bool)).sum())}")

    # ---------------------------------------------------------------
    # scenario 2: adversarial — the WRONG partner is the nearest tip.
    # A decoy fiber crosses f1 right at the gap and is itself cut there, so
    # its stub tip is closer to f1's left stub than the correct partner is.
    # Nearest-endpoint should mispair; geometry-aware should recover it.
    print("\n--- scenario 2: decoy cut at the crossing (nearest is wrong) ---")
    SIZE2 = 120
    t = np.linspace(0, 1, 200)[:, None]
    f1 = np.zeros((200, 3))
    f1[:, 0] = 60                      # z constant
    f1[:, 1] = 10 + 100 * t[:, 0]      # along y
    f1[:, 2] = 55 + 10 * np.sin(np.pi * t[:, 0])   # C-bow in x
    # decoy: quadratic Bezier crossing f1 at the future gap (y ~ 58, x ~ 65)
    P0 = np.array([60, 10, 110.0])
    P1 = np.array([60, 58, 60.0])
    P2 = np.array([60, 110, 42.0])
    f2 = ((1 - t) ** 2) * P0 + 2 * (1 - t) * t * P1 + (t**2) * P2
    f2 = resample_polyline(f2, 1.0)
    # cut the decoy where it crosses f1 (nearest point to f1's gap midpoint)
    cross = int(np.argmin(np.linalg.norm(f2 - np.array([60, 58, 65.0]), axis=1)))
    g2a, g2b = cross - 6, cross + 6
    mask3 = np.zeros((SIZE2, SIZE2, SIZE2), np.uint8)
    paint(mask3, f1, r=1.6)
    paint(mask3, f2, r=1.6)
    g0, g1 = 52, 64
    gap2 = f1[g0:g1].copy()
    brk2 = [Break(bid=0, piece_id=0, fiber_id=1, gap_pts=gap2,
                  left_end=f1[g0 - 1].copy(), right_end=f1[g1].copy())]
    cmask3 = mask3.copy()
    del_pts3, _ = ex.delete_gap_voxels(cmask3, f1, g0, g1, cKDTree(f2), r0=2.6)
    cmask3[tuple(del_pts3.T)] = 0
    del_pts4, _ = ex.delete_gap_voxels(cmask3, f2, g2a, g2b, cKDTree(f1), r0=2.6)
    cmask3[tuple(del_pts4.T)] = 0
    pa3 = [Piece(pid=0, fiber_id=1, pts=f1[:g0].copy()),
           Piece(pid=1, fiber_id=1, pts=f1[g1:].copy()),
           Piece(pid=2, fiber_id=2, pts=f2[:g2a].copy()),
           Piece(pid=3, fiber_id=2, pts=f2[g2b:].copy())]
    dist3 = ndimage.distance_transform_edt(cmask3 == 0)
    ends3 = collect_endpoints(pa3, dist3, SIZE2)
    attach_gt_breaks(ends3, brk2)
    world3 = World(pa3, cmask3)
    eL = next(e for e in ends3 if e.is_break_end and e.side == 0)
    eR = next(e for e in ends3 if e.is_break_end and e.side == 1)
    print("dist left-end -> correct right-end:",
          round(float(np.linalg.norm(eL.pos - eR.pos)), 2))
    for o in ends3:
        if o.eid != eL.eid:
            print(f"dist left-end -> e{o.eid} (fiber {o.fiber_id}, "
                  f"break_end={o.is_break_end}):",
                  round(float(np.linalg.norm(eL.pos - o.pos)), 2))
    for name, fn in (("A", method_a), ("B", method_b)):
        props = fn(ends3, world3)
        res = classify_proposals(props, ends3, brk2)
        detail = [(ends3[pr.ei].fiber_id, ends3[pr.ej].fiber_id)
                  for pr in props]
        print(f"[method {name}] repaired={res['repaired']} "
              f"false_cross={len(res['false_cross'])} "
              f"extra={len(res['extra_same'])} pairs(fibers)={detail}")


if __name__ == "__main__":
    main()
