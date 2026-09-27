"""Visualization: maximum-intensity projections of GT / corrupted / results."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

GAP = "#ffd60a"      # GT gap centerline: yellow
GOOD = "#2dc653"     # correct repair: green
FALSE = "#e63946"    # false cross-fiber link: red
EXTRA = "#ff8c00"    # extra same-fiber link: orange
UNREP = "#d100d1"    # unrepaired break marker: magenta


def _mip(mask: np.ndarray, axis: int) -> np.ndarray:
    return mask.max(axis=axis)


def _proj(pts: np.ndarray, axis: int) -> tuple[np.ndarray, np.ndarray]:
    keep = [a for a in range(3) if a != axis]
    return pts[:, keep[0]], pts[:, keep[1]]


def draw_state(ax, mask, breaks, proposals, ends, axis, title, show_gt=True,
               show_unrepaired=True):
    mip = _mip(mask, axis)
    ax.imshow(mip.T, cmap="gray_r", origin="lower", alpha=0.85,
              extent=(0, mip.shape[1], 0, mip.shape[0]))
    if show_gt:
        for b in breaks:
            u, v = _proj(b.gap_pts, axis)
            ax.plot(u, v, color=GAP, lw=2.2, alpha=0.95, solid_capstyle="round")
    for pr in proposals:
        ei, ej = ends[pr.ei], ends[pr.ej]
        if ei.is_break_end and ej.is_break_end and ei.bid == ej.bid \
                and ei.side != ej.side:
            col, lw, al = GOOD, 2.0, 0.95
        elif ei.fiber_id == ej.fiber_id:
            col, lw, al = EXTRA, 1.6, 0.9
        else:
            col, lw, al = FALSE, 1.6, 0.9
        u, v = _proj(pr.connector, axis)
        ax.plot(u, v, color=col, lw=lw, alpha=al)
    # mark unrepaired breaks
    repaired = set()
    for pr in proposals:
        ei, ej = ends[pr.ei], ends[pr.ej]
        if ei.is_break_end and ej.is_break_end and ei.bid == ej.bid \
                and ei.side != ej.side:
            repaired.add(ei.bid)
    if show_unrepaired:
        for b in breaks:
            if b.bid not in repaired:
                u, v = _proj(b.gap_pts[None][0][None], axis)
                ax.plot([u[0]], [v[0]], marker="x", color=UNREP, ms=9, mew=2)
    ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])


def fig_gt_corrupted(gt_mask, cmask, breaks, ends, out_png, size):
    """2x2: rows = GT / corrupted, cols = MIP along z (axis 0) and x (axis 2)."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 11))
    draw_state(axes[0, 0], gt_mask, breaks, [], ends, 0,
               "Ground truth (max proj. along z)", show_unrepaired=False)
    draw_state(axes[0, 1], gt_mask, breaks, [], ends, 2,
               "Ground truth (max proj. along x)", show_unrepaired=False)
    draw_state(axes[1, 0], cmask, breaks, [], ends, 0,
               "Corrupted: artificial breaks removed (z)")
    draw_state(axes[1, 1], cmask, breaks, [], ends, 2,
               "Corrupted: artificial breaks removed (x)")
    fig.suptitle("fiber-skeletons cube s1_00497_01497_03997_256 — "
                 "GT vs corrupted", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)


def fig_method(gt_mask, cmask, breaks, proposals, ends, method, out_png):
    """Result masks with connectors for one method (z and x projections)."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 6))
    draw_state(axes[0], cmask, breaks, proposals, ends, 0,
               f"Method {method}: result (max proj. along z)")
    draw_state(axes[1], cmask, breaks, proposals, ends, 2,
               f"Method {method}: result (max proj. along x)")
    fig.suptitle(
        f"Method {method} — green: correct repair, red: false (cross-fiber) "
        "link, orange: extra same-fiber link, magenta x: unrepaired break",
        fontsize=11)
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)


def fig_compare(gt_mask, cmask, breaks, props_a, props_b, ends, out_png):
    """A vs B side by side on the same projection."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.4))
    draw_state(axes[0], cmask, breaks, props_a, ends, 0, "A: nearest endpoints")
    draw_state(axes[1], cmask, breaks, props_b, ends, 0, "B: geometry/topology-aware")
    fig.suptitle("Reconnection quality: A vs B (max proj. along z; "
                 "GT gaps in yellow)", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)


def fig_hard_case(gt_mask, cmask, breaks, props_a, props_b, ends, out_png,
                  near_parallel, max_plots=4):
    """Zoomed views of breaks near parallel/crossing fibers (the hard subgroup).

    Each panel: (z, y) slab of the corrupted mask, max-projected along x, with
    the GT gap (yellow), method A proposals (dashed) and method B proposals
    (solid). Green = correct repair, red = false cross-fiber link,
    orange = extra same-fiber link.
    """
    hard = [b for b in breaks if near_parallel.get(b.bid, False)]
    if not hard:
        return False
    hard = hard[:max_plots]
    fig, axes = plt.subplots(1, len(hard), figsize=(5.2 * len(hard), 5.6),
                             squeeze=False)
    half = 30
    for ax, b in zip(axes[0], hard):
        c = b.gap_pts.mean(axis=0)
        lo = np.maximum(0, (c - half).astype(int))
        hi = np.minimum(np.asarray(cmask.shape), (c + half).astype(int))
        sub = cmask[lo[0]:hi[0], lo[1]:hi[1], :].max(axis=2)  # (z, y) slab
        ax.imshow(sub.T, cmap="gray_r", origin="lower", alpha=0.9,
                  extent=(lo[0], hi[0], lo[1], hi[1]), interpolation="nearest")
        u, v = _proj(b.gap_pts, 2)          # u = z, v = y
        ax.plot(u, v, color=GAP, lw=3.0, solid_capstyle="round")

        def draw(props, ls):
            for pr in props:
                ei, ej = ends[pr.ei], ends[pr.ej]
                mid = (ei.pos + ej.pos) / 2
                if np.linalg.norm(mid - c) > half * 1.5:
                    continue
                if ei.is_break_end and ej.is_break_end and ei.bid == ej.bid \
                        and ei.side != ej.side:
                    col = GOOD
                elif ei.fiber_id == ej.fiber_id:
                    col = EXTRA
                else:
                    col = FALSE
                u2, v2 = _proj(pr.connector, 2)
                ax.plot(u2, v2, color=col, lw=2.0, ls=ls, alpha=0.95)

        draw(props_a, "--")
        draw(props_b, "-")
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_title(f"break #{b.bid} (near parallel fiber), "
                     f"L={len(b.gap_pts)}", fontsize=10)
        ax.set_xlabel("z")
        ax.set_ylabel("y")
    fig.suptitle("Hard subgroup: breaks next to other fibers — solid = B, "
                 "dashed = A; green correct, red false, orange extra",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)
    return True


def fig_ablation(rows: list[dict], out_png):
    """Ablation ladder: repaired % and false cross-fiber links per variant."""
    names = [r["method"] for r in rows]
    rep = [r["repaired_pct"] for r in rows]
    fls = [r["false_cross_fiber"] for r in rows]
    x = range(len(names))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
    bars1 = ax1.bar(x, rep, color=["#9e9e9e", "#bdbdbd", "#ffb703",
                                   "#fb8500", "#219ebc", "#8ecae6",
                                   "#023047"][:len(names)])
    ax1.set_xticks(list(x), names, rotation=20, ha="right", fontsize=9)
    ax1.set_ylabel("breaks repaired, %")
    ax1.set_ylim(0, 100)
    ax1.bar_label(bars1, fmt="%.0f", fontsize=9)
    ax1.set_title("Repaired breaks (of all artificial breaks)", fontsize=11)
    bars2 = ax2.bar(x, fls, color="#e63946")
    ax2.set_xticks(list(x), names, rotation=20, ha="right", fontsize=9)
    ax2.set_ylabel("false cross-fiber links")
    ax2.bar_label(bars2, fmt="%d", fontsize=9)
    ax2.set_title("False connections (different fibers joined)", fontsize=11)
    fig.suptitle("Ablation: what makes the geometry-aware method work?",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)


def fig_tau_sweep(series: dict, taus: list, n_breaks: int, out_png):
    """Frontier per ablation variant: repaired % and false links vs tau."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4))
    colors = {"A1": "#9e9e9e", "B1a": "#ffb703", "B1b": "#fb8500",
              "B1c": "#219ebc", "B2": "#8ecae6", "B3": "#023047",
              "B1": "#219ebc"}
    for name, (rep_s, fl_s) in series.items():
        ax1.plot(taus, rep_s, marker="o", color=colors.get(name), label=name)
        ax2.plot(taus, fl_s, marker="o", color=colors.get(name), label=name)
    ax1.set_xlabel("acceptance threshold tau")
    ax1.set_ylabel("breaks repaired, %")
    ax1.axvline(1.2, color="k", ls=":", lw=1)
    ax1.text(1.22, ax1.get_ylim()[0] + 4, "tau used in main table",
             fontsize=8)
    ax1.set_title(f"Repaired breaks (n={n_breaks})", fontsize=11)
    ax2.set_xlabel("acceptance threshold tau")
    ax2.set_ylabel("false cross-fiber links")
    ax2.axvline(1.2, color="k", ls=":", lw=1)
    ax2.set_title("False connections vs tau", fontsize=11)
    ax1.legend(fontsize=9)
    ax2.legend(fontsize=9)
    fig.suptitle("Tau sweep: feature-set trade-off frontiers", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)
