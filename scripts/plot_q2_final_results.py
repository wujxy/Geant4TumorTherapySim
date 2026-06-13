#!/usr/bin/env python3
"""Generate the focused Q2 F1-F4 conclusion figures in figures2/."""

import argparse
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig-g4sim")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Circle, Wedge
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_DIR / "figures2"
FIG_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from plot_assignment_results import (  # noqa: E402
    ROOT,
    open_root,
    projected_columns,
    read_cell_rows,
    read_h1,
    read_h2,
    read_run_row,
)


CAPTURE_PATHS = {
    mode: [PROJECT_DIR / f"output_q2D_capture_{mode}_seed{seed}.root" for seed in (1, 2, 3)]
    for mode in ("uniform", "cytoplasm", "shell")
}
CAPTURE_MODES = ("uniform", "cytoplasm", "shell")
CAPTURE_COLORS = {
    "uniform": "#c83f31",
    "cytoplasm": "#2f8f6b",
    "shell": "#7b3fbf",
}
THERAPY_INPUTS = [
    ("gamma", "Gamma 1 MeV", "#2f6db3"),
    ("proton", "Proton 80 MeV", "#c83f31"),
    ("neutron_uniform", "BNCT uniform", "#7b3fbf"),
    ("neutron_shell", "BNCT shell", "#d38b2f"),
]


def apply_readable_style():
    plt.rcParams.update({
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 10,
        "figure.titlesize": 16,
    })


def tumor_selectivity(tumor, normal):
    total = tumor + normal
    return tumor / total if total > 0 else 0.0


def scale_to_tumor_dose(tumor, normal, target=1.0):
    if tumor <= 0:
        raise ValueError("mean tumor dose must be positive")
    scale = target / tumor
    return tumor * scale, normal * scale, scale


def projected_dose_colormap():
    cmap = plt.get_cmap("inferno").copy()
    cmap.set_bad("black")
    cmap.set_under("black")
    return cmap


def draw_radius_arrow(ax, radius, label, angle_deg, color):
    angle = math.radians(angle_deg)
    end = (radius * math.cos(angle), radius * math.sin(angle))
    ax.annotate(
        "",
        xy=end,
        xytext=(0.0, 0.0),
        arrowprops={"arrowstyle": "->", "color": color, "linewidth": 1.6},
    )
    label_radius = 0.58 * radius
    ax.text(
        label_radius * math.cos(angle),
        label_radius * math.sin(angle),
        label,
        color=color,
        ha="center",
        va="bottom",
        fontsize=10,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.68, "pad": 1.2},
    )


def require_source_mode(run, expected, filename):
    actual = run.get("source_mode")
    if actual != expected:
        raise ValueError(f"{filename}: expected sourceMode={expected}, found {actual}")


def tree_entries(path, tree_name):
    handle = open_root(path)
    if handle is None:
        raise ValueError(f"{path.name}: cannot open ROOT file")
    tree = handle.Get(tree_name)
    entries = int(tree.GetEntries()) if tree else -1
    handle.Close()
    return entries


def validate_input(path, source_mode, expected_cells=None):
    if not path.exists():
        raise FileNotFoundError(path)
    run = read_run_row(path)
    require_source_mode(run, source_mode, path.name)
    if tree_entries(path, "EventTree") != run["n_events"]:
        raise ValueError(f"{path.name}: EventTree count does not match RunTree")
    if expected_cells is not None and tree_entries(path, "CellTree") != expected_cells:
        raise ValueError(f"{path.name}: CellTree must contain {expected_cells} rows")
    return run


def cylindrical_bin_volumes(r_edges, z_edges):
    r_edges = np.asarray(r_edges, dtype=float)
    z_edges = np.asarray(z_edges, dtype=float)
    ring_areas = math.pi * (np.square(r_edges[1:]) - np.square(r_edges[:-1]))
    return np.outer(np.diff(z_edges), ring_areas)


def spherical_shell_volumes(centers):
    centers = np.asarray(centers, dtype=float)
    dr = centers[1] - centers[0]
    inner = np.maximum(0.0, centers - 0.5 * dr)
    outer = centers + 0.5 * dr
    return 4.0 * math.pi * (np.power(outer, 3) - np.power(inner, 3)) / 3.0


def mean_std(values):
    values = np.asarray(list(values), dtype=float)
    return float(np.mean(values)), float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def capture_seed_summary(path):
    run = validate_input(path, 1, expected_cells=4096)
    captures = run["n_events"]
    tumor_map = read_h2(path, "hCellLocalTumor")
    normal_map = read_h2(path, "hCellLocalNormal")
    if tumor_map is None or normal_map is None:
        raise ValueError(f"{path.name}: missing cell-local H2")

    frame = ROOT.RDataFrame("EventTree", str(path))
    frame = frame.Define(
        "tumorNucleusHighLET",
        "edepNucleusTumorAlpha_MeV + edepNucleusTumorLi7_MeV",
    ).Define(
        "normalNucleusHighLET",
        "edepNucleusNormalAlpha_MeV + edepNucleusNormalLi7_MeV",
    )
    tumor_cell = float(np.asarray(tumor_map[2]).sum()) / captures
    normal_cell = float(np.asarray(normal_map[2]).sum()) / captures
    tumor_nucleus = float(frame.Sum("tumorNucleusHighLET").GetValue()) / captures
    normal_nucleus = float(frame.Sum("normalNucleusHighLET").GetValue()) / captures
    tumor_hit = int(frame.Filter("tumorNucleusHighLET > 0").Count().GetValue()) / captures
    normal_hit = int(frame.Filter("normalNucleusHighLET > 0").Count().GetValue()) / captures
    return {
        "tumor_cell": tumor_cell,
        "normal_cell": normal_cell,
        "tumor_nucleus": tumor_nucleus,
        "normal_nucleus": normal_nucleus,
        "tumor_hit": tumor_hit,
        "normal_hit": normal_hit,
        "selectivity": tumor_selectivity(tumor_cell, normal_cell),
    }


def capture_summaries():
    return {
        mode: [capture_seed_summary(path) for path in paths]
        for mode, paths in CAPTURE_PATHS.items()
    }


def plot_f1():
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 4.8))
    for ax, mode in zip(axes, CAPTURE_MODES):
        ax.add_patch(Circle((0, 0), 5.0, facecolor="#f2d6aa", edgecolor="#222", linewidth=1.6))
        if mode == "uniform":
            ax.add_patch(Circle((0, 0), 5.0, facecolor="#d38b2f", alpha=0.58, edgecolor="none"))
        elif mode == "cytoplasm":
            ax.add_patch(Wedge((0, 0), 5.0, 0, 360, width=2.5,
                               facecolor="#2f8f6b", alpha=0.72, edgecolor="none"))
        else:
            ax.add_patch(Wedge((0, 0), 5.0, 0, 360, width=1.0,
                               facecolor="#d38b2f", alpha=0.8, edgecolor="none"))
        nucleus_color = "#d38b2f" if mode == "uniform" else "#7aa6d8"
        ax.add_patch(Circle((0, 0), 2.5, facecolor=nucleus_color, alpha=0.8,
                            edgecolor="#244d75", linewidth=1.4))
        ax.axvline(0, color="#555", linewidth=0.5, alpha=0.4)
        ax.axhline(0, color="#555", linewidth=0.5, alpha=0.4)
        draw_radius_arrow(ax, 2.5, "nucleus radius", 130, "#244d75")
        draw_radius_arrow(ax, 5.0, "cell radius", -35, "#222")
        if mode == "shell":
            draw_radius_arrow(ax, 4.0, "shell start", 20, "#9a5d10")
        ax.set_title(f"{mode} B10", fontsize=14)
        ax.set_aspect("equal")
        ax.set_xlim(-6.5, 6.5)
        ax.set_ylim(-6.5, 6.5)
        ax.set_xlabel("x (um)")
        ax.set_ylabel("z (um)")
    fig.suptitle("F1 B10 distribution geometry")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "F1_b10_distribution_geometry.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def grouped_seed_bars(ax, summaries, keys, ylabel, title):
    x = np.arange(len(keys))
    width = 0.25
    offsets = (-width, 0.0, width)
    for offset, mode in zip(offsets, CAPTURE_MODES):
        stats = [mean_std(seed[key] for seed in summaries[mode]) for key in keys]
        ax.bar(x + offset, [s[0] for s in stats], width, yerr=[s[1] for s in stats],
               capsize=4, color=CAPTURE_COLORS[mode], label=mode, edgecolor="#222")
    ax.set_xticks(x)
    ax.set_xticklabels(["tumor", "normal"])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)


def plot_f2():
    summaries = capture_summaries()
    fig, axes = plt.subplots(1, 4, figsize=(15.8, 4.7))
    grouped_seed_bars(
        axes[0], summaries, ("tumor_cell", "normal_cell"),
        "alpha+Li7 edep (MeV / capture)", "(a) Whole-cell high-LET response",
    )
    axes[0].legend(fontsize=9)
    grouped_seed_bars(
        axes[1], summaries, ("tumor_nucleus", "normal_nucleus"),
        "alpha+Li7 edep (MeV / capture)", "(b) Nucleus high-LET response",
    )
    grouped_seed_bars(
        axes[2], summaries, ("tumor_hit", "normal_hit"),
        "P(any nucleus high-LET edep / capture)", "(c) Nucleus-hit probability",
    )

    stats = [mean_std(seed["selectivity"] for seed in summaries[mode])
             for mode in CAPTURE_MODES]
    axes[3].bar(range(3), [s[0] for s in stats], yerr=[s[1] for s in stats], capsize=4,
                color=[CAPTURE_COLORS[mode] for mode in CAPTURE_MODES], edgecolor="#222")
    axes[3].set_xticks(range(3))
    axes[3].set_xticklabels(CAPTURE_MODES)
    axes[3].set_ylim(0, 1.05)
    axes[3].set_ylabel("Etumor / (Etumor + Enormal)")
    axes[3].set_title("(d) Whole-cell high-LET selectivity")
    axes[3].grid(axis="y", alpha=0.25)
    fig.suptitle("F2 Conditional B10-capture response (3 seeds x 100k captures)")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "F2_forced_capture_quantitative.png", dpi=180)
    plt.close(fig)


def stack_capture_hist(mode, hist_name, reader):
    total = None
    axes = None
    captures = 0
    for path in CAPTURE_PATHS[mode]:
        run = validate_input(path, 1, expected_cells=4096)
        result = reader(path, hist_name)
        if result is None:
            raise ValueError(f"{path.name}: missing {hist_name}")
        captures += run["n_events"]
        if reader is read_h2:
            axes = (np.asarray(result[0]), np.asarray(result[1]))
            values = np.asarray(result[2], dtype=float)
        else:
            axes = np.asarray(result[0])
            values = np.asarray(result[1], dtype=float)
        total = values if total is None else total + values
    if total is None or float(total.sum()) <= 0:
        raise ValueError(f"{mode} {hist_name}: empty histogram")
    return axes, total / captures


def draw_cell_boundaries(ax, radial=False, labels=False):
    if radial:
        ax.axvline(2.5, color="#39a9ff", linestyle="--", linewidth=1.8,
                   label="nucleus boundary" if labels else None)
        ax.axvline(4.0, color="#56d364", linestyle=":", linewidth=1.8,
                   label="shell start" if labels else None)
        return
    for radius, color, linestyle, label in (
        (2.5, "#39a9ff", "--", "nucleus boundary"),
        (4.0, "#56d364", ":", "shell start"),
    ):
        z = np.linspace(-radius, radius, 240)
        ax.plot(np.sqrt(np.maximum(0.0, radius * radius - z * z)), z,
                color=color, linestyle=linestyle, linewidth=1.8,
                label=label if labels else None)


def plot_f3():
    panels = [
        ("uniform", "hCellLocalTumor", "hCellRadialTumor", "Tumor: uniform"),
        ("cytoplasm", "hCellLocalTumor", "hCellRadialTumor", "Tumor: cytoplasm-only"),
        ("shell", "hCellLocalTumor", "hCellRadialTumor", "Tumor: outer shell"),
        ("cytoplasm", "hCellLocalNormal", "hCellRadialNormal", "Normal control: cytoplasm-only"),
    ]
    maps = []
    radials = []
    for mode, h2_name, h1_name, title in panels:
        map_result = stack_capture_hist(mode, h2_name, read_h2)
        radial_result = stack_capture_hist(mode, h1_name, read_h1)
        volumes = cylindrical_bin_volumes(*map_result[0])
        density = np.divide(map_result[1], volumes, out=np.zeros_like(map_result[1]), where=volumes > 0)
        radial_density = radial_result[1] / spherical_shell_volumes(radial_result[0])
        maps.append((map_result[0], density, title))
        radials.append((radial_result[0], radial_density, title))

    positives = np.concatenate([density[density > 0] for _, density, _ in maps])
    vmax = float(np.max(positives))
    norm = LogNorm(vmin=max(float(np.min(positives)), vmax * 1e-5), vmax=vmax)
    radial_positive = np.concatenate([line[line > 0] for _, line, _ in radials])
    radial_min = max(float(np.min(radial_positive)), float(np.max(radial_positive)) * 1e-6)
    radial_max = float(np.max(radial_positive)) * 1.25
    density_cmap = plt.get_cmap("inferno").copy()
    density_cmap.set_bad("black")

    fig, axes = plt.subplots(2, 4, figsize=(20.5, 9.0),
                             gridspec_kw={"hspace": 0.34, "wspace": 0.18})
    for index, (ax, (edges, density, title)) in enumerate(zip(axes[0], maps)):
        image = ax.pcolormesh(edges[0], edges[1], density, cmap=density_cmap, norm=norm)
        draw_cell_boundaries(ax, labels=ax is axes[0, 0])
        ax.set_title(title)
        ax.set_xlabel("r_xy (um)")
        if index == 0:
            ax.set_ylabel("z_local (um)")
    axes[0, 0].legend(loc="lower left")
    cbar = fig.colorbar(image, ax=axes[0], fraction=0.018, pad=0.012)
    cbar.set_label("High-LET edep density\n(MeV / capture / um^3, log)")

    for index, (ax, (centers, line, title)) in enumerate(zip(axes[1], radials)):
        ax.plot(centers, line, color="#6338a6", linewidth=2)
        draw_cell_boundaries(ax, radial=True, labels=ax is axes[1, 0])
        ax.set_yscale("log")
        ax.set_ylim(radial_min, radial_max)
        ax.set_xlim(0, 5)
        ax.set_xlabel("r from cell center (um)")
        if index == 0:
            ax.set_ylabel("MeV / capture / um^3")
        ax.set_title(title)
        ax.grid(alpha=0.25, which="both")
    axes[1, 0].legend(fontsize=8)
    fig.suptitle("F3 Conditional high-LET single-cell response")
    fig.savefig(FIG_DIR / "F3_forced_capture_singlecell_distribution.png",
                dpi=180, bbox_inches="tight")
    plt.close(fig)


def therapy_data(target=1.0):
    data = []
    for name, label, color in THERAPY_INPUTS:
        paths = therapy_input_paths(name)
        rows = aggregate_cell_rows(paths)
        total_events = 0
        total_li7 = 0
        total_li7_weighted = 0.0
        b10_capture_bias = None
        for path in paths:
            run = validate_input(path, 0, expected_cells=4096)
            total_events += run["n_events"]
            path_bias = run.get("b10_capture_bias", 1.0)
            if b10_capture_bias is None:
                b10_capture_bias = path_bias
            elif not math.isclose(b10_capture_bias, path_bias):
                raise ValueError(f"{path.name}: cannot mix different B10 capture bias factors")
            frame = ROOT.RDataFrame("EventTree", str(path))
            total_li7 += int(frame.Sum("nLi7").GetValue())
            columns = {str(name) for name in frame.GetColumnNames()}
            if "nLi7Weighted" in columns:
                total_li7_weighted += float(frame.Sum("nLi7Weighted").GetValue())
            else:
                total_li7_weighted += float(frame.Sum("nLi7").GetValue())
        tumor = [row["dose_cell"] for row in rows if row["cell_type"] == 1]
        normal = [row["dose_cell"] for row in rows if row["cell_type"] == 0]
        raw_tumor = float(np.mean(tumor))
        raw_normal = float(np.mean(normal))
        scaled_tumor, scaled_normal, scale = scale_to_tumor_dose(raw_tumor, raw_normal, target)
        scaled_rows = [{**row, "dose_cell": row["dose_cell"] * scale} for row in rows]
        data.append({
            "name": name,
            "label": label,
            "color": color,
            "raw_tumor": raw_tumor,
            "raw_normal": raw_normal,
            "tumor": scaled_tumor,
            "normal": scaled_normal,
            "scale": scale,
            "selectivity": tumor_selectivity(scaled_tumor, scaled_normal),
            "columns": projected_columns(scaled_rows),
            "n_events": total_events,
            "n_li7": total_li7,
            "n_li7_weighted": total_li7_weighted,
            "b10_capture_bias": b10_capture_bias or 1.0,
        })
    return data


def therapy_input_paths(name):
    base = PROJECT_DIR / f"output_q2B_{name}_final.root"
    if not name.startswith("neutron_"):
        return [base]
    biased = PROJECT_DIR / f"output_q2B_{name}_biased_seed1.root"
    if biased.exists():
        return [biased]
    supplemental = sorted(PROJECT_DIR.glob(f"output_q2B_{name}_seed*.root"))
    return [base, *supplemental]


def aggregate_cell_rows(paths):
    combined = {}
    metadata = {"cell_id", "cell_type", "x_mm", "y_mm", "z_mm"}
    for path in paths:
        rows = read_cell_rows(path)
        if len(rows) != 4096:
            raise ValueError(f"{path.name}: CellTree must contain 4096 rows")
        for row in rows:
            cell_id = row["cell_id"]
            if cell_id not in combined:
                combined[cell_id] = dict(row)
                continue
            target = combined[cell_id]
            for key in metadata:
                if target[key] != row[key]:
                    raise ValueError(f"{path.name}: inconsistent {key} for cellID={cell_id}")
            for key, value in row.items():
                if key not in metadata:
                    target[key] = target.get(key, 0) + value
    return [combined[cell_id] for cell_id in sorted(combined)]


def plot_f4():
    data = therapy_data()
    positive = [column["dose"] for item in data for column in item["columns"] if column["dose"] > 0]
    vmax = max(positive)
    norm = LogNorm(vmin=max(min(positive), vmax * 1e-5), vmax=vmax)
    dose_cmap = projected_dose_colormap()

    fig = plt.figure(figsize=(17.0, 10.2), constrained_layout=True)
    grid = fig.add_gridspec(3, 4, height_ratios=[4.8, 1.45, 1.35], hspace=0.12, wspace=0.03)
    map_axes = [fig.add_subplot(grid[0, index]) for index in range(4)]
    dose_ax = fig.add_subplot(grid[1, :])
    selectivity_ax = fig.add_subplot(grid[2, :])
    image = None
    for ax, item in zip(map_axes, data):
        for cell_type, marker, edge_color, label in (
            (1, "o", "#f03b20", "Tumor cells"),
            (0, "s", "#00a65a", "Normal cells"),
        ):
            selected = [column for column in item["columns"] if column["cell_type"] == cell_type]
            image = ax.scatter(
                [column["x"] for column in selected],
                [column["z"] for column in selected],
                c=[column["dose"] for column in selected],
                s=54, cmap=dose_cmap, norm=norm, marker=marker,
                edgecolors=edge_color, linewidths=1.1, label=label,
            )
        ax.add_patch(Circle((0, 0), 150.0, fill=False, edgecolor="#4a67c8",
                            linestyle="--", linewidth=1.1, alpha=0.75))
        ax.set_title(item["label"])
        ax.set_aspect("equal")
        ax.set_xlim(-130, 130)
        ax.set_ylim(-130, 130)
        ax.grid(alpha=0.16)
        ax.set_xlabel("x relative to tumor center (um)")
        ax.text(
            0.04, 0.96,
            f"raw Dtumor={item['raw_tumor']:.3g} Gy\n"
            f"scale={item['scale']:.2f}x\n"
            f"N={item['n_events'] / 1e6:.1f}M, bias={item['b10_capture_bias']:.0f}x\n"
            f"{item['n_li7']} raw / {item['n_li7_weighted']:.2f} weighted Li7",
            transform=ax.transAxes, ha="left", va="top", fontsize=8,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white",
                  "edgecolor": "#777", "alpha": 0.82},
        )
    map_axes[0].set_ylabel("z relative to tumor center (um)")
    map_axes[-1].legend(loc="lower right", fontsize=8)
    fig.colorbar(image, ax=map_axes, label="Projected cell dose after Dtumor=1 Gy scaling (Gy, log)",
                 fraction=0.018, pad=0.012)

    labels = [item["label"] for item in data]
    colors = [item["color"] for item in data]
    x = np.arange(4)
    width = 0.34
    dose_ax.bar(x - width / 2, [item["tumor"] for item in data], width,
                color=colors, edgecolor="#222", label="Tumor cells")
    dose_ax.bar(x + width / 2, [item["normal"] for item in data], width,
                color=colors, edgecolor="#222", alpha=0.45, hatch="//", label="Normal cells")
    dose_ax.set_xticks(x)
    dose_ax.set_xticklabels(labels)
    dose_ax.set_yscale("log")
    dose_ax.set_ylabel("Mean dose (Gy)")
    dose_ax.set_title("Mean cell dose after equal-tumor-dose normalization")
    dose_ax.grid(axis="y", alpha=0.25)
    dose_ax.legend(ncol=2, fontsize=8)

    selectivity = [item["selectivity"] for item in data]
    selectivity_ax.bar(labels, selectivity, color=colors, width=0.62)
    selectivity_ax.set_ylim(0, 1.05)
    selectivity_ax.set_ylabel("Dtumor / total")
    selectivity_ax.set_title("Tumor selectivity")
    selectivity_ax.grid(axis="y", alpha=0.25)
    for index, value in enumerate(selectivity):
        selectivity_ax.text(index, value + 0.025, f"{value:.3f}", ha="center", va="bottom")

    fig.suptitle(
        "F4 Exploratory real-beam comparison at equal mean tumor-cell dose (1 Gy)\n"
        "BNCT occurrence-bias estimator is not analog-validated"
    )
    fig.savefig(FIG_DIR / "F4_therapy_comparison_projected_maps.png", dpi=180)
    plt.close(fig)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", choices=("all", "f1", "f2", "f3", "f4"), default="all")
    return parser.parse_args()


def main():
    if ROOT is None:
        raise RuntimeError("PyROOT is required for Q2 final figures")
    apply_readable_style()
    section = parse_args().section
    actions = {"f1": plot_f1, "f2": plot_f2, "f3": plot_f3, "f4": plot_f4}
    for name, action in actions.items():
        if section in ("all", name):
            action()


if __name__ == "__main__":
    main()
