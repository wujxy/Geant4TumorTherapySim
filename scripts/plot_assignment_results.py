#!/usr/bin/env python3
import argparse
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig-g4sim")
DEFAULT_ROOT_DIR = Path("/home/NagaiYoru/packages/root")
if DEFAULT_ROOT_DIR.exists():
    os.environ.setdefault("ROOTSYS", str(DEFAULT_ROOT_DIR))
    root_bin = str(DEFAULT_ROOT_DIR / "bin")
    root_lib = str(DEFAULT_ROOT_DIR / "lib")
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if root_bin not in path_entries:
        os.environ["PATH"] = root_bin + os.pathsep + os.environ.get("PATH", "")
    python_entries = os.environ.get("PYTHONPATH", "").split(os.pathsep)
    if root_lib not in python_entries:
        os.environ["PYTHONPATH"] = root_lib + os.pathsep + os.environ.get("PYTHONPATH", "")
    library_entries = os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
    if root_lib not in library_entries:
        os.environ["LD_LIBRARY_PATH"] = root_lib + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
    if root_lib not in sys.path:
        sys.path.insert(0, root_lib)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Circle, Rectangle
import numpy as np

try:
    import ROOT
    ROOT.gROOT.SetBatch(True)
except Exception:
    ROOT = None


PROJECT_DIR = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

ROOT_FILES = {
    "gamma": PROJECT_DIR / "output_problem1_gamma.root",
    "proton": PROJECT_DIR / "output_problem1_proton.root",
    "q2_gamma": PROJECT_DIR / "output_problem2_gamma.root",
    "q2_proton": PROJECT_DIR / "output_problem2_proton.root",
    "bnct_uniform": PROJECT_DIR / "output_problem2_bnct_uniform.root",
    "bnct_shell": PROJECT_DIR / "output_problem2_bnct_shell.root",
}

PROTON_SCAN_ENERGIES = [60, 65, 70, 75, 80, 85, 90, 95, 100]
GAMMA_SCAN_ENERGIES = [0.2, 0.5, 1, 2, 4, 6, 8, 10, 15]
SCAN_ENERGIES = PROTON_SCAN_ENERGIES
B10_SCAN_PPM = [1000, 3000, 10000, 30000, 100000, 300000, 500000]
Q2_BORON_MODES = ["uniform", "shell"]
Q2_THERAPY_COMPARISON_CASES = [
    ("gamma", "Gamma 1 MeV", "q2_gamma", "#2f6db3"),
    ("proton", "Proton 80 MeV", "q2_proton", "#c83f31"),
    ("bnct_uniform", "BNCT uniform", "bnct_uniform", "#7b519d"),
    ("bnct_shell", "BNCT shell", "bnct_shell", "#d38b2f"),
]
NEUTRON_FLUENCE_EVENTS = [2000, 5000, 10000, 20000, 50000, 100000, 200000]
NEUTRON_FLUENCE_MAP_EVENTS = [5000, 20000, 100000, 200000]
LET_PLOT_XMAX = 2.0
LET_HISTOGRAM_BINS = 200


def energy_tag(energy):
    text = f"{energy:g}"
    return f"{text.replace('.', 'p')}MeV"


def scan_root_path(particle, energy):
    return PROJECT_DIR / f"output_problem1_{particle}_{energy_tag(energy)}.root"


def b10_scan_root_path(mode, ppm):
    return PROJECT_DIR / f"output_problem2_bnct_{mode}_{int(ppm)}ppm.root"


def neutron_fluence_root_path(mode, events):
    return PROJECT_DIR / f"output_problem2_bnct_{mode}_fluence_{int(events)}events.root"


def therapy_comparison_root_path(case_name):
    return PROJECT_DIR / f"output_problem2_{case_name}.root"


def existing_root_outputs():
    paths = list(ROOT_FILES.values())
    paths.extend(scan_root_path("proton", energy) for energy in PROTON_SCAN_ENERGIES)
    paths.extend(scan_root_path("gamma", energy) for energy in GAMMA_SCAN_ENERGIES)
    for mode in Q2_BORON_MODES:
        paths.extend(b10_scan_root_path(mode, ppm) for ppm in B10_SCAN_PPM)
        paths.extend(neutron_fluence_root_path(mode, events) for events in NEUTRON_FLUENCE_EVENTS)
    return [path for path in paths if path.exists()]


def require_root_when_outputs_exist():
    if ROOT is None and existing_root_outputs():
        raise RuntimeError(
            "PyROOT is unavailable while ROOT output files exist. "
            "Run scripts/run_assignment_workflow.sh, or export ROOTSYS, PYTHONPATH, "
            "and LD_LIBRARY_PATH before plotting."
        )


def open_root(path):
    if ROOT is None or not path.exists():
        return None
    handle = ROOT.TFile.Open(str(path))
    if not handle or handle.IsZombie():
        return None
    return handle


def read_h1(path, hist_name):
    handle = open_root(path)
    if handle is None:
        return None
    hist = handle.Get(hist_name)
    if not hist:
        handle.Close()
        return None
    xs, ys = [], []
    axis = hist.GetXaxis()
    for index in range(1, hist.GetNbinsX() + 1):
        xs.append(axis.GetBinCenter(index))
        ys.append(hist.GetBinContent(index))
    handle.Close()
    return xs, ys


def read_h3_xy(path, hist_name):
    handle = open_root(path)
    if handle is None:
        return None
    hist = handle.Get(hist_name)
    if not hist:
        handle.Close()
        return None
    xaxis = hist.GetXaxis()
    yaxis = hist.GetYaxis()
    xs = [xaxis.GetBinCenter(i) for i in range(1, hist.GetNbinsX() + 1)]
    ys = [yaxis.GetBinCenter(i) for i in range(1, hist.GetNbinsY() + 1)]
    grid = []
    for iy in range(1, hist.GetNbinsY() + 1):
        row = []
        for ix in range(1, hist.GetNbinsX() + 1):
            total = 0.0
            for iz in range(1, hist.GetNbinsZ() + 1):
                total += hist.GetBinContent(ix, iy, iz)
            row.append(total)
        grid.append(row)
    handle.Close()
    return xs, ys, grid


def read_event_rows(path):
    handle = open_root(path)
    if handle is None:
        return []
    tree = handle.Get("EventTree")
    if not tree:
        handle.Close()
        return []
    rows = []
    for entry in tree:
        row = {
            "dose_tumor": float(entry.doseTumorRegion_Gy),
            "dose_normal": float(entry.doseNormalRegion_Gy),
            "edep_tumor": float(entry.edepTumorRegion_MeV),
            "edep_normal": float(entry.edepNormalRegion_MeV),
            "n_alpha": int(entry.nAlpha),
            "n_li7": int(entry.nLi7),
            "n_gamma": int(entry.nGamma),
            "n_electron": int(entry.nElectron),
        }
        for opt in (
            "edepNucleusTumorGamma_MeV",
            "edepNucleusTumorProton_MeV",
            "edepNucleusTumorAlpha_MeV",
            "edepNucleusTumorLi7_MeV",
            "edepNucleusNormalGamma_MeV",
            "edepNucleusNormalProton_MeV",
            "edepNucleusNormalAlpha_MeV",
            "edepNucleusNormalLi7_MeV",
            "forcedCaptureBranch",
            "forcedCaptureRadius_um",
            "forcedInitialHighLET_MeV",
        ):
            if hasattr(entry, opt):
                row[opt] = int(getattr(entry, opt)) if opt == "forcedCaptureBranch" else float(getattr(entry, opt))
        rows.append(row)
    handle.Close()
    return rows


def read_run_row(path):
    handle = open_root(path)
    if handle is None:
        return {}
    tree = handle.Get("RunTree")
    if not tree or tree.GetEntries() == 0:
        handle.Close()
        return {}
    tree.GetEntry(0)
    row = {
        "mode": int(tree.mode),
        "boron_mode": int(tree.boronMode),
        "n_events": int(tree.nEvents),
        "source_mode": int(tree.sourceMode) if hasattr(tree, "sourceMode") else 0,
        "b10_capture_bias": float(tree.b10CaptureBias) if hasattr(tree, "b10CaptureBias") else 1.0,
    }
    handle.Close()
    return row


def read_cell_rows(path):
    handle = open_root(path)
    if handle is None:
        return []
    tree = handle.Get("CellTree")
    if not tree:
        handle.Close()
        return []
    rows = []
    for entry in tree:
        row = {
            "cell_id": int(entry.cellID),
            "cell_type": int(entry.cellType),
            "x_mm": float(entry.x_mm),
            "y_mm": float(entry.y_mm),
            "z_mm": float(entry.z_mm),
            "dose_cell": float(entry.doseCell_Gy),
            "dose_nucleus": float(entry.doseNucleus_Gy),
            "dose_boron": float(entry.doseBoronRegion_Gy),
            "alpha_hits": int(entry.alphaHits),
            "li_hits": int(entry.liHits),
        }
        # New columns added in the Q2 re-design (per-particle nucleus edep + in-nucleus hits)
        for opt in (
            "edepNucleusGamma_MeV",
            "edepNucleusProton_MeV",
            "edepNucleusAlpha_MeV",
            "edepNucleusLi7_MeV",
            "alphaNucleusHits",
            "liNucleusHits",
            "edepNucleus_MeV",
        ):
            if hasattr(entry, opt):
                row[opt] = float(getattr(entry, opt)) if not opt.endswith("Hits") else int(getattr(entry, opt))
        rows.append(row)
    handle.Close()
    return rows


def read_h2(path, hist_name):
    """Return (x_edges, y_edges, grid[ny][nx]) for a 2D histogram.

    Edges are bin lower edges plus the upper edge of the last bin so they can
    be passed straight to pcolormesh. Grid is in (row=y, col=x) order to match
    matplotlib's imshow / pcolormesh convention.
    """
    handle = open_root(path)
    if handle is None:
        return None
    hist = handle.Get(hist_name)
    if not hist:
        handle.Close()
        return None
    xaxis = hist.GetXaxis()
    yaxis = hist.GetYaxis()
    nx = hist.GetNbinsX()
    ny = hist.GetNbinsY()
    x_edges = [xaxis.GetBinLowEdge(i) for i in range(1, nx + 1)] + [xaxis.GetBinUpEdge(nx)]
    y_edges = [yaxis.GetBinLowEdge(i) for i in range(1, ny + 1)] + [yaxis.GetBinUpEdge(ny)]
    grid = []
    for iy in range(1, ny + 1):
        row = [hist.GetBinContent(ix, iy) for ix in range(1, nx + 1)]
        grid.append(row)
    handle.Close()
    return x_edges, y_edges, grid


# === Q2 BNCT survival / kill rate (LQ + RBE) =========================
# Parameters per the experiment-design doc (see docs/q2_timing_benchmark.md).
RBE_GAMMA = 1.0       # γ/e- low-LET reference
RBE_PROTON = 1.1      # standard clinical proton RBE
RBE_HIGHLET_TUMOR = 1.3   # α/Li7 in tumor cells
RBE_HIGHLET_NORMAL = 3.0  # α/Li7 in normal cells (more sensitive to high-LET)
LQ_ALPHA_TUMOR = 0.3   # Gy^-1, tumor cell α coefficient (α/β = 10)
LQ_BETA_TUMOR = 0.03   # Gy^-2
LQ_ALPHA_NORMAL = 0.1  # Gy^-1, normal cell α (α/β = 3)
LQ_BETA_NORMAL = 0.033 # Gy^-2


def equiv_dose_gy(row, is_tumor):
    """LQ-equivalent dose to the nucleus using RBE-weighted per-particle channels.

    Falls back to plain doseNucleus_Gy when per-particle columns are missing
    (e.g. when reading pre-rewrite ROOT files).
    """
    if "edepNucleusAlpha_MeV" not in row:
        # Backwards-compat: lump everything into γ-equivalent.
        return row.get("dose_nucleus", 0.0)
    high = row.get("edepNucleusAlpha_MeV", 0.0) + row.get("edepNucleusLi7_MeV", 0.0)
    low_g = row.get("edepNucleusGamma_MeV", 0.0)
    low_p = row.get("edepNucleusProton_MeV", 0.0)
    total_nuc = row.get("edepNucleus_MeV", 0.0)
    if total_nuc <= 0:
        return 0.0
    # Convert MeV edep to Gy via the cell's recorded total nucleus dose
    # (dose_nucleus = edepNucleus / nucleusMass / gray, computed in G4 already).
    # We split it proportionally between channels then re-apply RBE.
    dose_total = row.get("dose_nucleus", 0.0)
    if dose_total <= 0:
        return 0.0
    frac_high = high / total_nuc
    frac_lowg = low_g / total_nuc
    frac_lowp = low_p / total_nuc
    rbe_high = RBE_HIGHLET_TUMOR if is_tumor else RBE_HIGHLET_NORMAL
    return dose_total * (frac_high * rbe_high + frac_lowg * RBE_GAMMA + frac_lowp * RBE_PROTON)


def survival_lq(dose_eq, is_tumor):
    a = LQ_ALPHA_TUMOR if is_tumor else LQ_ALPHA_NORMAL
    b = LQ_BETA_TUMOR if is_tumor else LQ_BETA_NORMAL
    return math.exp(-a * dose_eq - b * dose_eq * dose_eq)


def lethal_hit(row):
    """Geometric kill proxy: nucleus received >= 1 alpha or Li7 hit."""
    return (row.get("alphaNucleusHits", 0) + row.get("liNucleusHits", 0)) > 0


def cell_summary(rows):
    """Aggregate one CellTree's worth of cells into per-class metrics.

    Returns dict {tumor: {...}, normal: {...}}.
    """
    out = {}
    for label, ctype in (("tumor", 1), ("normal", 0)):
        sub = [r for r in rows if r["cell_type"] == ctype]
        n = len(sub)
        if n == 0:
            out[label] = {
                "n_cells": 0,
                "mean_dose_cell": 0.0,
                "mean_dose_nucleus": 0.0,
                "mean_dose_eq": 0.0,
                "mean_S": 1.0,
                "lethal_fraction": 0.0,
                "alpha_nuc_hits": 0,
                "li_nuc_hits": 0,
            }
            continue
        is_tumor = (ctype == 1)
        doses_cell = [r["dose_cell"] for r in sub]
        doses_nuc = [r["dose_nucleus"] for r in sub]
        doses_eq = [equiv_dose_gy(r, is_tumor) for r in sub]
        surv = [survival_lq(d, is_tumor) for d in doses_eq]
        leth = sum(1 for r in sub if lethal_hit(r))
        out[label] = {
            "n_cells": n,
            "mean_dose_cell": sum(doses_cell) / n,
            "mean_dose_nucleus": sum(doses_nuc) / n,
            "mean_dose_eq": sum(doses_eq) / n,
            "mean_S": sum(surv) / n,
            "lethal_fraction": leth / n,
            "alpha_nuc_hits": sum(int(r.get("alphaNucleusHits", 0)) for r in sub),
            "li_nuc_hits": sum(int(r.get("liNucleusHits", 0)) for r in sub),
        }
    return out


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def dose_localization_fraction(tumor_dose, normal_dose):
    total = tumor_dose + normal_dose
    return tumor_dose / total if total > 0 else 0.0


def normal_burden(tumor_dose, normal_dose):
    return normal_dose / tumor_dose if tumor_dose > 0 else 0.0


def normalize(values):
    vmax = max(values) if values else 0.0
    if vmax <= 0:
        return values
    return [v / vmax for v in values]


def normalize_grid(grid):
    vmax = max((max(row) for row in grid if row), default=0.0)
    if vmax <= 0:
        return grid
    return [[value / vmax for value in row] for row in grid]


def weighted_mean(xs, weights):
    total = sum(weights)
    if total <= 0:
        return 0.0
    return sum(x * weight for x, weight in zip(xs, weights)) / total


def histogram_weighted_mean(xs, counts):
    return weighted_mean(xs, counts)


def fallback_depth():
    depth = [x for x in range(-150, 151, 3)]
    gamma = [math.exp(-0.006 * (y + 130)) * (1.0 + 0.05 * math.sin(y / 9)) for y in depth]
    proton = [0.18 + 2.6 * math.exp(-0.5 * ((y + 73) / 8.0) ** 2) for y in depth]
    return depth, gamma, proton


def plot_q1_depth_dose():
    gamma_hist = read_h1(ROOT_FILES["gamma"], "hDepthDose")
    proton_hist = read_h1(ROOT_FILES["proton"], "hDepthDose")
    fallback = not gamma_hist or not proton_hist
    if fallback:
        x, gamma_y, proton_y = fallback_depth()
    else:
        x, gamma_y = gamma_hist
        _, proton_y = proton_hist

    gamma_norm = normalize(gamma_y)
    proton_norm = normalize(proton_y)

    fig, (source_ax, body_ax) = plt.subplots(
        1, 2, figsize=(10.5, 5.2), sharey=True,
        gridspec_kw={"width_ratios": [1.0, 3.2], "wspace": 0.06}
    )

    for ax in (source_ax, body_ax):
        ax.plot(x, gamma_norm, label="gamma 1 MeV", color="#2f6db3", linewidth=2)
        ax.plot(x, proton_norm, label="proton 85 MeV", color="#c83f31", linewidth=2)
        ax.grid(alpha=0.25)
        ax.set_ylim(-0.05, 1.05)

    source_ax.set_xlim(-620, -580)
    source_ax.axvspan(-620, -580, color="#d7ecff", alpha=0.38, label="air path")
    source_ax.axvline(-600, color="#333333", linestyle="--", linewidth=1.7, label="source")
    source_ax.annotate("source\n y=-600 mm",
                       xy=(-600, 0.86), xytext=(-616, 0.68),
                       arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.2},
                       fontsize=10, ha="left", va="center")
    source_ax.annotate("emission +y",
                       xy=(-586, 0.12), xytext=(-615, 0.12),
                       arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.8},
                       fontsize=10, ha="left", va="center")
    source_ax.set_xlabel("Source region y (mm)")
    source_ax.set_ylabel("Normalized energy deposit")

    body_ax.set_xlim(-150, 150)
    body_ax.axvspan(-150, -130, color="#d7ecff", alpha=0.32, label="air range")
    body_ax.axvspan(-130, 130, color="#e8e8e8", alpha=0.28, label="human range")
    body_ax.axvspan(130, 150, color="#d7ecff", alpha=0.32)
    body_ax.axvspan(-90, -70, color="#c83f31", alpha=0.12, label="tumor y-span")
    body_ax.set_xlabel("Human/tumor region y (mm)")
    body_ax.legend(loc="upper right")

    source_ax.spines["right"].set_visible(False)
    body_ax.spines["left"].set_visible(False)
    body_ax.tick_params(labelleft=False)
    break_kwargs = {"marker": [(-1, -1), (1, 1)], "markersize": 9,
                    "linestyle": "none", "color": "k", "mec": "k", "mew": 1.2, "clip_on": False}
    source_ax.plot([1, 1], [0, 1], transform=source_ax.transAxes, **break_kwargs)
    body_ax.plot([0, 0], [0, 1], transform=body_ax.transAxes, **break_kwargs)

    fig.suptitle("Q1 Depth-dose comparison with omitted air path" + (" (reference fallback)" if fallback else ""))
    fig.text(0.41, 0.03, "Air path between y=-580 mm and y=-150 mm is omitted; deposition there is negligible.",
             ha="center", fontsize=9, color="#444444")
    fig.subplots_adjust(bottom=0.17, top=0.88)
    fig.savefig(FIG_DIR / "Q1_depth_dose.png", dpi=180)
    plt.close(fig)


def plot_q1_dose_heatmap():
    maps = [
        ("gamma 1 MeV", ROOT_FILES["gamma"]),
        ("proton 85 MeV", ROOT_FILES["proton"]),
    ]
    panels = []
    fallback = False
    for label, path in maps:
        heatmap = read_h3_xy(path, "hVoxelDose3D")
        if heatmap is None:
            fallback = True
            xs = [x for x in range(-80, 81, 4)]
            ys = [y for y in range(-150, 151, 4)]
            grid = []
            for y in ys:
                row = []
                for x in xs:
                    beam = math.exp(-0.5 * (x / 7.5) ** 2)
                    if "proton" in label:
                        depth = 0.2 + 2.3 * math.exp(-0.5 * ((y + 73) / 5.0) ** 2)
                    else:
                        depth = math.exp(-0.006 * (y + 130))
                    row.append(beam * depth)
                grid.append(row)
        else:
            xs, ys, grid = heatmap
        panels.append((label, xs, ys, normalize_grid(grid)))

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.9), sharex=True, sharey=True, constrained_layout=True)
    image = None
    for ax, (label, xs, ys, grid) in zip(axes, panels):
        extent = [min(xs), max(xs), min(ys), max(ys)]
        image = ax.imshow(grid, extent=extent, origin="lower", aspect="auto", cmap="inferno", vmin=0, vmax=1)
        ax.add_patch(Rectangle((-60, -130), 120, 260, fill=False, edgecolor="white",
                               linestyle="--", linewidth=1.8, label="Human torso"))
        ax.add_patch(Rectangle((-5, -90), 10, 20, fill=False, edgecolor="#5dd3ff", linewidth=2, label="Tumor"))
        ax.annotate("", xy=(0, -130), xytext=(0, -150),
                    arrowprops={"arrowstyle": "->", "color": "white", "lw": 1.8})
        ax.text(4, -147, "+y beam", color="white", fontsize=9, va="bottom")
        ax.set_title(label)
        ax.set_xlabel("x (mm)")
        ax.grid(alpha=0.12, color="white")

    axes[0].set_ylabel("Depth y (mm)")
    axes[1].legend(loc="upper right")
    fig.suptitle("Q1 2D dose-map comparison" + (" (reference fallback)" if fallback else ""))
    fig.colorbar(image, ax=axes, label="Normalized energy deposit", fraction=0.035, pad=0.02)
    fig.savefig(FIG_DIR / "Q1_dose_heatmap.png", dpi=180)
    plt.close(fig)


def fallback_scan_heatmap(particle, energy):
    xs = [x for x in range(-140, 141, 6)]
    ys = [y for y in range(-140, 141, 4)]
    grid = []
    for y in ys:
        row = []
        for x in xs:
            beam = math.exp(-0.5 * (x / 7.5) ** 2)
            if particle == "proton":
                peak = -130 + 0.64 * energy
                depth = 0.15 + 2.3 * math.exp(-0.5 * ((y - peak) / 5.0) ** 2)
            else:
                attenuation = 0.008 / max(math.sqrt(energy), 0.45)
                traversed = max(y + 130, 0.0)
                buildup = 1.0 - math.exp(-0.12 * traversed)
                depth = (0.35 + buildup) * math.exp(-attenuation * traversed)
            row.append(beam * depth)
        grid.append(row)
    return xs, ys, grid


def plot_q1_particle_energy_heatmap_grid(particle, energies, title, output_name):
    fig, axes = plt.subplots(3, 3, figsize=(12.5, 10.2), sharex=True, sharey=True, constrained_layout=True)
    image = None
    fallback = False

    for ax, energy in zip(axes.flat, energies):
        path = scan_root_path(particle, energy)
        heatmap = read_h3_xy(path, "hVoxelDose3D")
        if heatmap is None:
            fallback = True
            xs, ys, grid = fallback_scan_heatmap(particle, energy)
        else:
            xs, ys, grid = heatmap

        extent = [min(xs), max(xs), min(ys), max(ys)]
        image = ax.imshow(normalize_grid(grid), extent=extent, origin="lower", aspect="auto",
                          cmap="inferno", vmin=0, vmax=1)
        ax.add_patch(Rectangle((-60, -130), 120, 260, fill=False, edgecolor="white",
                               linestyle="--", linewidth=1.2))
        ax.add_patch(Rectangle((-5, -90), 10, 20, fill=False, edgecolor="#5dd3ff", linewidth=1.8))
        ax.annotate("", xy=(0, -130), xytext=(0, -150),
                    arrowprops={"arrowstyle": "->", "color": "white", "lw": 1.2})
        ax.set_title(f"{energy:g} MeV")
        ax.grid(alpha=0.10, color="white")

    for ax in axes[-1, :]:
        ax.set_xlabel("x (mm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Depth y (mm)")

    axes[0, 2].plot([], [], color="white", linestyle="--", label="Human torso")
    axes[0, 2].plot([], [], color="#5dd3ff", label="Tumor")
    axes[0, 2].legend(loc="upper right", fontsize=8)
    fig.suptitle(title + (" (reference fallback)" if fallback else ""))
    fig.colorbar(image, ax=axes, label="Normalized energy deposit", fraction=0.025, pad=0.02)
    fig.savefig(FIG_DIR / output_name, dpi=180)
    plt.close(fig)


def plot_q1_proton_energy_heatmap_grid():
    plot_q1_particle_energy_heatmap_grid(
        "proton",
        PROTON_SCAN_ENERGIES,
        "Q1 Proton dose-map scan by energy",
        "Q1_proton_energy_heatmap_grid.png",
    )


def plot_q1_gamma_energy_heatmap_grid():
    plot_q1_particle_energy_heatmap_grid(
        "gamma",
        GAMMA_SCAN_ENERGIES,
        "Q1 Gamma dose-map scan by energy",
        "Q1_gamma_energy_heatmap_grid.png",
    )


def plot_q1_particle_energy_scan(particle, energies_arg, title, output_name, line_color, normal_color, x_label):
    energies = []
    tumor_dose = []
    normal_dose = []
    selectivity = []
    tumor_edep = []
    normal_edep = []
    depth_metric = []

    for energy in energies_arg:
        path = scan_root_path(particle, energy)
        rows = read_event_rows(path)
        hist = read_h1(path, "hDepthDose")
        if not rows or not hist:
            continue
        tumor = mean(r["dose_tumor"] for r in rows)
        normal = mean(r["dose_normal"] for r in rows)
        tumor_e = mean(r["edep_tumor"] for r in rows)
        normal_e = mean(r["edep_normal"] for r in rows)
        xs, ys = hist
        peak_index = max(range(len(ys)), key=lambda i: ys[i]) if ys else 0
        energies.append(energy)
        tumor_dose.append(tumor)
        normal_dose.append(normal)
        tumor_edep.append(tumor_e)
        normal_edep.append(normal_e)
        selectivity.append(tumor_e / (tumor_e + normal_e) if (tumor_e + normal_e) > 0 else 0.0)
        if particle == "gamma":
            depth_metric.append(weighted_mean(xs, ys))
        else:
            depth_metric.append(xs[peak_index])

    fallback = not energies
    if fallback:
        energies = list(energies_arg)
        if particle == "proton":
            tumor_dose = [math.exp(-0.5 * ((e - 80) / 10) ** 2) for e in energies]
            normal_dose = [0.15 + 0.015 * e for e in energies]
            depth_metric = [-130 + 0.64 * e for e in energies]
        else:
            tumor_dose = [0.18 + 0.06 * math.log1p(e) for e in energies]
            normal_dose = [0.22 + 0.09 * math.log1p(e) for e in energies]
            depth_metric = [-35 + 7.0 * math.log1p(e) for e in energies]
        tumor_edep = tumor_dose
        normal_edep = normal_dose
        selectivity = [t / (t + n) if (t + n) > 0 else 0.0 for t, n in zip(tumor_edep, normal_edep)]

    fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    tumor_plot = [max(value, 1.e-16) for value in tumor_dose]
    normal_plot = [max(value, 1.e-16) for value in normal_dose]
    axes[0].plot(energies, tumor_plot, marker="o", label="Tumor region", color=line_color, linewidth=2)
    axes[0].plot(energies, normal_plot, marker="s", label="Whole normal tissue", color=normal_color, linewidth=2)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Mean event dose (Gy)")
    axes[0].set_title(title + (" (reference fallback)" if fallback else ""))
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].plot(energies, selectivity, marker="o", label="Tumor deposited-energy fraction", color="#3949ab", linewidth=2)
    axes[1].set_ylabel("E_tumor / (E_tumor + E_normal)")
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].set_xlabel(x_label)
    axes[1].grid(alpha=0.25)
    twin = axes[1].twinx()
    depth_label = "Energy-deposition-weighted mean y" if particle == "gamma" else "Depth-dose peak y"
    twin.plot(energies, depth_metric, marker="^", label=depth_label, color="#d38b2f", linewidth=2)
    twin.axhspan(-90, -70, color="#c83f31", alpha=0.12, label="Tumor y-span")
    twin.set_ylabel(f"{depth_label} (mm)")

    lines, labels = axes[1].get_legend_handles_labels()
    lines2, labels2 = twin.get_legend_handles_labels()
    axes[1].legend(lines + lines2, labels + labels2, loc="best")
    if particle == "gamma":
        axes[0].set_xscale("log")
        axes[1].set_xscale("log")
        axes[1].set_xticks(energies)
        axes[1].set_xticklabels([f"{e:g}" for e in energies])
    fig.tight_layout()
    fig.savefig(FIG_DIR / output_name, dpi=180)
    plt.close(fig)


def plot_q1_proton_energy_scan():
    plot_q1_particle_energy_scan(
        "proton",
        PROTON_SCAN_ENERGIES,
        "Q1 Proton energy scan",
        "Q1_proton_energy_scan.png",
        "#c83f31",
        "#2f8f5f",
        "Proton energy (MeV)",
    )


def plot_q1_gamma_energy_scan():
    plot_q1_particle_energy_scan(
        "gamma",
        GAMMA_SCAN_ENERGIES,
        "Q1 Gamma energy scan",
        "Q1_gamma_energy_scan.png",
        "#2f6db3",
        "#2f8f5f",
        "Gamma energy (MeV)",
    )


def plot_q1_region_dose():
    labels = ["Gamma", "Proton"]
    gamma_rows = read_event_rows(ROOT_FILES["gamma"])
    proton_rows = read_event_rows(ROOT_FILES["proton"])
    fallback = not gamma_rows or not proton_rows
    if fallback:
        tumor = [0.42, 1.15]
        normal = [0.35, 0.22]
    else:
        tumor = [mean(r["dose_tumor"] for r in gamma_rows), mean(r["dose_tumor"] for r in proton_rows)]
        normal = [mean(r["dose_normal"] for r in gamma_rows), mean(r["dose_normal"] for r in proton_rows)]

    x = range(len(labels))
    width = 0.35
    plt.figure(figsize=(7, 5))
    plt.bar([i - width / 2 for i in x], tumor, width, label="Tumor region", color="#c83f31")
    plt.bar([i + width / 2 for i in x], normal, width, label="Whole normal tissue", color="#2f8f5f")
    plt.xticks(list(x), labels)
    plt.ylabel("Mean event dose (Gy)")
    plt.title("Q1 Tumor vs whole-normal-tissue dose" + (" (reference fallback)" if fallback else ""))
    plt.yscale("log")
    plt.legend()
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Q1_region_dose_comparison.png", dpi=180)
    plt.close()


def plot_q1_let_spectra():
    gamma_hist = read_h1(ROOT_FILES["gamma"], "hLETTumor")
    proton_hist = read_h1(ROOT_FILES["proton"], "hLETTumor")
    fallback = not gamma_hist or not proton_hist
    if fallback:
        x = [LET_PLOT_XMAX * (i + 0.5) / LET_HISTOGRAM_BINS for i in range(LET_HISTOGRAM_BINS)]
        gamma_y = [math.exp(-v / 0.12) for v in x]
        proton_y = [math.exp(-v / 0.16) + 0.08 * math.exp(-0.5 * ((v - 0.7) / 0.18) ** 2) for v in x]
    else:
        x, gamma_y = gamma_hist
        _, proton_y = proton_hist

    gamma_mean = histogram_weighted_mean(x, gamma_y)
    proton_mean = histogram_weighted_mean(x, proton_y)
    gamma_steps = sum(gamma_y)
    proton_steps = sum(proton_y)

    fig, axes = plt.subplots(2, 1, figsize=(8.4, 7.0), gridspec_kw={"height_ratios": [3, 1]})
    axes[0].plot(x, normalize(gamma_y), label=f"gamma in tumor, mean={gamma_mean:.3f}", color="#2f6db3", linewidth=2)
    axes[0].plot(x, normalize(proton_y), label=f"proton in tumor, mean={proton_mean:.3f}", color="#c83f31", linewidth=2)
    axes[0].set_xlim(0, LET_PLOT_XMAX)
    axes[0].set_yscale("log")
    axes[0].set_ylim(1.e-4, 1.5)
    axes[0].set_ylabel("Normalized counts")
    axes[0].set_title("Q1 tumor LET spectra, low-LET zoom" + (" (reference fallback)" if fallback else ""))
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    labels = ["gamma", "proton"]
    means = [gamma_mean, proton_mean]
    axes[1].bar(labels, means, color=["#2f6db3", "#c83f31"], alpha=0.85)
    axes[1].set_ylim(0, max(means) * 1.22 if max(means) > 0 else 1.0)
    axes[1].set_ylabel("Mean LET\n(MeV/um)")
    axes[1].grid(axis="y", alpha=0.25)
    label_offset = max(means) * 0.015 if max(means) > 0 else 0.01
    axes[1].text(0, gamma_mean + label_offset, f"steps={gamma_steps:.0f}", ha="center", va="bottom", fontsize=9)
    axes[1].text(1, proton_mean + label_offset, f"steps={proton_steps:.0f}", ha="center", va="bottom", fontsize=9)
    axes[1].set_xlabel("LET (MeV/um), tumor-region steps")
    fig.tight_layout()
    plt.savefig(FIG_DIR / "Q1_let_spectra.png", dpi=180)
    plt.close()


def q2_cell_means(path):
    rows = read_cell_rows(path)
    if not rows:
        return None
    tumor = [r for r in rows if r["cell_type"] == 1]
    normal = [r for r in rows if r["cell_type"] == 0]
    return {
        "tumor_nucleus": mean(r["dose_nucleus"] for r in tumor),
        "normal_nucleus": mean(r["dose_nucleus"] for r in normal),
        "tumor_boron": mean(r["dose_boron"] for r in tumor),
    }


def q2_scan_summary(path):
    cell_rows = read_cell_rows(path)
    event_rows = read_event_rows(path)
    if not cell_rows or not event_rows:
        return None

    tumor = [row for row in cell_rows if row["cell_type"] == 1]
    normal = [row for row in cell_rows if row["cell_type"] == 0]
    tumor_cell = mean(row["dose_cell"] for row in tumor)
    normal_cell = mean(row["dose_cell"] for row in normal)
    tumor_nucleus = mean(row["dose_nucleus"] for row in tumor)
    normal_nucleus = mean(row["dose_nucleus"] for row in normal)
    reaction_yield = sum(row["n_li7"] for row in event_rows)
    return {
        "tumor_cell": tumor_cell,
        "normal_cell": normal_cell,
        "tumor_nucleus": tumor_nucleus,
        "normal_nucleus": normal_nucleus,
        "cell_localization": dose_localization_fraction(tumor_cell, normal_cell),
        "nucleus_localization": dose_localization_fraction(tumor_nucleus, normal_nucleus),
        "reaction_yield": reaction_yield,
        "nucleus_cell_ratio": tumor_nucleus / tumor_cell if tumor_cell > 0 else 0.0,
    }


def q2_therapy_comparison_summary(root_key, fallback_index):
    path = ROOT_FILES[root_key]
    cell_rows = read_cell_rows(path)
    event_rows = read_event_rows(path)
    if not cell_rows:
        fallback_values = [
            {"tumor_cell": 1.0e-5, "normal_cell": 9.0e-6, "tumor_nucleus": 3.0e-6, "normal_nucleus": 2.8e-6,
             "alpha_li7": 0, "gamma_secondaries": 1200, "electron_secondaries": 9000},
            {"tumor_cell": 1.5e-2, "normal_cell": 8.0e-4, "tumor_nucleus": 8.0e-3, "normal_nucleus": 4.5e-4,
             "alpha_li7": 0, "gamma_secondaries": 20, "electron_secondaries": 400},
            {"tumor_cell": 1.6e-2, "normal_cell": 4.8e-4, "tumor_nucleus": 1.7e-2, "normal_nucleus": 4.6e-4,
             "alpha_li7": 163, "gamma_secondaries": 7149, "electron_secondaries": 220},
            {"tumor_cell": 6.2e-3, "normal_cell": 2.3e-4, "tumor_nucleus": 4.4e-3, "normal_nucleus": 1.0e-12,
             "alpha_li7": 71, "gamma_secondaries": 7214, "electron_secondaries": 180},
        ][fallback_index]
        fallback_values["cell_localization"] = dose_localization_fraction(fallback_values["tumor_cell"], fallback_values["normal_cell"])
        fallback_values["nucleus_localization"] = dose_localization_fraction(fallback_values["tumor_nucleus"], fallback_values["normal_nucleus"])
        fallback_values["normal_burden"] = normal_burden(fallback_values["tumor_nucleus"], fallback_values["normal_nucleus"])
        fallback_values["fallback"] = True
        return fallback_values

    tumor = [row for row in cell_rows if row["cell_type"] == 1]
    normal = [row for row in cell_rows if row["cell_type"] == 0]
    tumor_cell = mean(row["dose_cell"] for row in tumor)
    normal_cell = mean(row["dose_cell"] for row in normal)
    tumor_nucleus = mean(row["dose_nucleus"] for row in tumor)
    normal_nucleus = mean(row["dose_nucleus"] for row in normal)
    alpha_li7 = sum(row["n_alpha"] + row["n_li7"] for row in event_rows)
    return {
        "tumor_cell": tumor_cell,
        "normal_cell": normal_cell,
        "tumor_nucleus": tumor_nucleus,
        "normal_nucleus": normal_nucleus,
        "cell_localization": dose_localization_fraction(tumor_cell, normal_cell),
        "nucleus_localization": dose_localization_fraction(tumor_nucleus, normal_nucleus),
        "normal_burden": normal_burden(tumor_nucleus, normal_nucleus),
        "alpha_li7": alpha_li7,
        "gamma_secondaries": sum(row["n_gamma"] for row in event_rows),
        "electron_secondaries": sum(row["n_electron"] for row in event_rows),
        "fallback": False,
    }


def q2_therapy_comparison_data():
    data = []
    for index, (case_name, label, root_key, color) in enumerate(Q2_THERAPY_COMPARISON_CASES):
        summary = q2_therapy_comparison_summary(root_key, index)
        data.append({
            "case": case_name,
            "label": label,
            "root_key": root_key,
            "color": color,
            **summary,
        })
    return data


def projected_columns(rows):
    if not rows:
        return []
    columns = {}
    for row in rows:
        x_um = round(row["x_mm"] * 1000.0, 3)
        z_um = round(row["z_mm"] * 1000.0, 3)
        key = (x_um, z_um, row["cell_type"])
        if key not in columns:
            columns[key] = {
                "x": x_um,
                "z": z_um,
                "cell_type": row["cell_type"],
                "dose": 0.0,
                "positive_cells": 0,
                "cells": 0,
            }
        columns[key]["dose"] += row["dose_cell"]
        columns[key]["positive_cells"] += 1 if row["dose_cell"] > 0 else 0
        columns[key]["cells"] += 1
    return list(columns.values())


def fallback_projected_columns(case_name):
    columns = []
    case_scale = {
        "gamma": (1.0e-5, 0.85e-5),
        "proton": (1.5e-2, 8.0e-4),
        "bnct_uniform": (1.6e-2, 4.8e-4),
        "bnct_shell": (6.2e-3, 2.3e-4),
    }[case_name]
    for ix in range(16):
        for iz in range(16):
            is_tumor = ((ix + iz) % 2) == 0
            x = (ix - 7.5) * 12.0
            z = (iz - 7.5) * 12.0
            radial = math.exp(-0.5 * ((x * x + z * z) ** 0.5 / 95.0) ** 2)
            base = case_scale[0] if is_tumor else case_scale[1]
            columns.append({"x": x, "z": z, "cell_type": 1 if is_tumor else 0, "dose": base * radial})
    return columns


def plot_q2_therapy_comparison_projected_maps():
    data = q2_therapy_comparison_data()
    fig = plt.figure(figsize=(16.8, 9.2), constrained_layout=True)
    grid = fig.add_gridspec(3, 4, height_ratios=[4.8, 1.45, 1.35], hspace=0.035, wspace=0.025)
    map_axes = [fig.add_subplot(grid[0, index]) for index in range(4)]
    dose_ax = fig.add_subplot(grid[1, :])
    localization_ax = fig.add_subplot(grid[2, :])
    image = None
    fallback = False

    for ax, item in zip(map_axes, data):
        rows = read_cell_rows(ROOT_FILES[item["root_key"]])
        columns = projected_columns(rows)
        if not columns:
            fallback = True
            columns = fallback_projected_columns(item["case"])
        panel_max = max((column["dose"] for column in columns), default=0.0)
        if panel_max <= 0:
            panel_max = 1.0
        for cell_type, marker, edge_color, label in (
            (1, "o", "#f03b20", "Cancer cells"),
            (0, "s", "#00a65a", "Normal cells"),
        ):
            selected = [column for column in columns if column["cell_type"] == cell_type]
            image = ax.scatter(
                [column["x"] for column in selected],
                [column["z"] for column in selected],
                c=[column["dose"] / panel_max for column in selected],
                s=54,
                cmap="inferno",
                vmin=0,
                vmax=1,
                marker=marker,
                edgecolors=edge_color,
                linewidths=1.1,
                label=label,
            )
        ax.add_patch(Circle((0, 0), 150.0, fill=False, edgecolor="#4a67c8", linestyle="--",
                            linewidth=1.1, alpha=0.75))
        ax.set_title(item["label"])
        ax.set_aspect("equal")
        ax.set_xlim(-130, 130)
        ax.set_ylim(-130, 130)
        ax.grid(alpha=0.16)
        ax.text(0.04, 0.96,
                f"T {item['tumor_cell']:.1e} Gy\nN {item['normal_cell']:.1e} Gy",
                transform=ax.transAxes, ha="left", va="top", fontsize=8,
                bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#777777", "alpha": 0.82})
        ax.set_xlabel("x relative to tumor center (um)")

    map_axes[0].set_ylabel("z relative to tumor center (um)")
    map_axes[-1].legend(loc="lower right", fontsize=8)
    labels = [item["label"] for item in data]
    x = list(range(len(data)))
    width = 0.34
    tumor_values = [max(item["tumor_cell"], 1.e-16) for item in data]
    normal_values = [max(item["normal_cell"], 1.e-16) for item in data]
    dose_ax.bar(
        [value - width / 2 for value in x],
        tumor_values,
        width,
        color=[item["color"] for item in data],
        label="Cancer cells",
    )
    dose_ax.bar(
        [value + width / 2 for value in x],
        normal_values,
        width,
        color=[item["color"] for item in data],
        alpha=0.45,
        hatch="//",
        edgecolor="#333333",
        linewidth=0.7,
        label="Normal cells",
    )
    dose_ax.set_xticks(x, labels)
    dose_ax.set_yscale("log")
    dose_ax.set_ylabel("Mean whole-cell dose (Gy)")
    dose_ax.set_title("Mean whole-cell dose")
    dose_ax.grid(axis="y", alpha=0.25)
    dose_ax.legend(ncol=2, fontsize=8, loc="upper left")
    localization_values = [item["cell_localization"] for item in data]
    localization_ax.bar(
        labels,
        localization_values,
        color=[item["color"] for item in data],
        width=0.62,
    )
    localization_ax.set_ylim(0, 1.05)
    localization_ax.set_ylabel("D_cancer / (D_cancer + D_normal)")
    localization_ax.set_title("Cell localization")
    localization_ax.grid(axis="y", alpha=0.25)
    for index, value in enumerate(localization_values):
        localization_ax.text(index, value + 0.025, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    fig.suptitle("Q2 Projected dose maps and whole-cell metrics by therapy" + (" (reference fallback)" if fallback else ""))
    fig.colorbar(image, ax=map_axes, label="Panel-normalized projected cell dose", fraction=0.018, pad=0.012)
    fig.savefig(FIG_DIR / "Q2_therapy_comparison_projected_maps.png", dpi=180)
    plt.close(fig)


def plot_q2_b10_concentration_scan():
    styles = {
        "uniform": {"label": "Uniform B10", "color": "#7b519d", "marker": "o"},
        "shell": {"label": "Outer shell B10", "color": "#d38b2f", "marker": "s"},
    }
    summaries = {}
    for mode in Q2_BORON_MODES:
        points = []
        for ppm in B10_SCAN_PPM:
            summary = q2_scan_summary(b10_scan_root_path(mode, ppm))
            if summary is None and ppm == 500000:
                summary = q2_scan_summary(ROOT_FILES[f"bnct_{mode}"])
            if summary is None:
                continue
            points.append((ppm, summary))
        summaries[mode] = points

    fallback = not any(summaries.values())
    if fallback:
        for mode, scale in (("uniform", 1.0), ("shell", 0.42)):
            summaries[mode] = []
            for ppm in B10_SCAN_PPM:
                saturation = 1.0 - math.exp(-ppm / 90000.0)
                tumor_nucleus = scale * 0.012 * saturation
                normal_nucleus = 1.e-10 * (ppm / 500000.0)
                tumor_cell = scale * 0.015 * saturation
                normal_cell = 0.0005 * saturation
                summaries[mode].append((ppm, {
                    "tumor_cell": tumor_cell,
                    "normal_cell": normal_cell,
                    "tumor_nucleus": tumor_nucleus,
                    "normal_nucleus": normal_nucleus,
                    "cell_localization": dose_localization_fraction(tumor_cell, normal_cell),
                    "nucleus_localization": dose_localization_fraction(tumor_nucleus, normal_nucleus),
                    "reaction_yield": int(scale * 150 * saturation),
                    "nucleus_cell_ratio": tumor_nucleus / tumor_cell if tumor_cell > 0 else 0.0,
                }))

    fig, axes = plt.subplots(2, 2, figsize=(11.6, 8.2), constrained_layout=True)
    for mode, points in summaries.items():
        if not points:
            continue
        ppm = [item[0] for item in points]
        style = styles[mode]
        label = style["label"]
        color = style["color"]
        marker = style["marker"]
        axes[0, 0].plot(ppm, [item[1]["nucleus_localization"] for item in points],
                        marker=marker, color=color, linewidth=2, label=f"{label}, nucleus")
        axes[0, 0].plot(ppm, [item[1]["cell_localization"] for item in points],
                        marker=marker, color=color, linewidth=1.6, linestyle="--", alpha=0.75,
                        label=f"{label}, whole cell")
        axes[0, 1].plot(ppm, [max(item[1]["tumor_nucleus"], 1.e-16) for item in points],
                        marker=marker, color=color, linewidth=2, label=f"{label}, cancer nucleus")
        axes[0, 1].plot(ppm, [max(item[1]["normal_nucleus"], 1.e-16) for item in points],
                        marker=marker, color=color, linewidth=1.6, linestyle="--", alpha=0.75,
                        label=f"{label}, normal nucleus")
        axes[1, 0].plot(ppm, [item[1]["reaction_yield"] for item in points],
                        marker=marker, color=color, linewidth=2, label=label)
        axes[1, 1].plot(ppm, [max(item[1]["nucleus_cell_ratio"], 1.e-16) for item in points],
                        marker=marker, color=color, linewidth=2, label=label)

    axes[0, 0].set_ylabel("D_cancer / (D_cancer + D_normal)")
    axes[0, 0].set_ylim(-0.02, 1.04)
    axes[0, 0].set_title("Dose localization fraction")
    axes[0, 1].set_ylabel("Mean nucleus dose (Gy)")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("Absolute nucleus dose")
    axes[1, 0].set_ylabel("Li7 count")
    axes[1, 0].set_title("B10-capture proxy")
    axes[1, 1].set_ylabel("D_cancer_nucleus / D_cancer_cell")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_title("Cancer nucleus-to-cell dose ratio")
    for ax in axes.flat:
        ax.set_xscale("log")
        ax.set_xlabel("B10 concentration in cancer cells (ppm)")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle("Q2 B10 concentration scan" + (" (reference fallback)" if fallback else ""))
    fig.savefig(FIG_DIR / "Q2_b10_concentration_scan.png", dpi=180)
    plt.close(fig)


def plot_q2_neutron_fluence_scan():
    styles = {
        "uniform": {"label": "Uniform B10", "color": "#7b519d", "marker": "o"},
        "shell": {"label": "Outer shell B10", "color": "#d38b2f", "marker": "s"},
    }
    summaries = {}
    for mode in Q2_BORON_MODES:
        points = []
        for events in NEUTRON_FLUENCE_EVENTS:
            summary = q2_scan_summary(neutron_fluence_root_path(mode, events))
            if summary is None and events == 20000:
                summary = q2_scan_summary(ROOT_FILES[f"bnct_{mode}"])
            if summary is None:
                continue
            points.append((events, summary))
        summaries[mode] = points

    fallback = not any(summaries.values())
    if fallback:
        for mode, scale in (("uniform", 1.0), ("shell", 0.38)):
            summaries[mode] = []
            for events in NEUTRON_FLUENCE_EVENTS:
                fluence = events / 20000.0
                tumor_cell = scale * 0.016 * fluence
                normal_cell = 0.00045 * fluence
                tumor_nucleus = scale * 0.016 * fluence
                normal_nucleus = 0.00015 * fluence
                summaries[mode].append((events, {
                    "tumor_cell": tumor_cell,
                    "normal_cell": normal_cell,
                    "tumor_nucleus": tumor_nucleus,
                    "normal_nucleus": normal_nucleus,
                    "cell_localization": dose_localization_fraction(tumor_cell, normal_cell),
                    "nucleus_localization": dose_localization_fraction(tumor_nucleus, normal_nucleus),
                    "reaction_yield": int(scale * 160 * fluence),
                    "nucleus_cell_ratio": tumor_nucleus / tumor_cell if tumor_cell > 0 else 0.0,
                }))

    fig, axes = plt.subplots(2, 2, figsize=(11.6, 8.2), constrained_layout=True)
    for mode, points in summaries.items():
        if not points:
            continue
        events = [item[0] for item in points]
        style = styles[mode]
        label = style["label"]
        color = style["color"]
        marker = style["marker"]
        axes[0, 0].plot(events, [max(item[1]["tumor_cell"], 1.e-16) for item in points],
                        marker=marker, color=color, linewidth=2, label=f"{label}, cancer cell")
        axes[0, 0].plot(events, [max(item[1]["normal_cell"], 1.e-16) for item in points],
                        marker=marker, color=color, linewidth=1.6, linestyle="--", alpha=0.75,
                        label=f"{label}, normal cell")
        axes[0, 1].plot(events, [max(item[1]["tumor_nucleus"], 1.e-16) for item in points],
                        marker=marker, color=color, linewidth=2, label=f"{label}, cancer nucleus")
        axes[0, 1].plot(events, [max(item[1]["normal_nucleus"], 1.e-16) for item in points],
                        marker=marker, color=color, linewidth=1.6, linestyle="--", alpha=0.75,
                        label=f"{label}, normal nucleus")
        axes[1, 0].plot(events, [item[1]["nucleus_localization"] for item in points],
                        marker=marker, color=color, linewidth=2, label=f"{label}, nucleus")
        axes[1, 0].plot(events, [item[1]["cell_localization"] for item in points],
                        marker=marker, color=color, linewidth=1.6, linestyle="--", alpha=0.75,
                        label=f"{label}, whole cell")
        axes[1, 1].plot(events, [item[1]["reaction_yield"] for item in points],
                        marker=marker, color=color, linewidth=2, label=label)

    axes[0, 0].set_ylabel("Mean cell dose (Gy)")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("Whole-cell dose")
    axes[0, 1].set_ylabel("Mean nucleus dose (Gy)")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("Nucleus dose")
    axes[1, 0].set_ylabel("D_cancer / (D_cancer + D_normal)")
    axes[1, 0].set_ylim(-0.02, 1.04)
    axes[1, 0].set_title("Dose localization fraction")
    axes[1, 1].set_ylabel("Li7 count")
    axes[1, 1].set_title("B10-capture proxy")
    for ax in axes.flat:
        ax.set_xscale("log")
        ax.set_xlabel("Neutron histories / relative fluence")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle("Q2 Neutron fluence scan at 500000 ppm B10" + (" (reference fallback)" if fallback else ""))
    fig.savefig(FIG_DIR / "Q2_neutron_fluence_scan.png", dpi=180)
    plt.close(fig)


def plot_q2_neutron_fluence_projected_maps():
    panels = []
    for mode in Q2_BORON_MODES:
        for events in NEUTRON_FLUENCE_MAP_EVENTS:
            path = neutron_fluence_root_path(mode, events)
            rows = read_cell_rows(path)
            if not rows and events == 20000:
                rows = read_cell_rows(ROOT_FILES[f"bnct_{mode}"])
            panels.append((mode, events, projected_columns(rows)))

    fallback = not any(columns for _, _, columns in panels)
    if fallback:
        panels = []
        for mode in Q2_BORON_MODES:
            for events in NEUTRON_FLUENCE_MAP_EVENTS:
                columns = []
                for ix in range(16):
                    for iz in range(16):
                        x = (ix - 7.5) * 12.0
                        z = (iz - 7.5) * 12.0
                        is_tumor = ((ix + iz) % 2) == 0
                        fluence = events / 20000.0
                        scale = 1.0 if mode == "uniform" else 0.38
                        dose = fluence * scale * (0.01 if is_tumor else 0.0003)
                        columns.append({"x": x, "z": z, "cell_type": 1 if is_tumor else 0, "dose": dose})
                panels.append((mode, events, columns))

    max_dose = max((column["dose"] for _, _, columns in panels for column in columns), default=0.0)
    if max_dose <= 0:
        max_dose = 1.0

    fig, axes = plt.subplots(2, len(NEUTRON_FLUENCE_MAP_EVENTS), figsize=(14.2, 7.1),
                             sharex=True, sharey=True, constrained_layout=True)
    image = None
    for row_index, mode in enumerate(Q2_BORON_MODES):
        for col_index, events in enumerate(NEUTRON_FLUENCE_MAP_EVENTS):
            ax = axes[row_index, col_index]
            columns = next(cols for panel_mode, panel_events, cols in panels
                           if panel_mode == mode and panel_events == events)
            for cell_type, marker, edge_color in (
                (1, "o", "#f03b20"),
                (0, "s", "#00a65a"),
            ):
                selected = [column for column in columns if column["cell_type"] == cell_type]
                image = ax.scatter(
                    [column["x"] for column in selected],
                    [column["z"] for column in selected],
                    c=[column["dose"] for column in selected],
                    s=58,
                    cmap="inferno",
                    vmin=0,
                    vmax=max_dose,
                    marker=marker,
                    edgecolors=edge_color,
                    linewidths=1.2,
                )
            ax.add_patch(Circle((0, 0), 150.0, fill=False, edgecolor="#4a67c8",
                                linestyle="--", linewidth=1.0, alpha=0.7))
            if row_index == 0:
                ax.set_title(f"{events:g} histories")
            if col_index == 0:
                ax.set_ylabel("Uniform B10\nz (um)" if mode == "uniform" else "Outer shell B10\nz (um)")
            ax.set_aspect("equal")
            ax.set_xlim(-125, 125)
            ax.set_ylim(-125, 125)
            ax.grid(alpha=0.15)
            if row_index == 1:
                ax.set_xlabel("x (um)")

    axes[0, -1].scatter([], [], s=58, marker="o", edgecolors="#f03b20", facecolors="black",
                        label="Cancer cells")
    axes[0, -1].scatter([], [], s=58, marker="s", edgecolors="#00a65a", facecolors="black",
                        label="Normal cells")
    axes[0, -1].legend(loc="upper right", fontsize=8)
    fig.suptitle("Q2 Neutron fluence projected dose maps at 500000 ppm B10" + (" (reference fallback)" if fallback else ""))
    fig.colorbar(image, ax=axes, label="Projected cell dose summed over y (Gy)", fraction=0.025, pad=0.02)
    fig.savefig(FIG_DIR / "Q2_neutron_fluence_projected_maps.png", dpi=180)
    plt.close(fig)


def plot_q2_boron_cell_model():
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.5), sharex=True, sharey=True)
    configs = [
        ("Uniform B10 in cancer cell", "uniform"),
        ("B10 in outer 1 um shell", "shell"),
    ]
    for ax, (title, mode) in zip(axes, configs):
        cell = Circle((0, 0), 5.0, facecolor="#f2a3a3" if mode == "uniform" else "#f6d9d9",
                      edgecolor="#b73b3b", linewidth=2, alpha=0.75)
        ax.add_patch(cell)
        if mode == "shell":
            shell = Circle((0, 0), 5.0, facecolor="none", edgecolor="#d38b2f", linewidth=8, alpha=0.8)
            ax.add_patch(shell)
            inner = Circle((0, 0), 4.0, facecolor="#f9eeee", edgecolor="none", alpha=0.9)
            ax.add_patch(inner)
        nucleus = Circle((0, 0), 2.5, facecolor="#6077c9", edgecolor="#263f99", linewidth=1.5, alpha=0.85)
        ax.add_patch(nucleus)
        ax.text(0, 0, "nucleus", color="white", ha="center", va="center", fontsize=9)
        ax.annotate("alpha / Li7\nshort range", xy=(3.5, 0.4), xytext=(6.5, 4.0),
                    arrowprops={"arrowstyle": "->", "lw": 1.3}, fontsize=9)
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xlim(-8, 10)
        ax.set_ylim(-7, 7)
        ax.set_xlabel("um")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("um")
    fig.suptitle("Q2 Cell-scale boron distribution model")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "Q2_boron_distribution_cell_model.png", dpi=180)
    plt.close(fig)


def plot_q2_micro_dose_map():
    datasets = [
        ("Uniform B10", neutron_fluence_root_path("uniform", 200000)),
        ("Outer shell B10", neutron_fluence_root_path("shell", 200000)),
    ]
    def panel_metrics(rows):
        tumor = [row for row in rows if row["cell_type"] == 1]
        normal = [row for row in rows if row["cell_type"] == 0]
        tumor_cell_values = [row["dose_cell"] for row in tumor]
        normal_cell_values = [row["dose_cell"] for row in normal]
        tumor_nucleus_values = [row["dose_nucleus"] for row in tumor]
        normal_nucleus_values = [row["dose_nucleus"] for row in normal]
        tumor_cell = mean(tumor_cell_values)
        normal_cell = mean(normal_cell_values)
        ratio = tumor_cell / normal_cell if normal_cell > 0 else 0.0
        return {
            "cell_means": [tumor_cell, normal_cell],
            "nucleus_means": [mean(tumor_nucleus_values), mean(normal_nucleus_values)],
            "ratio": ratio,
        }

    all_columns = []
    for _, path in datasets:
        all_columns.extend(projected_columns(read_cell_rows(path)))
    max_dose = max((r["dose"] for r in all_columns), default=0.0)
    if max_dose <= 0:
        max_dose = 1.0

    fig = plt.figure(figsize=(11.4, 9.0), constrained_layout=True)
    grid = fig.add_gridspec(3, 2, height_ratios=[4.2, 1.35, 1.35], hspace=0.10, wspace=0.08)
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    cell_bar_axes = [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    nucleus_bar_axes = [fig.add_subplot(grid[2, 0]), fig.add_subplot(grid[2, 1])]
    image = None
    for ax, cell_bar_ax, nucleus_bar_ax, (title, path) in zip(
        axes, cell_bar_axes, nucleus_bar_axes, datasets
    ):
        rows = read_cell_rows(path)
        columns = projected_columns(rows)
        for cell_type, marker, edge_color, label in (
            (1, "o", "#f03b20", "Cancer cells"),
            (0, "s", "#00a65a", "Normal cells in tumor"),
        ):
            selected = [r for r in columns if r["cell_type"] == cell_type]
            image = ax.scatter(
                [r["x"] for r in selected],
                [r["z"] for r in selected],
                c=[r["dose"] for r in selected],
                s=104,
                cmap="inferno",
                vmin=0,
                vmax=max_dose,
                marker=marker,
                edgecolors=edge_color,
                linewidths=1.8,
                label=label,
            )
        metrics = panel_metrics(rows)
        ax.add_patch(Circle((0, 0), 150.0, fill=False, edgecolor="#4a67c8", linestyle="--",
                            linewidth=1.4, alpha=0.75))
        ax.annotate("neutron beam\ncross-section", xy=(0, -105), xytext=(-92, -119),
                    arrowprops={"arrowstyle": "->", "color": "#4a67c8", "lw": 1.2},
                    color="#4a67c8", fontsize=9)
        ax.set_title(f"{title}  |  y-projected cell dose")
        ax.set_xlabel("x relative to tumor center (um)")
        ax.set_aspect("equal")
        ax.set_xlim(-130, 130)
        ax.set_ylim(-130, 130)
        ax.grid(alpha=0.18)
        cell_means = [max(value, 1.e-16) for value in metrics["cell_means"]]
        cell_bar_ax.bar(["Cancer", "Normal"], cell_means, color=["#c83f31", "#2f8f5f"], width=0.58)
        cell_bar_ax.set_yscale("log")
        cell_bar_ax.set_ylabel("Mean cell dose\n(Gy)")
        cell_bar_ax.set_title(f"Mean cell dose, cancer/normal={metrics['ratio']:.1f}x", fontsize=10, pad=10)
        cell_bar_ax.grid(axis="y", alpha=0.25)
        for index, value in enumerate(cell_means):
            cell_bar_ax.text(index, value * 1.15, f"{value:.2e}", ha="center", va="bottom", fontsize=8)

        nucleus_means = [max(value, 1.e-16) for value in metrics["nucleus_means"]]
        nucleus_bar_ax.bar(["Cancer", "Normal"], nucleus_means, color=["#c83f31", "#2f8f5f"], width=0.58)
        nucleus_bar_ax.set_yscale("log")
        nucleus_bar_ax.set_ylabel("Mean nucleus dose\n(Gy)")
        nucleus_bar_ax.set_title("Mean nucleus dose", fontsize=10, pad=10)
        nucleus_bar_ax.grid(axis="y", alpha=0.25)
        for index, value in enumerate(nucleus_means):
            nucleus_bar_ax.text(index, value * 1.15, f"{value:.2e}", ha="center", va="bottom", fontsize=8)
    axes[0].set_ylabel("z relative to tumor center (um)")
    axes[1].legend(loc="upper right")
    axes[1].tick_params(labelleft=False)
    fig.suptitle("Q2 Representative tumor micro-region projected dose map")
    fig.colorbar(image, ax=axes, label="Projected cell dose summed over y (Gy, linear scale)", fraction=0.035, pad=0.02)
    fig.savefig(FIG_DIR / "Q2_micro_dose_map_uniform_vs_shell.png", dpi=180)
    plt.close(fig)


def plot_q2_mixed_geometry_layout():
    rows = read_cell_rows(ROOT_FILES["bnct_uniform"])
    fallback = not rows
    if fallback:
        rows = []
        pitch_um = 12.0
        for ix in range(16):
            for iz in range(16):
                x = (ix - 7.5) * pitch_um
                z = (iz - 7.5) * pitch_um
                rows.append({"x_mm": x / 1000.0, "z_mm": z / 1000.0,
                             "cell_type": 1 if (ix + iz) % 2 == 0 else 0})

    xs = [r["x_mm"] * 1000.0 for r in rows]
    zs = [r["z_mm"] * 1000.0 for r in rows]
    colors = ["#c83f31" if r["cell_type"] == 1 else "#2f8f5f" for r in rows]

    fig, ax = plt.subplots(figsize=(6.8, 6.2))
    ax.scatter(xs, zs, s=38, c=colors, alpha=0.86, edgecolors="white", linewidths=0.25)
    ax.add_patch(Rectangle((-100, -100), 200, 200, fill=False, edgecolor="#333333",
                           linestyle="--", linewidth=1.4, label="Cell patch"))
    ax.add_patch(Circle((0, 0), 150.0, fill=False, edgecolor="#4a67c8",
                        linestyle="--", linewidth=1.5, label="150 um beam radius"))
    ax.scatter([], [], s=60, c="#c83f31", label="B10-loaded cancer cells")
    ax.scatter([], [], s=60, c="#2f8f5f", label="Normal cells, no B10")
    ax.set_aspect("equal")
    ax.set_xlim(-170, 170)
    ax.set_ylim(-170, 170)
    ax.set_xlabel("x relative to tumor center (um)")
    ax.set_ylabel("z relative to tumor center (um)")
    ax.set_title("Q2 mixed cell layout in representative tumor micro-region" + (" (reference fallback)" if fallback else ""))
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "Q2_geometry_mixed_cell_layout.png", dpi=180)
    plt.close(fig)


def plot_q2_nucleus_dose():
    uniform = q2_cell_means(ROOT_FILES["bnct_uniform"])
    shell = q2_cell_means(ROOT_FILES["bnct_shell"])
    fallback = uniform is None or shell is None
    if fallback:
        uniform = {"tumor_nucleus": 1.0, "normal_nucleus": 0.12, "tumor_boron": 1.4}
        shell = {"tumor_nucleus": 0.62, "normal_nucleus": 0.10, "tumor_boron": 1.7}

    labels = ["Uniform B10", "Outer shell B10"]
    tumor = [uniform["tumor_nucleus"], shell["tumor_nucleus"]]
    normal = [uniform["normal_nucleus"], shell["normal_nucleus"]]
    x = range(len(labels))
    width = 0.35
    plt.figure(figsize=(7.5, 5))
    plt.bar([i - width / 2 for i in x], tumor, width, label="Tumor nucleus", color="#c83f31")
    plt.bar([i + width / 2 for i in x], normal, width, label="Normal nucleus", color="#2f8f5f")
    plt.xticks(list(x), labels)
    plt.ylabel("Mean nucleus dose (Gy)")
    plt.title("Q2 BNCT nucleus dose" + (" (reference fallback)" if fallback else ""))
    plt.legend()
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Q2_bnct_nucleus_dose.png", dpi=180)
    plt.savefig(FIG_DIR / "Q2_nucleus_dose_selectivity.png", dpi=180)
    plt.close()


def plot_q2_nucleus_dose_scatter():
    datasets = [
        ("Uniform B10", ROOT_FILES["bnct_uniform"], 0),
        ("Outer shell B10", ROOT_FILES["bnct_shell"], 1),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.9), sharey=True, constrained_layout=True)
    fallback = False
    for ax, (title, path, panel_index) in zip(axes, datasets):
        rows = read_cell_rows(path)
        if not rows:
            fallback = True
            rows = []
        tumor = [r["dose_nucleus"] for r in rows if r["cell_type"] == 1]
        normal = [r["dose_nucleus"] for r in rows if r["cell_type"] == 0]
        if not tumor and not normal:
            tumor = [0.02, 0.4, 1.2, 0.0, 0.08]
            normal = [0.0, 0.0, 0.01, 0.0, 0.0]

        samples = [("Cancer", tumor, "#c83f31"), ("Normal", normal, "#2f8f5f")]
        for x_index, (_, values, color) in enumerate(samples):
            positive = [value for value in values if value > 0]
            zero_count = len(values) - len(positive)
            ax.scatter([x_index] * len(positive), positive, s=22, alpha=0.62, color=color)
            ax.scatter([x_index], [1.e-12], s=max(20, min(180, zero_count * 0.03)),
                       alpha=0.35, color=color, marker="s")
            ax.hlines(mean(values), x_index - 0.27, x_index + 0.27, colors=color, linewidth=2.0)
            if zero_count:
                ax.text(x_index, 1.7e-12, f"{zero_count} zero-dose cells",
                        ha="center", va="bottom", fontsize=8, color=color)
        ax.set_xticks([0, 1], ["Cancer", "Normal"])
        ax.set_yscale("log")
        ax.set_ylim(1.e-12, None)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)
        if panel_index == 0:
            ax.set_ylabel("Nucleus dose per cell (Gy)")
    fig.suptitle("Q2 nucleus-dose selectivity per cell" + (" (reference fallback)" if fallback else ""))
    fig.savefig(FIG_DIR / "Q2_nucleus_dose_scatter_selectivity.png", dpi=180)
    plt.close(fig)


def plot_q2_selectivity_index():
    uniform = q2_cell_means(ROOT_FILES["bnct_uniform"])
    shell = q2_cell_means(ROOT_FILES["bnct_shell"])
    fallback = uniform is None or shell is None
    if fallback:
        uniform = {"tumor_nucleus": 1.0, "normal_nucleus": 0.12}
        shell = {"tumor_nucleus": 0.62, "normal_nucleus": 0.10}
    labels = ["Uniform B10", "Outer shell B10"]
    values = []
    for item in (uniform, shell):
        total = item["tumor_nucleus"] + item["normal_nucleus"]
        values.append(item["tumor_nucleus"] / total if total > 0 else 0.0)

    plt.figure(figsize=(6.8, 4.7))
    plt.bar(labels, values, color=["#7b519d", "#d38b2f"])
    plt.ylim(0, 1.05)
    plt.ylabel("D_cancer_nucleus / (D_cancer_nucleus + D_normal_nucleus)")
    plt.title("Q2 BNCT cell-scale selectivity index" + (" (reference fallback)" if fallback else ""))
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Q2_bnct_selectivity_index.png", dpi=180)
    plt.close()


def plot_q2_secondary_yield():
    uniform_rows = read_event_rows(ROOT_FILES["bnct_uniform"])
    shell_rows = read_event_rows(ROOT_FILES["bnct_shell"])
    fallback = not uniform_rows or not shell_rows
    if fallback:
        data = {
            "Uniform B10": [38, 34, 22],
            "Outer shell B10": [41, 36, 20],
        }
    else:
        data = {
            "Uniform B10": [
                sum(r["n_alpha"] for r in uniform_rows),
                sum(r["n_li7"] for r in uniform_rows),
                sum(r["n_gamma"] for r in uniform_rows),
            ],
            "Outer shell B10": [
                sum(r["n_alpha"] for r in shell_rows),
                sum(r["n_li7"] for r in shell_rows),
                sum(r["n_gamma"] for r in shell_rows),
            ],
        }

    species = ["alpha", "Li7", "gamma"]
    x = range(len(species))
    width = 0.35
    plt.figure(figsize=(7.5, 5))
    plt.bar([i - width / 2 for i in x], data["Uniform B10"], width, label="Uniform B10", color="#7b519d")
    plt.bar([i + width / 2 for i in x], data["Outer shell B10"], width, label="Outer shell B10", color="#d38b2f")
    plt.xticks(list(x), species)
    plt.ylabel("Secondary count")
    plt.title("Q2 BNCT secondary yields" + (" (reference fallback)" if fallback else ""))
    plt.legend()
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Q2_bnct_secondary_yield.png", dpi=180)
    plt.close()


def plot_q2_cell_dose_spectra():
    datasets = [
        ("Uniform B10", ROOT_FILES["bnct_uniform"], "#7b519d"),
        ("Outer shell B10", ROOT_FILES["bnct_shell"], "#d38b2f"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    fallback = False
    for label, path, color in datasets:
        rows = read_cell_rows(path)
        tumor = [r["dose_cell"] for r in rows if r["cell_type"] == 1 and r["dose_cell"] > 0]
        nucleus = [r["dose_nucleus"] for r in rows if r["cell_type"] == 1 and r["dose_nucleus"] > 0]
        if not tumor:
            fallback = True
            tumor = [math.exp(-i / 10) for i in range(1, 60)]
        if not nucleus:
            nucleus = [0.0]
        axes[0].hist(tumor, bins=40, histtype="step", linewidth=2, label=label, color=color)
        axes[1].hist(nucleus, bins=40, histtype="step", linewidth=2, label=label, color=color)
    axes[0].set_xlabel("Tumor cell dose (Gy)")
    axes[0].set_ylabel("Cell count")
    axes[0].set_title("Whole cancer-cell dose")
    axes[1].set_xlabel("Cancer nucleus dose (Gy)")
    axes[1].set_title("Cancer-nucleus dose")
    for ax in axes:
        ax.set_yscale("log")
        ax.legend()
        ax.grid(alpha=0.25)
    fig.suptitle("Q2 Cell and nucleus dose spectra" + (" (reference fallback)" if fallback else ""))
    fig.savefig(FIG_DIR / "Q2_cell_dose_spectra.png", dpi=180)
    plt.close(fig)


def plot_q2_boron_distribution():
    radius = [i * 0.05 for i in range(101)]
    uniform = [1.0 for _ in radius]
    shell = [1.0 if r >= 4.0 else 0.0 for r in radius]
    nucleus = [1.0 if r <= 2.5 else float("nan") for r in radius]

    plt.figure(figsize=(8, 5))
    plt.plot(radius, uniform, label="Uniform tumor cell", color="#7b519d", linewidth=2)
    plt.plot(radius, shell, label="Outer 1 um shell", color="#d38b2f", linewidth=2)
    plt.plot(radius, nucleus, label="Nucleus radius", color="#2f6db3", linewidth=3, alpha=0.45)
    plt.xlabel("Cell radius r (um)")
    plt.ylabel("Relative B10 concentration C/C0")
    plt.title("Q2 Boron-10 radial distribution model")
    plt.ylim(-0.05, 1.15)
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Q2_boron_distribution.png", dpi=180)
    plt.close()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Plot Geant4 tumor-therapy assignment results.")
    parser.add_argument(
        "--section",
        choices=("all", "q1", "q2", "q2new"),
        default="all",
        help="Generate all figures or only one assignment section.",
    )
    return parser.parse_args(argv)


# =====================================================================
# Q2 redesign: figures F2 (shell vs uniform main), F3' (single-cell
# stacked dose distribution), F4 (equal-dose cross-therapy), F5 (B10
# total scan). All consume output_q2A_/q2B_/q2C_*.root.
# =====================================================================

Q2A_UNIFORM_PPM_DEFAULT = 300000


def q2a_paths(mode, ppm=Q2A_UNIFORM_PPM_DEFAULT, seeds=(1, 2, 3)):
    """Return list of expected ROOT paths for experiment-A runs."""
    return [PROJECT_DIR / f"output_q2A_{mode}_{ppm}ppm_seed{s}.root" for s in seeds]


def aggregate_q2a_summary(mode, ppm=Q2A_UNIFORM_PPM_DEFAULT):
    """Run cell_summary on each seed and collect per-class metrics across seeds.

    Returns dict {tumor: {metric: [v1, v2, v3]}, normal: {...}, n_seeds: N,
    a_li7_total: [N1, N2, N3]}. Missing seeds are skipped silently.
    """
    rows_per_seed = []
    a_li7 = []
    for path in q2a_paths(mode, ppm):
        if not path.exists():
            continue
        rows = read_cell_rows(path)
        evts = read_event_rows(path)
        if not rows:
            continue
        rows_per_seed.append(cell_summary(rows))
        a_li7.append(sum(e["n_alpha"] + e["n_li7"] for e in evts))
    if not rows_per_seed:
        return None
    out = {"tumor": {}, "normal": {}, "n_seeds": len(rows_per_seed), "a_li7": a_li7}
    keys = ("mean_dose_cell", "mean_dose_nucleus", "mean_dose_eq", "mean_S",
            "lethal_fraction", "alpha_nuc_hits", "li_nuc_hits", "n_cells")
    for cls in ("tumor", "normal"):
        for k in keys:
            out[cls][k] = [s[cls][k] for s in rows_per_seed]
    return out


def _bar_with_err(ax, x, values_per_group, colors, labels, ylabel, title=None):
    """values_per_group is list of (mean, std) per group."""
    means = [v[0] for v in values_per_group]
    errs = [v[1] for v in values_per_group]
    bars = ax.bar(x, means, yerr=errs, capsize=4, color=colors,
                  edgecolor="#333", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=12, ha="right")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    if title:
        ax.set_title(title, fontsize=10)
    for bar, m in zip(bars, means):
        if m > 0:
            ax.text(bar.get_x() + bar.get_width()/2, m, f"{m:.2g}",
                    ha="center", va="bottom", fontsize=8)


def _mean_std(values):
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    m = sum(values) / n
    if n < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in values) / (n - 1)
    return m, math.sqrt(var)


def plot_q2_shell_vs_uniform_main(ppm=Q2A_UNIFORM_PPM_DEFAULT):
    """F2: 4-panel main result for hypothesis H1 (shell > uniform at equal total B10)."""
    uniform = aggregate_q2a_summary("uniform", ppm)
    shell = aggregate_q2a_summary("shell", ppm)
    if uniform is None or shell is None:
        print(f"[F2] missing q2A outputs at ppm={ppm}; skipping")
        return
    fig, axes = plt.subplots(1, 4, figsize=(15.5, 4.6))

    # Panel (a): tumor / normal nucleus dose, grouped by mode.
    groups = ["uniform\nT", "uniform\nN", "shell\nT", "shell\nN"]
    colors = ["#c83f31", "#5fa8d3", "#7b3fbf", "#5fa8d3"]
    vals = [
        _mean_std(uniform["tumor"]["mean_dose_nucleus"]),
        _mean_std(uniform["normal"]["mean_dose_nucleus"]),
        _mean_std(shell["tumor"]["mean_dose_nucleus"]),
        _mean_std(shell["normal"]["mean_dose_nucleus"]),
    ]
    _bar_with_err(axes[0], np.arange(4), vals, colors, groups,
                  "Mean nucleus dose (Gy)", "(a) Nucleus dose")

    # Panel (b): LQ survival fraction.
    vals_S = [
        _mean_std(uniform["tumor"]["mean_S"]),
        _mean_std(uniform["normal"]["mean_S"]),
        _mean_std(shell["tumor"]["mean_S"]),
        _mean_std(shell["normal"]["mean_S"]),
    ]
    _bar_with_err(axes[1], np.arange(4), vals_S, colors, groups,
                  "LQ survival S (cell mean)", "(b) Survival (LQ + RBE)")
    axes[1].set_ylim(0, 1.05)

    # Panel (c): lethal-hit fraction (geometric proxy).
    vals_LH = [
        _mean_std(uniform["tumor"]["lethal_fraction"]),
        _mean_std(uniform["normal"]["lethal_fraction"]),
        _mean_std(shell["tumor"]["lethal_fraction"]),
        _mean_std(shell["normal"]["lethal_fraction"]),
    ]
    _bar_with_err(axes[2], np.arange(4), vals_LH, colors, groups,
                  "Lethal-hit fraction\n(>=1 alpha or Li7 in nucleus)",
                  "(c) Lethal-hit proxy")

    # Panel (d): in-nucleus alpha+Li7 hit count totals.
    vals_NH = [
        _mean_std([a + b for a, b in zip(uniform["tumor"]["alpha_nuc_hits"], uniform["tumor"]["li_nuc_hits"])]),
        _mean_std([a + b for a, b in zip(uniform["normal"]["alpha_nuc_hits"], uniform["normal"]["li_nuc_hits"])]),
        _mean_std([a + b for a, b in zip(shell["tumor"]["alpha_nuc_hits"], shell["tumor"]["li_nuc_hits"])]),
        _mean_std([a + b for a, b in zip(shell["normal"]["alpha_nuc_hits"], shell["normal"]["li_nuc_hits"])]),
    ]
    _bar_with_err(axes[3], np.arange(4), vals_NH, colors, groups,
                  "Total alpha+Li7 nucleus hits",
                  "(d) Reaction products in nucleus")

    fig.suptitle(f"F2 Shell vs uniform B10 at equal total atom count "
                 f"(uniform-equiv {ppm} ppm, {uniform['n_seeds']} seeds)",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_DIR / "Q2_shell_vs_uniform_main.png", dpi=180)
    plt.close(fig)


def _stack_h2_across_seeds(mode, hist_name, ppm=Q2A_UNIFORM_PPM_DEFAULT):
    """Sum cell-local H2 from all seeds of one experiment-A mode."""
    grids = []
    edges = None
    for path in q2a_paths(mode, ppm):
        if not path.exists():
            continue
        result = read_h2(path, hist_name)
        if result is None:
            continue
        if edges is None:
            edges = (result[0], result[1])
        grids.append(np.array(result[2]))
    if not grids:
        return None
    return edges[0], edges[1], np.sum(grids, axis=0)


def _stack_h1_across_seeds(mode, hist_name, ppm=Q2A_UNIFORM_PPM_DEFAULT):
    """Sum 1D cell-radial histograms across seeds. Returns (centers, totals)."""
    counts = None
    centers = None
    for path in q2a_paths(mode, ppm):
        if not path.exists():
            continue
        h = read_h1(path, hist_name)
        if h is None:
            continue
        if counts is None:
            centers = list(h[0])
            counts = list(h[1])
        else:
            counts = [c + d for c, d in zip(counts, h[1])]
    if counts is None:
        return None
    return centers, counts


def plot_q2_singlecell_dose_distribution(ppm=Q2A_UNIFORM_PPM_DEFAULT):
    """F3': stacked single-cell dose distribution.

    Top row: 3 cell-local 2D edep maps (r_xy, z_local) — normal / tumor uniform / tumor shell.
    Bottom row: 3 radial 1D dose density curves (Gy / um^3, 4*pi*r^2 jacobian removed).
    """
    # --- Gather data: stack tumor cell H2 from uniform vs shell q2A;
    # use either's "normal" H2 (they should be equivalent — reaction-free).
    h2_tumor_u = _stack_h2_across_seeds("uniform", "hCellLocalTumor", ppm)
    h2_tumor_s = _stack_h2_across_seeds("shell",   "hCellLocalTumor", ppm)
    h2_normal_u = _stack_h2_across_seeds("uniform", "hCellLocalNormal", ppm)
    h2_normal_s = _stack_h2_across_seeds("shell",   "hCellLocalNormal", ppm)
    if not all([h2_tumor_u, h2_tumor_s, h2_normal_u, h2_normal_s]):
        print("[F3'] missing q2A H2 inputs; skipping")
        return
    # Combine normal cell maps from both modes (they share the no-boron condition).
    x_edges, y_edges, _ = h2_normal_u
    nx = len(x_edges) - 1
    ny = len(y_edges) - 1
    grid_normal = h2_normal_u[2] + h2_normal_s[2]
    grid_tumor_u = h2_tumor_u[2]
    grid_tumor_s = h2_tumor_s[2]

    # Cells contributing per panel: 2048 normal × (uniform_seeds + shell_seeds),
    # 2048 tumor × seeds for each tumor mode.
    n_uniform = aggregate_q2a_summary("uniform", ppm)
    n_shell = aggregate_q2a_summary("shell", ppm)
    n_norm_cells = (sum(n_uniform["normal"]["n_cells"]) if n_uniform else 0) + \
                   (sum(n_shell["normal"]["n_cells"]) if n_shell else 0)
    n_tum_cells_u = sum(n_uniform["tumor"]["n_cells"]) if n_uniform else 0
    n_tum_cells_s = sum(n_shell["tumor"]["n_cells"]) if n_shell else 0

    # Convert MeV per (r_xy, z_local) bin into dose density Gy/um^3:
    #   bin volume in 2D-cylindrical = 2*pi*r * dr * dz (we plot mean over cells,
    #   so divide by n_cells too).
    dr = x_edges[1] - x_edges[0]
    dz = y_edges[1] - y_edges[0]
    # Geant4 reports MeV; convert to Gy assuming water density 1 g/cm^3 -> mass = 1e-12 g per um^3
    MEV_TO_J = 1.602e-13
    G_PER_UM3 = 1.0e-12  # water density, 1 g/cm^3 = 1e-12 g/um^3
    UM3_TO_KG = 1.0e-15  # 1 um^3 of water = 1e-12 g = 1e-15 kg
    # dose [Gy] in a bin = edep_MeV * MEV_TO_J / (mass_kg_in_bin)
    # mass_kg_in_bin = bin_volume_um3 * UM3_TO_KG
    #
    # We want average per-cell dose density: edep / n_cells / volume_um3 -> MeV/um^3
    # then -> Gy: divide by mass per um^3 in kg = UM3_TO_KG; multiply by MEV_TO_J.

    def to_dose_density(grid, n_cells):
        if n_cells <= 0:
            return None
        out = np.zeros_like(grid, dtype=float)
        for iy in range(ny):
            for ix in range(nx):
                r = 0.5 * (x_edges[ix] + x_edges[ix + 1])
                # cylindrical shell volume per radial bin (μm^3): 2π r dr dz
                if r <= 0:
                    out[iy][ix] = 0.0
                    continue
                vol_um3 = 2.0 * math.pi * r * dr * dz
                edep_per_cell_per_um3 = grid[iy][ix] / n_cells / vol_um3
                # MeV/um^3 -> Gy
                dose_gy = edep_per_cell_per_um3 * MEV_TO_J / UM3_TO_KG
                out[iy][ix] = dose_gy
        return out

    map_normal = to_dose_density(grid_normal, n_norm_cells)
    map_tumor_u = to_dose_density(grid_tumor_u, n_tum_cells_u)
    map_tumor_s = to_dose_density(grid_tumor_s, n_tum_cells_s)
    if any(m is None for m in (map_normal, map_tumor_u, map_tumor_s)):
        print("[F3'] zero cell counts in one panel; skipping")
        return

    vmax = max(np.max(m) for m in (map_normal, map_tumor_u, map_tumor_s))
    if vmax <= 0:
        vmax = 1.0

    # --- Bottom row: radial 1D dose density (per-cell average per um^3).
    rad_normal_u = _stack_h1_across_seeds("uniform", "hCellRadialNormal", ppm)
    rad_normal_s = _stack_h1_across_seeds("shell",   "hCellRadialNormal", ppm)
    rad_tumor_u  = _stack_h1_across_seeds("uniform", "hCellRadialTumor",  ppm)
    rad_tumor_s  = _stack_h1_across_seeds("shell",   "hCellRadialTumor",  ppm)
    if not all([rad_normal_u, rad_normal_s, rad_tumor_u, rad_tumor_s]):
        print("[F3'] radial H1 missing; skipping")
        return
    centers = rad_normal_u[0]
    dr1d = centers[1] - centers[0]
    rad_normal_counts = [a + b for a, b in zip(rad_normal_u[1], rad_normal_s[1])]

    def radial_dose_density(counts, n_cells):
        if n_cells <= 0:
            return [0] * len(counts)
        out = []
        for r, c in zip(centers, counts):
            if r <= 0:
                out.append(0.0)
                continue
            shell_vol_um3 = 4.0 * math.pi * r * r * dr1d
            edep_per_cell_per_um3 = c / n_cells / shell_vol_um3
            dose_gy = edep_per_cell_per_um3 * MEV_TO_J / UM3_TO_KG
            out.append(dose_gy)
        return out

    line_normal = radial_dose_density(rad_normal_counts, n_norm_cells)
    line_tumor_u = radial_dose_density(rad_tumor_u[1], n_tum_cells_u)
    line_tumor_s = radial_dose_density(rad_tumor_s[1], n_tum_cells_s)

    # --- Plot.
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.0),
                             gridspec_kw={"height_ratios": [1.05, 0.95], "hspace": 0.36})

    titles = ["normal cell (no B10)",
              f"tumor cell, uniform B10 ({ppm} ppm)",
              "tumor cell, shell B10 (equal total)"]
    panels = [map_normal, map_tumor_u, map_tumor_s]
    for ax, panel, title in zip(axes[0], panels, titles):
        im = ax.pcolormesh(x_edges, y_edges, panel,
                           cmap="inferno", vmin=0, vmax=vmax)
        ax.set_xlabel("r_xy (um)")
        ax.set_ylabel("z_local (um)")
        ax.set_title(title, fontsize=10.5)
        ax.set_aspect("auto")
        # 5 um cell radius circle (projection)
        ax.axhline(0, color="white", linewidth=0.4, alpha=0.5)
    cbar = fig.colorbar(im, ax=axes[0], orientation="vertical",
                        shrink=0.85, pad=0.015)
    cbar.set_label("Mean dose density (Gy / um^3)")

    radial_panels = [(line_normal, "#5fa8d3", "normal"),
                     (line_tumor_u, "#c83f31", "tumor uniform"),
                     (line_tumor_s, "#7b3fbf", "tumor shell")]
    for ax, (line, color, label) in zip(axes[1], radial_panels):
        ax.plot(centers, line, color=color, linewidth=2.2, label=label)
        ax.fill_between(centers, line, color=color, alpha=0.18)
        ax.set_xlabel("r (um) from cell center")
        ax.set_ylabel("Dose density (Gy / um^3)")
        ax.set_xlim(0, 5)
        ax.grid(alpha=0.25)
        ax.set_title(label, fontsize=10.5)
        # Mark r = 4 um (start of shell layer, cellRadius - 1 um shell)
        ax.axvline(4.0, color="#888", linestyle="--", linewidth=0.9, alpha=0.6)
        ax.text(4.05, ax.get_ylim()[1] * 0.95, "shell",
                fontsize=8, color="#666", va="top", ha="left")
    fig.suptitle("F3' Single-cell stacked dose distribution "
                 f"(equal total B10, {n_uniform['n_seeds']} seeds, {ppm} ppm uniform-equiv)",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "Q2_singlecell_dose_distribution.png", dpi=180)
    plt.close(fig)


def plot_q2_therapy_equal_dose():
    """F4: cross-therapy comparison at matched tumor-cell prescription dose.

    Reads output_q2B_<group>_final.root for {gamma, proton, neutron_uniform, neutron_shell}.
    """
    groups = [
        ("gamma", "gamma 1 MeV", "#2f6db3"),
        ("proton", "proton 80 MeV", "#c83f31"),
        ("neutron_uniform", "BNCT uniform", "#7b3fbf"),
        ("neutron_shell", "BNCT shell", "#d38b2f"),
    ]
    summaries = []
    for name, label, color in groups:
        path = PROJECT_DIR / f"output_q2B_{name}_final.root"
        if not path.exists():
            print(f"[F4] missing {path.name}; skipping")
            return
        rows = read_cell_rows(path)
        if not rows:
            print(f"[F4] empty CellTree for {name}; skipping")
            return
        s = cell_summary(rows)
        s["_label"] = label
        s["_color"] = color
        s["_name"] = name
        summaries.append(s)

    fig, axes = plt.subplots(1, 4, figsize=(15.5, 4.6))
    x = np.arange(len(summaries))
    labels = [s["_label"] for s in summaries]
    colors = [s["_color"] for s in summaries]

    # (a) tumor vs normal cell dose
    width = 0.36
    tumor_d = [s["tumor"]["mean_dose_cell"] for s in summaries]
    normal_d = [s["normal"]["mean_dose_cell"] for s in summaries]
    axes[0].bar(x - width/2, tumor_d, width, color=colors, label="tumor", edgecolor="#222")
    axes[0].bar(x + width/2, normal_d, width, color=colors, alpha=0.45, hatch="//",
                label="normal", edgecolor="#222")
    axes[0].set_xticks(x); axes[0].set_xticklabels(labels, rotation=15, ha="right")
    axes[0].set_ylabel("Mean cell dose (Gy)")
    axes[0].set_title("(a) Tumor vs normal cell dose")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend(fontsize=9)

    # (b) LQ survival per group, normal cells only — the safety axis.
    s_normal = [s["normal"]["mean_S"] for s in summaries]
    axes[1].bar(x, s_normal, color=colors, edgecolor="#222")
    axes[1].set_xticks(x); axes[1].set_xticklabels(labels, rotation=15, ha="right")
    axes[1].set_ylabel("Normal cell mean S")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title("(b) Normal cell survival (higher = safer)")
    axes[1].grid(axis="y", alpha=0.25)
    for xi, v in zip(x, s_normal):
        axes[1].text(xi, v, f"{v:.3f}", ha="center", va="bottom", fontsize=9)

    # (c) Therapeutic index = K_tumor / K_normal where K = 1 - S
    ti = []
    for s in summaries:
        kT = 1.0 - s["tumor"]["mean_S"]
        kN = 1.0 - s["normal"]["mean_S"]
        ti.append(kT / kN if kN > 1e-9 else float("inf") if kT > 0 else 0.0)
    finite = [v for v in ti if math.isfinite(v)]
    axes[2].bar(x, [v if math.isfinite(v) else (max(finite) * 1.5 if finite else 1) for v in ti],
                color=colors, edgecolor="#222")
    axes[2].set_xticks(x); axes[2].set_xticklabels(labels, rotation=15, ha="right")
    axes[2].set_ylabel("K_tumor / K_normal (TI)")
    axes[2].set_title("(c) Therapeutic index")
    axes[2].grid(axis="y", alpha=0.25)
    for xi, v in zip(x, ti):
        txt = "inf" if not math.isfinite(v) else f"{v:.1f}"
        axes[2].text(xi, axes[2].get_ylim()[1]*0.95, txt, ha="center", fontsize=8.5,
                     va="top", color="#222")

    # (d) tumor-cell nucleus dose CDF
    for s in summaries:
        rows = []
        for path in [PROJECT_DIR / f"output_q2B_{s['_name']}_final.root"]:
            rows.extend(read_cell_rows(path))
        nuc_doses = sorted(r["dose_nucleus"] for r in rows if r["cell_type"] == 1)
        if nuc_doses:
            cdf = np.arange(1, len(nuc_doses) + 1) / len(nuc_doses)
            axes[3].plot(nuc_doses, cdf, color=s["_color"], label=s["_label"], linewidth=2)
    axes[3].set_xlabel("tumor nucleus dose (Gy)")
    axes[3].set_ylabel("CDF")
    axes[3].set_xscale("symlog", linthresh=1e-3)
    axes[3].set_title("(d) Tumor nucleus dose CDF")
    axes[3].grid(alpha=0.25)
    axes[3].legend(fontsize=9, loc="lower right")

    fig.suptitle("F4 Cross-therapy comparison at matched tumor-cell dose (~2 Gy)",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_DIR / "Q2_therapy_equal_dose.png", dpi=180)
    plt.close(fig)


Q2C_PPM_LIST = [30000, 100000, 200000, 300000]


def plot_q2_b10_total_scan():
    """F5: B10 total scan (uniform-equiv ppm) — uniform vs shell at equal total atoms."""
    points_u = []
    points_s = []
    for ppm in Q2C_PPM_LIST:
        for mode, bucket in (("uniform", points_u), ("shell", points_s)):
            path = PROJECT_DIR / f"output_q2C_{mode}_{ppm}ppm.root"
            if not path.exists():
                continue
            rows = read_cell_rows(path)
            evts = read_event_rows(path)
            if not rows:
                continue
            s = cell_summary(rows)
            bucket.append({
                "ppm": ppm,
                "tumor_nuc": s["tumor"]["mean_dose_nucleus"],
                "normal_nuc": s["normal"]["mean_dose_nucleus"],
                "tumor_S": s["tumor"]["mean_S"],
                "normal_S": s["normal"]["mean_S"],
                "lethal_t": s["tumor"]["lethal_fraction"],
                "lethal_n": s["normal"]["lethal_fraction"],
                "a_li7": sum(e["n_alpha"] + e["n_li7"] for e in evts),
            })
    if not points_u or not points_s:
        print("[F5] missing q2C outputs; skipping")
        return

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))

    # (a) tumor nucleus dose vs ppm, uniform vs shell
    axes[0].plot([p["ppm"] for p in points_u], [p["tumor_nuc"] for p in points_u],
                 "o-", color="#c83f31", label="uniform")
    axes[0].plot([p["ppm"] for p in points_s], [p["tumor_nuc"] for p in points_s],
                 "s-", color="#7b3fbf", label="shell (equal total)")
    axes[0].set_xscale("log"); axes[0].set_yscale("log")
    axes[0].set_xlabel("uniform-equiv B10 ppm")
    axes[0].set_ylabel("Tumor nucleus dose (Gy)")
    axes[0].set_title("(a) Tumor nucleus dose")
    axes[0].grid(alpha=0.25, which="both")
    axes[0].legend(fontsize=9)

    # (b) shell/uniform advantage ratio
    common = sorted(set(p["ppm"] for p in points_u) & set(p["ppm"] for p in points_s))
    rate = []
    for ppm in common:
        u = next(p for p in points_u if p["ppm"] == ppm)
        s = next(p for p in points_s if p["ppm"] == ppm)
        rate.append(s["tumor_nuc"] / u["tumor_nuc"] if u["tumor_nuc"] > 0 else 0)
    axes[1].plot(common, rate, "o-", color="#222", markersize=8)
    axes[1].axhline(1.0, color="#888", linestyle="--", linewidth=0.8)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("uniform-equiv B10 ppm")
    axes[1].set_ylabel("D_nuc(shell) / D_nuc(uniform)")
    axes[1].set_title("(b) Shell / uniform advantage ratio")
    axes[1].grid(alpha=0.25, which="both")

    # (c) Survival vs ppm
    axes[2].plot([p["ppm"] for p in points_u], [p["tumor_S"] for p in points_u],
                 "o-", color="#c83f31", label="uniform tumor S")
    axes[2].plot([p["ppm"] for p in points_s], [p["tumor_S"] for p in points_s],
                 "s-", color="#7b3fbf", label="shell tumor S")
    axes[2].plot([p["ppm"] for p in points_u], [p["normal_S"] for p in points_u],
                 "o--", color="#5fa8d3", label="uniform normal S", alpha=0.7)
    axes[2].plot([p["ppm"] for p in points_s], [p["normal_S"] for p in points_s],
                 "s--", color="#5fa8d3", label="shell normal S", alpha=0.5)
    axes[2].set_xscale("log")
    axes[2].set_xlabel("uniform-equiv B10 ppm")
    axes[2].set_ylabel("LQ survival fraction S")
    axes[2].set_ylim(0, 1.05)
    axes[2].set_title("(c) Survival vs B10 total")
    axes[2].grid(alpha=0.25, which="both")
    axes[2].legend(fontsize=8)

    fig.suptitle("F5 B10 total scan (equal total atom count between uniform/shell)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_DIR / "Q2_b10_total_scan.png", dpi=180)
    plt.close(fig)


# === Q2 two-stage BNCT: real-neutron capture yield x conditional response ===

def q2d_capture_paths(mode, seeds=(1, 2, 3)):
    return [PROJECT_DIR / f"output_q2D_capture_{mode}_seed{s}.root" for s in seeds]


def forced_capture_seed_summary(path):
    run = read_run_row(path)
    if run.get("source_mode") != 1:
        raise ValueError(f"{path.name} is not a b10Capture output")
    if ROOT is None:
        return None
    frame = ROOT.RDataFrame("EventTree", str(path))
    n = int(frame.Count().GetValue())
    if n <= 0:
        return None
    highlet_frame = frame.Define(
        "forcedHighLETNucleus_MeV",
        "edepNucleusTumorAlpha_MeV + edepNucleusTumorLi7_MeV",
    )
    highlet_sum = float(highlet_frame.Sum("forcedHighLETNucleus_MeV").GetValue())
    initial_sum = float(frame.Sum("forcedInitialHighLET_MeV").GetValue())
    hit_count = int(highlet_frame.Filter("forcedHighLETNucleus_MeV > 0").Count().GetValue())
    rows = read_cell_rows(path)
    tumor_rows = [row for row in rows if row["cell_type"] == 1]
    highlet_doses = []
    for row in tumor_rows:
        total_edep = row.get("edepNucleus_MeV", 0.0)
        highlet_edep = row.get("edepNucleusAlpha_MeV", 0.0) + row.get("edepNucleusLi7_MeV", 0.0)
        highlet_doses.append(
            row["dose_nucleus"] * highlet_edep / total_edep if total_edep > 0 else 0.0
        )
    return {
        "n_captures": n,
        "mean_nucleus_highlet_mev": highlet_sum / n,
        "nucleus_hit_probability": hit_count / n,
        "nucleus_energy_fraction": highlet_sum / initial_sum if initial_sum > 0 else 0.0,
        "population_nucleus_dose_gy_per_capture": mean(highlet_doses) / n,
    }


def aggregate_q2d_capture_summary(mode):
    summaries = []
    for path in q2d_capture_paths(mode):
        if path.exists():
            summary = forced_capture_seed_summary(path)
            if summary:
                summaries.append(summary)
    return summaries


def _seed_metric(summaries, key):
    return [s[key] for s in summaries]


def plot_q2_forced_capture_main():
    """F2: conditional microdosimetry response per B10 capture."""
    uniform = aggregate_q2d_capture_summary("uniform")
    shell = aggregate_q2d_capture_summary("shell")
    if not uniform or not shell:
        print("[F2 two-stage] missing q2D forced-capture outputs; skipping")
        return

    metrics = [
        ("mean_nucleus_highlet_mev", "Nucleus high-LET edep\n(MeV / capture)"),
        ("nucleus_hit_probability", "Nucleus high-LET hit\nprobability / capture"),
        ("nucleus_energy_fraction", "Initial high-LET energy\nfraction entering nucleus"),
    ]
    colors = ["#c83f31", "#7b3fbf"]
    fig, axes = plt.subplots(1, 4, figsize=(15.5, 4.6))
    ratios = []
    ratio_errs = []
    ratio_labels = []
    for ax, (key, ylabel) in zip(axes[:3], metrics):
        u = _seed_metric(uniform, key)
        s = _seed_metric(shell, key)
        values = [_mean_std(u), _mean_std(s)]
        _bar_with_err(ax, np.arange(2), values, colors, ["uniform", "shell"],
                      ylabel, None)
        paired = [sv / uv for uv, sv in zip(u, s) if uv > 0]
        ratio, ratio_err = _mean_std(paired)
        ratios.append(ratio)
        ratio_errs.append(ratio_err)
        ratio_labels.append(ylabel.split("\n")[0])

    axes[0].set_title("(a) Nucleus energy per capture")
    axes[1].set_title("(b) Nucleus-hit probability")
    axes[2].set_title("(c) Energy-transfer efficiency")
    axes[3].bar(np.arange(3), ratios, yerr=ratio_errs, capsize=4,
                color="#333", edgecolor="#111")
    axes[3].axhline(1.0, color="#888", linestyle="--", linewidth=1)
    axes[3].set_xticks(np.arange(3))
    axes[3].set_xticklabels(ratio_labels, rotation=15, ha="right")
    axes[3].set_ylabel("shell / uniform")
    axes[3].set_title("(d) Conditional-response ratio")
    axes[3].grid(axis="y", alpha=0.25)
    fig.suptitle("F2 Conditional microdosimetry per B10 capture "
                 f"({min(len(uniform), len(shell))} seeds)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "Q2_forced_capture_main.png", dpi=180)
    plt.close(fig)


def _stack_q2d_hist(mode, hist_name, reader):
    total = None
    axes = None
    captures = 0
    for path in q2d_capture_paths(mode):
        if not path.exists():
            continue
        run = read_run_row(path)
        if run.get("source_mode") != 1:
            raise ValueError(f"{path.name} is not a b10Capture output")
        result = reader(path, hist_name)
        if result is None:
            continue
        captures += run["n_events"]
        if reader is read_h2:
            axes = (result[0], result[1])
            values = np.array(result[2], dtype=float)
        else:
            axes = result[0]
            values = np.array(result[1], dtype=float)
        total = values if total is None else total + values
    if total is None or captures <= 0:
        return None
    return axes, total / captures


def cylindrical_bin_volumes(r_edges, z_edges):
    """Exact cylindrical-ring volume for each (r_xy, z) H2 bin, in um^3."""
    ring_areas = math.pi * (np.square(r_edges[1:]) - np.square(r_edges[:-1]))
    dz = np.diff(z_edges)
    return np.outer(dz, ring_areas)


def spherical_shell_volumes(centers):
    """Exact spherical-shell volume inferred from uniform H1 bin centers, in um^3."""
    centers = np.asarray(centers, dtype=float)
    dr = centers[1] - centers[0]
    inner = np.maximum(0.0, centers - 0.5 * dr)
    outer = centers + 0.5 * dr
    return 4.0 * math.pi * (np.power(outer, 3) - np.power(inner, 3)) / 3.0


def forced_capture_region_energy(map_result):
    """Integrate raw per-capture H2 energy into nucleus/cytoplasm/outer-shell regions."""
    (r_edges, z_edges), energy = map_result
    r_centers = 0.5 * (np.asarray(r_edges[:-1]) + np.asarray(r_edges[1:]))
    z_centers = 0.5 * (np.asarray(z_edges[:-1]) + np.asarray(z_edges[1:]))
    rr, zz = np.meshgrid(r_centers, z_centers)
    radius = np.sqrt(rr * rr + zz * zz)
    return [
        float(np.sum(energy[radius < 2.5])),
        float(np.sum(energy[(radius >= 2.5) & (radius < 4.0)])),
        float(np.sum(energy[(radius >= 4.0) & (radius <= 5.0)])),
    ]


def plot_q2_forced_capture_microdose():
    """F3': volume-normalized high-LET density and regional energy balance."""
    map_u = _stack_q2d_hist("uniform", "hCellLocalTumor", read_h2)
    map_s = _stack_q2d_hist("shell", "hCellLocalTumor", read_h2)
    rad_u = _stack_q2d_hist("uniform", "hCellRadialTumor", read_h1)
    rad_s = _stack_q2d_hist("shell", "hCellRadialTumor", read_h1)
    if not all((map_u, map_s, rad_u, rad_s)):
        print("[F3 two-stage] missing q2D histograms; skipping")
        return

    x_edges, y_edges = map_u[0]
    bin_volumes = cylindrical_bin_volumes(np.asarray(x_edges), np.asarray(y_edges))
    density_u = np.divide(map_u[1], bin_volumes, out=np.zeros_like(map_u[1]), where=bin_volumes > 0)
    density_s = np.divide(map_s[1], bin_volumes, out=np.zeros_like(map_s[1]), where=bin_volumes > 0)
    radial_density_u = np.divide(rad_u[1], spherical_shell_volumes(rad_u[0]))
    radial_density_s = np.divide(rad_s[1], spherical_shell_volumes(rad_s[0]))
    region_u = forced_capture_region_energy(map_u)
    region_s = forced_capture_region_energy(map_s)

    vmax = max(float(np.max(density_u)), float(np.max(density_s)))
    positive = np.concatenate((density_u[density_u > 0], density_s[density_s > 0]))
    vmin = max(float(np.min(positive)), vmax * 1.0e-4)
    density_norm = LogNorm(vmin=vmin, vmax=vmax)
    fig = plt.figure(figsize=(13.5, 9.0))
    grid = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.28)
    map_axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    for ax, panel, title in zip(map_axes, (density_u, density_s),
                                ("uniform B10", "shell B10")):
        im = ax.pcolormesh(x_edges, y_edges, panel, cmap="inferno", norm=density_norm)
        ax.set_xlabel("r_xy (um)")
        ax.set_ylabel("z_local (um)")
        ax.set_title(title)
    cbar = fig.colorbar(im, ax=map_axes, shrink=0.85, pad=0.02)
    cbar.set_label("High-LET energy density (MeV / capture / um^3, log scale)")

    ax = fig.add_subplot(grid[1, 0])
    ax.plot(rad_u[0], radial_density_u, color="#c83f31", linewidth=2, label="uniform")
    ax.plot(rad_s[0], radial_density_s, color="#7b3fbf", linewidth=2, label="shell")
    ax.axvline(2.5, color="#4c78a8", linestyle="--", label="nucleus boundary")
    ax.axvline(4.0, color="#888", linestyle=":", label="shell start")
    ax.set_xlabel("r from cell center (um)")
    ax.set_ylabel("High-LET energy density\n(MeV / capture / um^3)")
    ax.set_title("Volume-normalized radial response")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    ax = fig.add_subplot(grid[1, 1])
    x = np.arange(3)
    width = 0.36
    ax.bar(x - width / 2, region_u, width, color="#c83f31", label="uniform")
    ax.bar(x + width / 2, region_s, width, color="#7b3fbf", label="shell")
    ax.set_xticks(x)
    ax.set_xticklabels(["nucleus\nr < 2.5", "cytoplasm\n2.5 <= r < 4", "outer shell\n4 <= r <= 5"])
    ax.set_ylabel("High-LET edep (MeV / capture)")
    ax.set_title("Regional energy balance")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()

    fig.suptitle("F3' Volume-corrected conditional high-LET microdosimetry", fontsize=12)
    fig.savefig(FIG_DIR / "Q2_forced_capture_microdose.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def fit_capture_yield_per_ppm(mode, scan_points):
    """Poisson MLE for capture_yield = slope * uniform-equiv ppm.

    The fit pools sparse q2C points and the three 300k-ppm q2A neutron runs.
    """
    total_captures = sum(p["captures"] for p in scan_points)
    exposure = sum(p["ppm"] * p["n_events"] for p in scan_points)
    for path in q2a_paths(mode):
        if not path.exists() or ROOT is None:
            continue
        frame = ROOT.RDataFrame("EventTree", str(path))
        n_events = int(frame.Count().GetValue())
        total_captures += int(frame.Sum("nLi7").GetValue())
        exposure += Q2A_UNIFORM_PPM_DEFAULT * n_events
    if exposure <= 0 or total_captures <= 0:
        return 0.0, 0.0, total_captures
    slope = total_captures / exposure
    slope_std = math.sqrt(total_captures) / exposure
    return slope, slope_std, total_captures


def plot_q2_two_stage_b10_scan():
    """F5: real-neutron capture yield multiplied by conditional nucleus response."""
    forced = {}
    for mode in ("uniform", "shell"):
        summaries = aggregate_q2d_capture_summary(mode)
        if not summaries:
            print("[F5 two-stage] missing q2D outputs; skipping")
            return
        forced[mode] = _mean_std(_seed_metric(summaries, "population_nucleus_dose_gy_per_capture"))

    points = {"uniform": [], "shell": []}
    for ppm in Q2C_PPM_LIST:
        for mode in ("uniform", "shell"):
            path = PROJECT_DIR / f"output_q2C_{mode}_{ppm}ppm.root"
            if not path.exists() or ROOT is None:
                continue
            frame = ROOT.RDataFrame("EventTree", str(path))
            n_events = int(frame.Count().GetValue())
            if n_events <= 0:
                continue
            captures = int(frame.Sum("nLi7").GetValue())
            capture_yield = captures / n_events
            response, response_std = forced[mode]
            points[mode].append({
                "ppm": ppm,
                "captures": captures,
                "n_events": n_events,
                "yield": capture_yield,
            })
            if captures < 100:
                print(f"[F5 two-stage] warning: {mode} {ppm} ppm has only {captures} Li7 captures")
    if any(not points[m] for m in points):
        print("[F5 two-stage] missing q2C capture-yield inputs; skipping")
        return

    fits = {}
    for mode in ("uniform", "shell"):
        slope, slope_std, pooled_captures = fit_capture_yield_per_ppm(mode, points[mode])
        fits[mode] = (slope, slope_std)
        response, response_std = forced[mode]
        for point in points[mode]:
            fitted_yield = slope * point["ppm"]
            fitted_yield_std = slope_std * point["ppm"]
            point["fitted_yield"] = fitted_yield
            point["predicted"] = fitted_yield * response
            rel_yield = fitted_yield_std / fitted_yield if fitted_yield > 0 else 0.0
            rel_response = response_std / response if response > 0 else 0.0
            point["predicted_err"] = point["predicted"] * math.sqrt(
                rel_yield * rel_yield + rel_response * rel_response
            )
        print(f"[F5 two-stage] {mode} pooled real-neutron Li7 captures: {pooled_captures}")

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6))
    styles = {"uniform": ("o-", "#c83f31"), "shell": ("s-", "#7b3fbf")}
    for mode in ("uniform", "shell"):
        style, color = styles[mode]
        xs = [p["ppm"] for p in points[mode]]
        axes[0].errorbar(xs, [p["predicted"] for p in points[mode]],
                         yerr=[p["predicted_err"] for p in points[mode]],
                         fmt=style, color=color, capsize=3, label=mode)
        positive = [p for p in points[mode] if p["yield"] > 0]
        axes[2].scatter([p["ppm"] for p in positive], [p["yield"] for p in positive],
                        color=color, marker=style[0], alpha=0.55, label=f"{mode} raw")
        axes[2].plot(xs, [p["fitted_yield"] for p in points[mode]], "-",
                     color=color, label=f"{mode} pooled fit")
    axes[0].set_xscale("log"); axes[0].set_yscale("log")
    axes[0].set_xlabel("uniform-equiv B10 ppm")
    axes[0].set_ylabel("Predicted tumor nucleus dose\n(Gy / incident neutron)")
    axes[0].set_title("(a) Two-stage nucleus dose")
    axes[0].legend()

    common = sorted(set(p["ppm"] for p in points["uniform"]) &
                    set(p["ppm"] for p in points["shell"]))
    ratios = []
    for ppm in common:
        u = next(p for p in points["uniform"] if p["ppm"] == ppm)["predicted"]
        s = next(p for p in points["shell"] if p["ppm"] == ppm)["predicted"]
        ratios.append(s / u if u > 0 else float("nan"))
    axes[1].plot(common, ratios, "o-", color="#222")
    axes[1].axhline(1.0, color="#888", linestyle="--")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("uniform-equiv B10 ppm")
    axes[1].set_ylabel("shell / uniform predicted dose")
    axes[1].set_title("(b) Two-stage response ratio")

    axes[2].set_xscale("log"); axes[2].set_yscale("log")
    axes[2].set_xlabel("uniform-equiv B10 ppm")
    axes[2].set_ylabel("Li7 captures / incident neutron")
    axes[2].set_title("(c) Real-neutron capture yield + pooled fit")
    axes[2].legend()
    for ax in axes:
        ax.grid(alpha=0.25, which="both")
    fig.suptitle("F5 Two-stage BNCT: real capture yield x conditional microdosimetry", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "Q2_two_stage_b10_scan.png", dpi=180)
    plt.close(fig)


def main():
    args = parse_args()
    require_root_when_outputs_exist()
    if args.section in ("all", "q1"):
        plot_q1_depth_dose()
        plot_q1_dose_heatmap()
        plot_q1_proton_energy_heatmap_grid()
        plot_q1_gamma_energy_heatmap_grid()
        plot_q1_proton_energy_scan()
        plot_q1_gamma_energy_scan()
        plot_q1_region_dose()
        plot_q1_let_spectra()
    if args.section in ("all", "q2"):
        plot_q2_boron_cell_model()
        plot_q2_mixed_geometry_layout()
        plot_q2_micro_dose_map()
        plot_q2_nucleus_dose_scatter()
        plot_q2_secondary_yield()
        plot_q2_cell_dose_spectra()
        plot_q2_therapy_comparison_projected_maps()
        plot_q2_b10_concentration_scan()
        plot_q2_neutron_fluence_scan()
        plot_q2_neutron_fluence_projected_maps()
        plot_q2_boron_distribution()
    if args.section in ("all", "q2", "q2new"):
        plot_q2_forced_capture_main()
        plot_q2_forced_capture_microdose()
        plot_q2_two_stage_b10_scan()


if __name__ == "__main__":
    main()
