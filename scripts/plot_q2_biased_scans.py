#!/usr/bin/env python3
"""Plot weighted beam-based Q2 concentration and tumor-depth experiments."""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig-g4sim")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_DIR / "figures_final"
FIG_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from plot_assignment_results import (  # noqa: E402
    ROOT,
    projected_columns,
    read_cell_rows,
    read_run_row,
)


PPM_LIST = (30000, 100000, 200000, 300000)
MODES = ("uniform", "shell")
MODE_COLORS = {"uniform": "#3465a4", "shell": "#c17d11"}
DEPTH_Y_MM = (-110, -95, -80, -65, -50)
DEPTH_MM = tuple(y + 120 for y in DEPTH_Y_MM)


def ppm_path(mode, ppm):
    return PROJECT_DIR / f"output_q2C_biased_{mode}_{ppm}ppm.root"


def depth_path(y):
    return PROJECT_DIR / f"output_q2E_depth_ym{abs(y)}_analog.root"


def validate_beam(path, expect_biased):
    if not path.exists():
        raise FileNotFoundError(path)
    run = read_run_row(path)
    if run.get("source_mode") != 0:
        raise ValueError(f"{path.name}: expected beam sourceMode")
    if expect_biased and run.get("b10_capture_bias", 1.0) <= 1.0:
        raise ValueError(f"{path.name}: expected occurrence-biased neutron run")
    if not expect_biased and run.get("b10_capture_bias", 1.0) != 1.0:
        raise ValueError(f"{path.name}: expected analog neutron run")
    return run


def mean_cell_dose(rows, cell_type, histories):
    values = [row["dose_cell"] for row in rows if row["cell_type"] == cell_type]
    return float(np.mean(values)) / histories if values else 0.0


def summarize(path, expect_biased=True):
    run = validate_beam(path, expect_biased)
    histories = run["n_events"]
    frame = ROOT.RDataFrame("EventTree", str(path))
    entries = int(frame.Count().GetValue())
    if entries != histories:
        raise ValueError(f"{path.name}: EventTree has {entries} rows, expected {histories}")
    weighted_li7 = float(frame.Sum("nLi7Weighted").GetValue())
    raw_li7 = float(frame.Sum("nLi7").GetValue())
    reached = float(frame.Sum("primaryNeutronReachedTumor").GetValue())
    tumor_edep_events = int(frame.Filter("edepTumorRegion_MeV > 0").Count().GetValue())
    tumor_region_edep = float(frame.Sum("edepTumorRegion_MeV").GetValue()) / histories
    tumor_region_dose = float(frame.Sum("doseTumorRegion_Gy").GetValue()) / histories
    rows = read_cell_rows(path)
    tumor = mean_cell_dose(rows, 1, histories)
    normal = mean_cell_dose(rows, 0, histories)
    return {
        "path": path,
        "histories": histories,
        "bias": run["b10_capture_bias"],
        "weighted_li7_per_neutron": weighted_li7 / histories,
        "raw_li7": raw_li7,
        "reach_fraction": reached / histories,
        "tumor_edep_event_fraction": tumor_edep_events / histories,
        "tumor_region_edep_per_neutron": tumor_region_edep,
        "tumor_region_dose_per_neutron": tumor_region_dose,
        "tumor_dose_per_neutron": tumor,
        "normal_dose_per_neutron": normal,
        "selectivity": tumor / (tumor + normal) if tumor + normal > 0 else 0.0,
        "columns": projected_columns(rows),
    }


def style():
    plt.rcParams.update({
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 15,
    })


def plot_ppm_scan(data):
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.5))
    for mode in MODES:
        rows = data[mode]
        x = np.asarray(PPM_LIST) / 1000.0
        color = MODE_COLORS[mode]
        axes[0, 0].plot(x, [r["weighted_li7_per_neutron"] for r in rows], "o-",
                        color=color, label=mode)
        axes[0, 1].plot(x, [r["tumor_dose_per_neutron"] for r in rows], "o-",
                        color=color, label=f"{mode}: tumor")
        axes[0, 1].plot(x, [r["normal_dose_per_neutron"] for r in rows], "s--",
                        color=color, alpha=0.65, label=f"{mode}: normal")
        axes[1, 0].plot(x, [r["selectivity"] for r in rows], "o-", color=color, label=mode)
        axes[1, 1].plot(x, [r["raw_li7"] for r in rows], "o-", color=color, label=mode)

    axes[0, 0].set_ylabel("Weighted Li7 yield / incident neutron")
    axes[0, 0].set_title("(a) Weight-scored Li7-yield estimator")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_ylabel("Mean cell dose / incident neutron (Gy)")
    axes[0, 1].set_title("(b) Weight-scored mean cell dose")
    axes[1, 0].set_ylim(0, 1.02)
    axes[1, 0].set_ylabel(r"$D_\mathrm{tumor}/(D_\mathrm{tumor}+D_\mathrm{normal})$")
    axes[1, 0].set_title("(c) Tumor selectivity")
    axes[1, 1].set_ylabel("Raw simulated Li7 count")
    axes[1, 1].set_title("(d) Biased-run effective statistics")
    for ax in axes.flat:
        ax.set_xlabel("Uniform-equivalent total B10 concentration (10³ ppm)")
        ax.grid(alpha=0.25)
        ax.legend()
    fig.suptitle("Exploratory B10 concentration scan: weight-scored estimator (not analog-validated)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_DIR / "Q2_biased_ppm_scan.png", dpi=200)
    plt.close(fig)


def positive_limits(groups):
    values = [column["dose"] / row["histories"]
              for group in groups for row in group for column in row["columns"]
              if column["dose"] > 0]
    if not values:
        raise ValueError("projected maps contain no positive dose")
    return max(min(values), np.percentile(values, 3)), max(values)


def draw_projected(ax, summary, norm, title):
    columns = summary["columns"]
    dose = np.asarray([c["dose"] / summary["histories"] for c in columns])
    scatter = ax.scatter(
        [c["x"] for c in columns], [c["z"] for c in columns], c=dose,
        s=28, marker="s", cmap="inferno", norm=norm,
        edgecolors=["#ff6b5f" if c["cell_type"] == 1 else "#50d890" for c in columns],
        linewidths=0.35,
    )
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlabel("Cell-column x (um)")
    ax.set_ylabel("Cell-column z (um)")
    ax.set_facecolor("black")
    return scatter


def add_cell_type_legend(ax):
    handles = [
        Line2D([], [], marker="o", linestyle="", markerfacecolor="black",
               markeredgecolor="#ff6b5f", label="tumor column"),
        Line2D([], [], marker="s", linestyle="", markerfacecolor="black",
               markeredgecolor="#50d890", label="normal column"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.75)


def plot_ppm_maps(data):
    groups = [data[mode] for mode in MODES]
    vmin, vmax = positive_limits(groups)
    norm = LogNorm(vmin=vmin, vmax=vmax)
    fig, axes = plt.subplots(2, 4, figsize=(15.5, 7.2), constrained_layout=True)
    scatter = None
    for row_index, mode in enumerate(MODES):
        for col_index, ppm in enumerate(PPM_LIST):
            summary = data[mode][col_index]
            scatter = draw_projected(
                axes[row_index, col_index], summary, norm,
                f"{mode}, {ppm // 1000}k ppm\nraw Li7={summary['raw_li7']:.0f}",
            )
    add_cell_type_legend(axes[0, 0])
    fig.colorbar(scatter, ax=axes, label="Weight-scored projected cell dose / incident neutron (Gy)")
    fig.suptitle("Exploratory cell-stacked maps from occurrence-biased scan (not analog-validated)")
    fig.savefig(FIG_DIR / "Q2_biased_ppm_projected_maps.png", dpi=200)
    plt.close(fig)


def plot_depth_scan(data):
    x = np.asarray(DEPTH_MM)
    tumor_dose = np.asarray([r["tumor_region_dose_per_neutron"] for r in data])
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.5))
    axes[0, 0].plot(x, [r["reach_fraction"] for r in data], "o-", color="#3465a4")
    axes[0, 0].set_ylabel("Primary-neutron tumor-region reach fraction")
    axes[0, 0].set_title("(a) Neutron delivery to tumor region")
    axes[0, 1].plot(x, [r["tumor_edep_event_fraction"] for r in data], "o-", color="#75507b")
    axes[0, 1].set_ylabel("Fraction with tumor-region energy deposition")
    axes[0, 1].set_title("(b) Events depositing energy in tumor region")
    axes[1, 0].plot(x, [r["tumor_region_edep_per_neutron"] for r in data], "o-", color="#c17d11")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_ylabel("Tumor-region edep / incident neutron (MeV)")
    axes[1, 0].set_title("(c) Analog tumor-region energy deposition")
    axes[1, 1].plot(x, tumor_dose / tumor_dose[0], "o-", label="tumor-region dose", color="#c17d11")
    axes[1, 1].plot(x, np.asarray([r["reach_fraction"] for r in data]) /
                    data[0]["reach_fraction"], "s--", label="reach fraction", color="#3465a4")
    axes[1, 1].axhline(1.0, color="#555", linewidth=1)
    axes[1, 1].set_ylabel("Value normalized to 10 mm depth")
    axes[1, 1].set_title("(d) Relative attenuation with depth")
    axes[1, 1].legend()
    for ax in axes.flat:
        ax.set_xlabel("Water-equivalent depth to tumor proximal face (mm)")
        ax.grid(alpha=0.25)
    fig.suptitle("Tumor-depth scan: analog neutron transport")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_DIR / "Q2_tumor_depth_scan.png", dpi=200)
    plt.close(fig)


def plot_depth_maps(data):
    vmax = max(column["dose"] for summary in data for column in summary["columns"])
    if vmax <= 0:
        raise ValueError("depth cell-column maps contain no positive dose")
    norm = Normalize(vmin=0.0, vmax=vmax)
    fig, axes = plt.subplots(
        1, 5, figsize=(18.5, 4.6), sharex=True, sharey=True, constrained_layout=True,
    )
    image = None
    for ax, depth, summary in zip(axes, DEPTH_MM, data):
        columns = summary["columns"]
        positive_columns = sum(column["dose"] > 0 for column in columns)
        ax.set_facecolor("black")
        for cell_type, marker, edge_color in (
            (1, "o", "#f03b20"),
            (0, "s", "#00a65a"),
        ):
            selected = [column for column in columns if column["cell_type"] == cell_type]
            image = ax.scatter(
                [column["x"] for column in selected],
                [column["z"] for column in selected],
                c=[column["dose"] for column in selected],
                s=54,
                cmap="inferno",
                norm=norm,
                marker=marker,
                edgecolors=edge_color,
                linewidths=1.0,
            )
        ax.add_patch(Circle((0, 0), 150.0, fill=False, edgecolor="#4a67c8",
                            linestyle="--", linewidth=1.0, alpha=0.75))
        ax.set_title(f"Depth {depth} mm\npositive columns = {positive_columns}")
        ax.set_aspect("equal")
        ax.set_xlim(-125, 125)
        ax.set_ylim(-125, 125)
        ax.set_xlabel("Cell-column x (um)")
        ax.grid(alpha=0.12)
    axes[0].set_ylabel("Cell-column z (um)")
    add_cell_type_legend(axes[-1])
    fig.colorbar(image, ax=axes, label="Projected cell-column dose summed over y (Gy)")
    fig.suptitle("Cell-stacked projected dose maps versus tumor depth (200k analog neutrons per point)")
    fig.savefig(FIG_DIR / "Q2_tumor_depth_projected_maps.png", dpi=200)
    plt.close(fig)


def main():
    if ROOT is None:
        raise RuntimeError("PyROOT is required")
    style()
    ppm_data = {mode: [summarize(ppm_path(mode, ppm)) for ppm in PPM_LIST] for mode in MODES}
    depth_data = [summarize(depth_path(y), expect_biased=False) for y in DEPTH_Y_MM]
    plot_ppm_scan(ppm_data)
    plot_ppm_maps(ppm_data)
    plot_depth_scan(depth_data)
    plot_depth_maps(depth_data)
    for group in (*ppm_data.values(), depth_data):
        for row in group:
            print(
                f"{row['path'].name}: rawLi7={row['raw_li7']:.0f}, "
                f"weightedLi7/n={row['weighted_li7_per_neutron']:.6g}, "
                f"reach={row['reach_fraction']:.6g}, tumorDose/n={row['tumor_dose_per_neutron']:.6g}"
            )


if __name__ == "__main__":
    main()
