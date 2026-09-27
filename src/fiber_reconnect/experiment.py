"""Core experiment: artificial breaks + two endpoint-reconnection baselines.

Pipeline
--------
1. Load fiber polylines from the NML (per tree = per fiber), clip to the cube.
2. Corrupt: cut random interior arc segments out of some fibers, delete the
   corresponding mask voxels (only voxels owned by that fiber), keep GT.
3. Build the method-visible world: remaining piece polylines + corrupted mask,
   dangling endpoints with tangent/curvature features, border/tip filters.
4. Method A: greedy nearest-endpoint pairing (distance only), straight connectors.
   Method B: curvature/tangent/crossing-aware cost + global (Hungarian)
   assignment, smooth tangent-continuous connectors.
5. Score both against GT: repaired breaks, false (cross-fiber) links,
   extra same-fiber links, positional error of the restored segment.

All hyperparameters are fixed a priori (not tuned on the evaluation cube).
Coordinates are local cube voxels in (z, y, x) order.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

from fiber_reconnect.nml_io import (
    chain_decomposition,
    cube_name_to_origin,
    parse_nml,
    resample_polyline,
)

# ---------------------------------------------------------------------------
# config (fixed a priori)
# ---------------------------------------------------------------------------
D_MAX = 34.0           # max endpoint gap distance either method may bridge (voxels)
D_MIN = 3.0            # endpoints closer than this are not separate tips
STUB_MARGIN = 12       # min remaining arc length on each side of a cut (voxels)
GAP_LEN_MIN, GAP_LEN_MAX = 8, 20    # artificial break length range (voxels)
P_BREAK_1 = 0.75       # prob. of one break per eligible fiber
P_BREAK_2 = 0.35       # prob. of a second break on long fibers
ELIGIBLE_LEN = 50      # min fiber arc length to receive a break
DEL_RADIUS0 = 5.0      # deletion tube radius: mask tubes are ~3 vox thick, so a
                       # clean sever needs to remove the full cross-section
BORDER_MARGIN = 3.0    # endpoints this close to a cube face are border cuts
TIP_FWD = 3.0          # look this far along the outward tangent for the tip rule
TIP_DIST_THR = 1.5     # dist-to-fiber beyond this at the forward point => tip
TANGENT_K = 6          # voxels spanned by the end-tangent average
CURV_MIN_PTS = 8       # need this many points for a curvature estimate
CURV_MAX = 0.12        # clamp on curvature (rad/voxel)
W_D = 1.0              # method B weights: distance
W_ALIGN = 1.0          # tangent alignment
W_CURV = 0.7           # curvature residual
W_CROSS = 3.0          # crossing other fibers
ALIGN_FORBID = -0.15   # tangents pointing backwards forbid a candidate
TAU_ACCEPT = 1.2       # method B rejects assignments above this cost
CONNECT_R = 2.0        # paint radius of connectors into result masks
NEAR_PARALLEL_R = 6.0  # subgroup: other fiber within this dist of a gap


# ---------------------------------------------------------------------------
# data structures
# ---------------------------------------------------------------------------
@dataclass
class Piece:
    pid: int
    fiber_id: int          # GT: NML tree id
    pts: np.ndarray        # (N, 3) local (z, y, x), ~1 voxel arc spacing


@dataclass
class Break:
    bid: int
    piece_id: int
    fiber_id: int
    gap_pts: np.ndarray    # GT deleted centerline (M, 3)
    left_end: np.ndarray   # GT tip of the left stub (3,)
    right_end: np.ndarray  # GT tip of the right stub (3,)
    del_radius: float = 0.0


@dataclass
class EndPoint:
    eid: int
    pid: int               # piece-after id the endpoint belongs to
    pos: np.ndarray        # (3,)
    tangent: np.ndarray    # outward unit tangent
    kappa: float           # |curvature| estimate (rad/voxel), 0 if straight
    normal: np.ndarray     # unit normal toward the curvature center (or 0)
    # --- GT-only fields (never visible to the methods) ---
    fiber_id: int = -1
    is_break_end: bool = False
    bid: int = -1
    side: int = -1         # 0 = left stub, 1 = right stub


@dataclass
class Proposal:
    method: str
    ei: int
    ej: int
    cost: float
    connector: np.ndarray  # (M, 3) polyline


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def load_pieces(nml_path: str, cube_name: str) -> list[Piece]:
    """NML trees -> clipped, resampled polylines in local (z, y, x) coords."""
    trees, _scale = parse_nml(nml_path)
    z0, y0, x0, size = cube_name_to_origin(cube_name)
    pieces: list[Piece] = []
    pid = 0
    for tree in trees:
        for chain in chain_decomposition(tree):
            nodes = np.asarray([tree.positions[n] for n in chain])  # global x,y,z
            local = np.stack(
                [nodes[:, 2] - z0, nodes[:, 1] - y0, nodes[:, 0] - x0], axis=1
            )
            rs = resample_polyline(local, 1.0)
            inb = np.all((rs >= 0) & (rs < size), axis=1)
            # contiguous in-cube runs
            idx = np.where(inb)[0]
            if len(idx) == 0:
                continue
            splits = np.where(np.diff(idx) > 1)[0]
            for run in np.split(idx, splits + 1):
                if len(run) >= 10:
                    pieces.append(Piece(pid=pid, fiber_id=tree.tree_id,
                                        pts=rs[run].copy()))
                    pid += 1
    return pieces


# ---------------------------------------------------------------------------
# corruption
# ---------------------------------------------------------------------------
def pick_gaps(n_pts: int, rng: np.random.Generator) -> list[tuple[int, int]]:
    """Arc-index ranges (g0, g1) of artificial gaps on one piece."""
    gaps: list[tuple[int, int]] = []
    if n_pts < ELIGIBLE_LEN + 2 * STUB_MARGIN:
        return gaps
    n_gaps = 0
    if rng.random() < P_BREAK_1:
        n_gaps = 1
        if n_pts >= 100 and rng.random() < P_BREAK_2:
            n_gaps = 2
    tries = 0
    while len(gaps) < n_gaps and tries < 30:
        tries += 1
        L = int(rng.integers(GAP_LEN_MIN, GAP_LEN_MAX + 1))
        lo = STUB_MARGIN + L
        hi = n_pts - STUB_MARGIN - L
        if hi <= lo:
            continue
        c = int(rng.integers(lo, hi))
        g0, g1 = c, c + L
        if all(g1 + STUB_MARGIN < a or b + STUB_MARGIN < g0 for a, b in gaps):
            gaps.append((g0, g1))
    return sorted(gaps)


def _severance_ok(mask_box: np.ndarray, del_local: np.ndarray,
                  gap_local: np.ndarray, r_del: float) -> bool:
    """After deleting del_local voxels from mask_box, are the two stub tips
    (nearest surviving voxels just beyond the deleted tube) in different
    connected components?"""
    box = mask_box.copy()
    box[tuple(del_local.T)] = 0
    lab, _ = ndimage.label(box > 0, structure=np.ones((3, 3, 3), int))
    shape = np.asarray(box.shape)
    tips = []
    for t in (gap_local[0], gap_local[-1]):
        c = np.clip(np.round(t).astype(int), 0, shape - 1)
        # nearest surviving component around the tip (ball covers the tube)
        for r in range(1, int(r_del) + 5):
            zz, yy, xx = np.ogrid[-r:r + 1, -r:r + 1, -r:r + 1]
            ball = (zz**2 + yy**2 + xx**2) <= r * r
            offs = np.stack(np.where(ball), axis=1) - r
            pts = np.clip(c[None, :] + offs, 0, shape - 1)
            vals = lab[pts[:, 0], pts[:, 1], pts[:, 2]]
            vals = vals[vals > 0]
            if len(vals):
                tips.append(int(np.bincount(vals).argmax()))
                break
    return len(tips) == 2 and tips[0] != tips[1]


def delete_gap_voxels(
    mask: np.ndarray,
    piece_pts: np.ndarray,
    g0: int,
    g1: int,
    other_tree: cKDTree,
    r0: float = DEL_RADIUS0,
) -> tuple[np.ndarray, float]:
    """Mask voxels of this fiber around the gap to delete (other fibers kept).

    The cut is PERPENDICULAR to the fiber (like a real break): a voxel is
    deleted if its arc-projection onto the piece polyline falls inside the
    slab [g0 - r, g1 + r), it lies within r_cut of the piece centerline (this
    fiber's tube), and the piece centerline is its nearest centerline
    (ownership by proximity -> neighboring fibers keep their voxels).
    Returns (voxel coords (M,3), slab half-width used).
    """
    size = mask.shape
    piece_tree = cKDTree(piece_pts)
    r_cut = r0 - 0.5      # tube radius ~3.5, cut radius a bit larger
    r = r0
    for _ in range(4):
        gmin, gmax = piece_pts[g0:g1].min(axis=0), piece_pts[g0:g1].max(axis=0)
        lo = np.maximum(0, np.floor(gmin - (r + 7)).astype(int))
        hi = np.minimum(size, np.ceil(gmax + (r + 8)).astype(int))
        box = mask[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        box_vox = np.argwhere(box > 0)
        if len(box_vox) == 0:
            return np.empty((0, 3), int), r
        vf = box_vox.astype(float)
        d_p, k_idx = piece_tree.query(vf + lo, k=1, workers=-1)
        d_oth, _ = other_tree.query(vf + lo, k=1, workers=-1)
        sel = ((k_idx >= g0 - r) & (k_idx < g1 + r)
               & (d_p <= r_cut) & (d_p <= d_oth + 1e-9))
        del_pts = box_vox[sel]
        if len(del_pts) == 0:
            return np.empty((0, 3), int), r
        gap_local = piece_pts[g0:g1] - lo
        if _severance_ok(box, del_pts, gap_local, r):
            return del_pts + lo, r
        r += 1.0
    return np.empty((0, 3), int), r


def corrupt(pieces: list[Piece], mask: np.ndarray,
            seed: int = 20260926) -> tuple[np.ndarray, list[Break], list[Piece]]:
    """Apply artificial breaks. Returns (corrupted_mask, breaks, pieces_after)."""
    rng = np.random.default_rng(seed)
    cmask = mask.copy()

    plan = []
    for p in pieces:
        gaps = pick_gaps(len(p.pts), rng)
        if gaps:
            plan.append((p, gaps))

    breaks: list[Break] = []
    cut_ranges: dict[int, list[tuple[int, int, int]]] = {}
    for p, gaps in plan:
        others = [q for q in pieces if q.pid != p.pid]
        other_tree = (cKDTree(np.vstack([q.pts for q in others]))
                      if others else cKDTree(np.full((1, 3), -1e6)))
        for g0, g1 in gaps:
            deleted, r = delete_gap_voxels(cmask, p.pts, g0, g1, other_tree)
            if len(deleted) == 0:
                continue  # could not sever; skip this candidate break
            cmask[tuple(deleted.T)] = 0
            cut_ranges.setdefault(p.pid, []).append((g0, g1, int(np.ceil(r))))

    # pieces after corruption (what a tracer on the corrupted mask would see).
    # Segments adjacent to a cut are trimmed to the surviving mask: leading
    # points whose centerline voxel was deleted are dropped, so piece tips sit
    # exactly on the corrupted mask boundary. For every trimmed segment we
    # record its surviving first/last indices in the ORIGINAL piece pts.
    pieces_after: list[Piece] = []
    nxt = max((p.pid for p in pieces), default=-1) + 1
    # (pid, seg_start, seg_end) -> (first_surv_idx, last_surv_idx) in p.pts
    surv: dict[tuple[int, int, int], tuple[int, int]] = {}
    for p in pieces:
        cuts = sorted(cut_ranges.get(p.pid, []))
        segs, cur = [], 0
        for g0, g1, m in cuts:
            if g0 - m > cur:
                segs.append((cur, g0 - m))
            cur = g1 + m
        if cur < len(p.pts):
            segs.append((cur, len(p.pts)))
        for s0, s1 in segs:
            seg = p.pts[s0:s1]
            a, b = 0, len(seg)
            if s0 > 0:  # start right after a gap -> trim from the start
                while a < b and not _in_mask(cmask, seg[a]):
                    a += 1
            if s1 < len(p.pts):  # end right before a gap -> trim from the end
                while b > a and not _in_mask(cmask, seg[b - 1]):
                    b -= 1
            if b - a >= 3:
                pieces_after.append(Piece(pid=nxt, fiber_id=p.fiber_id,
                                          pts=seg[a:b].copy()))
                surv[(p.pid, s0, s1)] = (s0 + a, s0 + b - 1)
                nxt += 1

    # one Break record per cut; tips = surviving-mask tips (method-visible)
    for p in pieces:
        cuts = sorted(cut_ranges.get(p.pid, []))
        for k, (g0, g1, m) in enumerate(cuts):
            left_seg = ((p.pid, 0, g0 - m) if k == 0
                        else (p.pid, cuts[k - 1][1] + cuts[k - 1][2], g0 - m))
            right_seg = ((p.pid, g1 + m, len(p.pts)) if k == len(cuts) - 1
                         else (p.pid, g1 + m, cuts[k + 1][0] - cuts[k + 1][2]))
            if left_seg not in surv or right_seg not in surv:
                continue  # a stub vanished entirely -> break unrepairable
            breaks.append(Break(
                bid=len(breaks), piece_id=p.pid, fiber_id=p.fiber_id,
                gap_pts=p.pts[g0:g1].copy(),
                left_end=p.pts[surv[left_seg][1]].copy(),
                right_end=p.pts[surv[right_seg][0]].copy(),
                del_radius=float(m)))
    return cmask, breaks, pieces_after


def _in_mask(cmask: np.ndarray, pt: np.ndarray) -> bool:
    idx = np.clip(np.round(pt).astype(int), 0, np.asarray(cmask.shape) - 1)
    return bool(cmask[idx[0], idx[1], idx[2]])


# ---------------------------------------------------------------------------
# endpoints
# ---------------------------------------------------------------------------
def outward_tangent(pts: np.ndarray, at_start: bool):
    """(outward unit tangent, curvature, curvature normal) at a piece end."""
    n = len(pts)
    k = min(TANGENT_K, n - 1)
    if at_start:
        tang = pts[0] - pts[k]
    else:
        tang = pts[-1] - pts[-1 - k]
    nt = float(np.linalg.norm(tang))
    tang = tang / nt if nt > 1e-9 else np.zeros(3)

    kappa, normal = 0.0, np.zeros(3)
    if n >= CURV_MIN_PTS:
        # direction over the first/last ~3 voxels vs direction CURV_MIN_PTS-1 in
        if at_start:
            t_e = -(pts[min(3, n - 1)] - pts[0])
            t_f = -(pts[CURV_MIN_PTS - 1] - pts[max(CURV_MIN_PTS - 4, 0)])
        else:
            t_e = pts[-1] - pts[max(n - 4, 0)]
            t_f = pts[max(n - CURV_MIN_PTS, 0)] - pts[max(n - CURV_MIN_PTS - 1, 0)]
        for t in (t_e, t_f):
            nn = np.linalg.norm(t)
            if nn > 1e-9:
                t /= nn
        arc = float(np.linalg.norm(pts[-1] - pts[max(n - CURV_MIN_PTS, 0)])) \
            if not at_start else \
            float(np.linalg.norm(pts[min(CURV_MIN_PTS - 1, n - 1)] - pts[0]))
        dt = t_e - t_f
        dtn = float(np.linalg.norm(dt))
        if arc > 2.0 and dtn > 1e-9:
            kappa = min(dtn / arc, CURV_MAX)
            normal = dt / dtn
    return tang, kappa, normal


def collect_endpoints(
    pieces_after: list[Piece],
    dist_to_fiber: np.ndarray,
    size: int,
) -> list[EndPoint]:
    """Dangling endpoints visible to the methods (border ends filtered out)."""
    ends: list[EndPoint] = []
    eid = 0
    for p in pieces_after:
        for at_start in (True, False):
            pos = p.pts[0] if at_start else p.pts[-1]
            tang, kappa, normal = outward_tangent(p.pts, at_start)
            if float(np.linalg.norm(tang)) < 1e-6:
                continue
            # border rule: cut by the cube edge, not a real break
            if min(pos) < BORDER_MARGIN or max(pos) > size - 1 - BORDER_MARGIN:
                continue
            # tip rule: does the mask continue beyond the endpoint?
            fwd = pos + TIP_FWD * tang
            if np.all((fwd >= 0) & (fwd < size - 1)):
                d = dist_to_fiber[int(round(fwd[0])), int(round(fwd[1])),
                                  int(round(fwd[2]))]
                if d < TIP_DIST_THR:
                    continue  # fiber continues -> not a dangling tip
            ends.append(EndPoint(eid=eid, pid=p.pid, pos=pos.copy(),
                                 tangent=tang, kappa=kappa, normal=normal,
                                 fiber_id=p.fiber_id))
            eid += 1
    return ends


def attach_gt_breaks(ends: list[EndPoint], breaks: list[Break], tol: float = 2.5):
    """Mark which endpoints are the two sides of an inserted break (GT only)."""
    for b in breaks:
        for side, tip in ((0, b.left_end), (1, b.right_end)):
            best, bd = None, tol
            for e in ends:
                d = float(np.linalg.norm(e.pos - tip))
                if d < bd:
                    best, bd = e, d
            if best is not None:
                best.is_break_end = True
                best.bid = b.bid
                best.side = side


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------
def circ_extrapolate(e: EndPoint, d: float) -> np.ndarray:
    """Position d voxels along the fiber assuming local circular curvature."""
    kd = e.kappa * d
    if e.kappa > 1e-6 and kd < np.pi / 2:
        return e.pos + (np.sin(kd) / e.kappa) * e.tangent \
            + ((1 - np.cos(kd)) / e.kappa) * e.normal
    return e.pos + d * e.tangent


def bezier_connector(ei: EndPoint, ej: EndPoint, d: float,
                     spacing: float = 0.7) -> np.ndarray:
    """Tangent-continuous cubic Bezier between two endpoints."""
    p0, p3 = ei.pos, ej.pos
    p1 = ei.pos + (circ_extrapolate(ei, d) - ei.pos) / 3.0
    p2 = ej.pos + (circ_extrapolate(ej, d) - ej.pos) / 3.0
    n = max(6, int(np.ceil(d / spacing)))
    s = np.linspace(0, 1, n)[:, None]
    return ((1 - s) ** 3) * p0 + 3 * ((1 - s) ** 2) * s * p1 \
        + 3 * (1 - s) * s**2 * p2 + s**3 * p3


def straight_connector(pi: np.ndarray, pj: np.ndarray,
                       spacing: float = 0.7) -> np.ndarray:
    d = float(np.linalg.norm(pj - pi))
    n = max(2, int(np.ceil(d / spacing)))
    s = np.linspace(0, 1, n)[:, None]
    return pi * (1 - s) + pj * s


class World:
    """Everything the methods are allowed to see (no GT identity)."""

    def __init__(self, pieces_after: list[Piece], cmask: np.ndarray):
        self.pieces = {p.pid: p for p in pieces_after}
        self.piece_trees = {p.pid: cKDTree(p.pts) for p in pieces_after}
        self.cmask = cmask
        self.dist_fiber = ndimage.distance_transform_edt(cmask == 0)

    def crossing(self, ei: EndPoint, ej: EndPoint, conn: np.ndarray) -> bool:
        """Does the connector pass through voxels of *other* fibers?"""
        ti, tj = self.piece_trees[ei.pid], self.piece_trees[ej.pid]
        for s in conn:
            if float(ti.query(s[None], workers=-1)[0][0]) <= 3.5:
                continue
            if float(tj.query(s[None], workers=-1)[0][0]) <= 3.5:
                continue
            idx = np.clip(np.round(s).astype(int), 0,
                          np.asarray(self.cmask.shape) - 1)
            if self.dist_fiber[idx[0], idx[1], idx[2]] < 1.2:
                return True
        return False


# ---------------------------------------------------------------------------
# methods
# ---------------------------------------------------------------------------
def candidate_pairs(ends: list[EndPoint], world: World):
    """All (i, j, d) endpoint pairs the methods may consider."""
    pairs = []
    n = len(ends)
    P = np.asarray([e.pos for e in ends])
    for i in range(n):
        for j in range(i + 1, n):
            if ends[i].pid == ends[j].pid:
                continue  # a remaining piece is never paired with itself
            d = float(np.linalg.norm(P[j] - P[i]))
            if D_MIN <= d <= D_MAX:
                pairs.append((i, j, d))
    return pairs


def method_a(ends: list[EndPoint], world: World) -> list[Proposal]:
    """A0: greedy nearest-endpoint pairing; straight connectors."""
    props = []
    used: set[int] = set()
    for i, j, d in sorted(candidate_pairs(ends, world), key=lambda t: t[2]):
        if i in used or j in used:
            continue
        used.update((i, j))
        props.append(Proposal(method="A0", ei=i, ej=j, cost=d,
                              connector=straight_connector(ends[i].pos,
                                                           ends[j].pos)))
    return props


def build_cost_matrix(ends: list[EndPoint], world: World,
                      use_align_hard: bool = True, use_align_soft: bool = True,
                      use_curv: bool = True,
                      use_cross: bool = True) -> np.ndarray:
    """Cost matrix for all candidate endpoint pairs (1e6 = forbidden).

    The tangent cue has two separable parts:
      use_align_hard — a candidate is FORBIDDEN if either endpoint's outward
        tangent points away from the other end (align < ALIGN_FORBID);
      use_align_soft — a soft penalty W_ALIGN * mean(1 - align) on the cost.
    """
    pairs = candidate_pairs(ends, world)
    n = len(ends)
    C = np.full((n, n), 1e6)
    if not pairs:
        np.fill_diagonal(C, 1e6)
        return C
    for i, j, d in pairs:
        ei, ej = ends[i], ends[j]
        cost = W_D * (d / D_MAX)
        a_i = a_j = None
        if use_align_hard or use_align_soft:
            u = (ej.pos - ei.pos) / d
            a_i = float(ei.tangent @ u)
            a_j = float(-ej.tangent @ u)
            if use_align_hard and (a_i < ALIGN_FORBID or a_j < ALIGN_FORBID):
                continue  # a tangent points away from the partner
            if use_align_soft:
                cost += W_ALIGN * ((1 - a_i) + (1 - a_j)) / 2.0
        if use_curv:
            cres = (float(np.linalg.norm(circ_extrapolate(ei, d) - ej.pos))
                    + float(np.linalg.norm(circ_extrapolate(ej, d) - ei.pos))) / 2.0
            cost += W_CURV * cres / max(d, 1.0)
        if use_cross:
            conn = bezier_connector(ei, ej, d)
            if world.crossing(ei, ej, conn):
                cost += W_CROSS
        C[i, j] = C[j, i] = cost
    np.fill_diagonal(C, 1e6)
    return C


def assign_and_filter(C: np.ndarray, ends: list[EndPoint],
                      tau: float, name: str = "B") -> list[Proposal]:
    """Hungarian assignment + tau filter + one-to-one greedy filter."""
    rows, cols = linear_sum_assignment(C)
    cand = []
    for r, c in zip(rows, cols):
        if r != c and C[r, c] < 1e5 and C[r, c] <= tau:
            cand.append((float(C[r, c]), int(r), int(c)))
    cand.sort()
    used: set[int] = set()
    props = []
    for cost, i, j in cand:
        if i in used or j in used or i == j:
            continue
        used.update((i, j))
        props.append(Proposal(
            method=name, ei=i, ej=j, cost=cost,
            connector=bezier_connector(
                ends[i], ends[j],
                float(np.linalg.norm(ends[i].pos - ends[j].pos)))))
    return props


def method_scored(ends: list[EndPoint], world: World,
                  use_align_hard: bool = True, use_align_soft: bool = True,
                  use_curv: bool = True, use_cross: bool = True,
                  tau: float = TAU_ACCEPT, name: str = "B") -> list[Proposal]:
    """Global (Hungarian) assignment with selectable cost components.

    Ablation ladder (same candidate pairs, same matching machinery, same tau;
    only the cost function differs):
      A1:  all feature flags False                     (distance only)
      B1a: use_align_hard only                         (forbid backwards)
      B1b: use_align_soft only                         (soft alignment cost)
      B1c: use_align_hard + use_align_soft             (tangent, full)
      B2:  B1c + curvature residual
      B3:  B1c + curvature + crossing penalty          (== full method B)
    A cost above `tau` rejects the assignment -> the endpoint stays unpaired.
    """
    C = build_cost_matrix(ends, world, use_align_hard, use_align_soft,
                          use_curv, use_cross)
    return assign_and_filter(C, ends, tau, name)


def method_scored_sweep(ends: list[EndPoint], world: World,
                        taus: list[float], use_align_hard: bool = True,
                        use_align_soft: bool = True, use_curv: bool = True,
                        use_cross: bool = True,
                        name: str = "B") -> dict[float, list[Proposal]]:
    """Tau sweep: cost matrix computed once (assignment is tau-independent)."""
    C = build_cost_matrix(ends, world, use_align_hard, use_align_soft,
                          use_curv, use_cross)
    return {tau: assign_and_filter(C, ends, tau, name) for tau in taus}


def method_a1(ends: list[EndPoint], world: World) -> list[Proposal]:
    """Distance-only cost + Hungarian assignment (no geometry features)."""
    return method_scored(ends, world, use_align_hard=False,
                         use_align_soft=False, use_curv=False,
                         use_cross=False, name="A1")


def method_b(ends: list[EndPoint], world: World) -> list[Proposal]:
    """Full geometry/topology-aware method (B3)."""
    return method_scored(ends, world, name="B3")


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
def classify_proposals(props: list[Proposal], ends: list[EndPoint],
                       breaks: list[Break]) -> dict:
    """Score proposals against GT."""
    repaired: set[int] = set()
    false_cross, extra_same = [], []
    for pr in props:
        ei, ej = ends[pr.ei], ends[pr.ej]
        if ei.is_break_end and ej.is_break_end and ei.bid == ej.bid \
                and ei.side != ej.side:
            repaired.add(ei.bid)
        elif ei.fiber_id == ej.fiber_id:
            extra_same.append(pr)
        else:
            false_cross.append(pr)
    return {"repaired": sorted(repaired),
            "false_cross": false_cross,
            "extra_same": extra_same,
            "unrepaired": [b.bid for b in breaks if b.bid not in repaired]}


def _repair_connector(props: list[Proposal], ends: list[EndPoint]):
    out = {}
    for pr in props:
        ei, ej = ends[pr.ei], ends[pr.ej]
        if ei.is_break_end and ej.is_break_end and ei.bid == ej.bid \
                and ei.side != ej.side:
            out[ei.bid] = pr.connector
    return out


def position_errors(props: list[Proposal], ends: list[EndPoint],
                    breaks: list[Break]):
    """Mean/max distance from GT gap centerline to the predicted connector."""
    conns = _repair_connector(props, ends)
    mean_err, max_err = {}, {}
    for b in breaks:
        if b.bid in conns:
            d, _ = cKDTree(conns[b.bid]).query(b.gap_pts, k=1, workers=-1)
            mean_err[b.bid] = float(d.mean())
            max_err[b.bid] = float(d.max())
    return mean_err, max_err


def near_parallel_flags(breaks: list[Break], pieces: list[Piece]) -> dict[int, bool]:
    """GT subgroup: does another fiber pass close to the gap?"""
    trees = {p.pid: cKDTree(p.pts) for p in pieces}
    out = {}
    for b in breaks:
        flag = False
        for p in pieces:
            if p.fiber_id == b.fiber_id:
                continue
            d, _ = trees[p.pid].query(b.gap_pts, k=1, workers=-1)
            if d.min() <= NEAR_PARALLEL_R:
                flag = True
                break
        out[b.bid] = flag
    return out
