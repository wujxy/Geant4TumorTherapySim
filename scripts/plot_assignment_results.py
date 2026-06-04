#!/usr/bin/env python3
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
from matplotlib.patches import Circle, Rectangle

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
    "bnct_uniform": PROJECT_DIR / "output_problem2_bnct_uniform.root",
    "bnct_shell": PROJECT_DIR / "output_problem2_bnct_shell.root",
}

PROTON_SCAN_ENERGIES = [30, 35, 40, 45, 50, 55, 60, 70, 80]
GAMMA_SCAN_ENERGIES = [0.2, 0.5, 1, 2, 4, 6, 8, 10, 15]
SCAN_ENERGIES = PROTON_SCAN_ENERGIES
B10_SCAN_PPM = [1000, 3000, 10000, 30000, 100000, 300000, 500000]
Q2_BORON_MODES = ["uniform", "shell"]
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
        rows.append({
            "dose_tumor": float(entry.doseTumorRegion_Gy),
            "dose_normal": float(entry.doseNormalRegion_Gy),
            "edep_tumor": float(entry.edepTumorRegion_MeV),
            "edep_normal": float(entry.edepNormalRegion_MeV),
            "n_alpha": int(entry.nAlpha),
            "n_li7": int(entry.nLi7),
            "n_gamma": int(entry.nGamma),
            "n_electron": int(entry.nElectron),
        })
    handle.Close()
    return rows


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
        rows.append({
            "cell_type": int(entry.cellType),
            "x_mm": float(entry.x_mm),
            "y_mm": float(entry.y_mm),
            "z_mm": float(entry.z_mm),
            "dose_cell": float(entry.doseCell_Gy),
            "dose_nucleus": float(entry.doseNucleus_Gy),
            "dose_boron": float(entry.doseBoronRegion_Gy),
            "alpha_hits": int(entry.alphaHits),
            "li_hits": int(entry.liHits),
        })
    handle.Close()
    return rows


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def dose_localization_fraction(tumor_dose, normal_dose):
    total = tumor_dose + normal_dose
    return tumor_dose / total if total > 0 else 0.0


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
    depth = [x for x in range(-80, 61, 2)]
    gamma = [math.exp(-0.012 * (x + 80)) * (1.0 + 0.05 * math.sin(x / 9)) for x in depth]
    proton = [0.18 + 2.6 * math.exp(-0.5 * ((x + 45) / 8.0) ** 2) for x in depth]
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
        ax.plot(x, proton_norm, label="proton 45 MeV", color="#c83f31", linewidth=2)
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

    body_ax.set_xlim(-80, 80)
    body_ax.axvspan(-80, -60, color="#d7ecff", alpha=0.32, label="air range")
    body_ax.axvspan(-60, 60, color="#e8e8e8", alpha=0.28, label="human range")
    body_ax.axvspan(60, 80, color="#d7ecff", alpha=0.32)
    body_ax.axvspan(-50, -40, color="#c83f31", alpha=0.12, label="tumor y-span")
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
    fig.text(0.41, 0.03, "Air path between y=-580 mm and y=-80 mm is omitted; deposition there is negligible.",
             ha="center", fontsize=9, color="#444444")
    fig.subplots_adjust(bottom=0.17, top=0.88)
    fig.savefig(FIG_DIR / "Q1_depth_dose.png", dpi=180)
    plt.close(fig)


def plot_q1_dose_heatmap():
    maps = [
        ("gamma 1 MeV", ROOT_FILES["gamma"]),
        ("proton 45 MeV", ROOT_FILES["proton"]),
    ]
    panels = []
    fallback = False
    for label, path in maps:
        heatmap = read_h3_xy(path, "hVoxelDose3D")
        if heatmap is None:
            fallback = True
            xs = [x for x in range(-80, 81, 4)]
            ys = [y for y in range(-80, 21, 3)]
            grid = []
            for y in ys:
                row = []
                for x in xs:
                    beam = math.exp(-0.5 * ((x + 45) / 7.5) ** 2)
                    if "proton" in label:
                        depth = 0.2 + 2.3 * math.exp(-0.5 * ((y + 45) / 5.0) ** 2)
                    else:
                        depth = math.exp(-0.015 * (y + 60))
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
        ax.add_patch(Rectangle((-130, -60), 260, 120, fill=False, edgecolor="white",
                               linestyle="--", linewidth=1.8, label="Human torso"))
        ax.add_patch(Rectangle((-55, -50), 20, 10, fill=False, edgecolor="#5dd3ff", linewidth=2, label="Tumor"))
        ax.annotate("", xy=(-45, -55), xytext=(-45, -75),
                    arrowprops={"arrowstyle": "->", "color": "white", "lw": 1.8})
        ax.text(-42, -72, "+y beam", color="white", fontsize=9, va="center")
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
    ys = [y for y in range(-80, 81, 4)]
    grid = []
    for y in ys:
        row = []
        for x in xs:
            beam = math.exp(-0.5 * ((x + 45) / 7.5) ** 2)
            if particle == "proton":
                peak = -60 + 0.7 * energy
                depth = 0.15 + 2.3 * math.exp(-0.5 * ((y - peak) / 5.0) ** 2)
            else:
                attenuation = 0.008 / max(math.sqrt(energy), 0.45)
                buildup = 1.0 - math.exp(-0.12 * max(y + 60, 0.0))
                depth = (0.35 + buildup) * math.exp(-attenuation * max(y + 60, 0.0))
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
        ax.add_patch(Rectangle((-130, -60), 260, 120, fill=False, edgecolor="white",
                               linestyle="--", linewidth=1.2))
        ax.add_patch(Rectangle((-55, -50), 20, 10, fill=False, edgecolor="#5dd3ff", linewidth=1.8))
        ax.annotate("", xy=(-45, -55), xytext=(-45, -75),
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
            tumor_dose = [math.exp(-0.5 * ((e - 45) / 8) ** 2) for e in energies]
            normal_dose = [0.15 + 0.015 * e for e in energies]
            depth_metric = [-60 + 0.7 * e for e in energies]
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
    depth_label = "Dose-weighted mean y" if particle == "gamma" else "Depth-dose peak y"
    twin.plot(energies, depth_metric, marker="^", label=depth_label, color="#d38b2f", linewidth=2)
    twin.axhspan(-50, -40, color="#c83f31", alpha=0.12, label="Tumor y-span")
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
    reaction_yield = sum(row["n_alpha"] + row["n_li7"] for row in event_rows)
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


def projected_columns(rows):
    if not rows:
        return []
    columns = {}
    for row in rows:
        x_um = round((row["x_mm"] + 45.0) * 1000.0, 3)
        z_um = round((row["z_mm"] - 30.0) * 1000.0, 3)
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
    axes[1, 0].set_ylabel("alpha + Li7 count")
    axes[1, 0].set_title("BNCT charged-particle yield")
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
    axes[1, 1].set_ylabel("alpha + Li7 count")
    axes[1, 1].set_title("BNCT charged-particle yield")
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
        ("Uniform B10", ROOT_FILES["bnct_uniform"]),
        ("Outer shell B10", ROOT_FILES["bnct_shell"]),
    ]
    def panel_metrics(rows):
        tumor = [row for row in rows if row["cell_type"] == 1]
        normal = [row for row in rows if row["cell_type"] == 0]
        tumor_cell = mean(row["dose_cell"] for row in tumor)
        normal_cell = mean(row["dose_cell"] for row in normal)
        tumor_nucleus = mean(row["dose_nucleus"] for row in tumor)
        normal_nucleus = mean(row["dose_nucleus"] for row in normal)
        ratio = tumor_cell / normal_cell if normal_cell > 0 else 0.0
        return tumor_cell, normal_cell, tumor_nucleus, normal_nucleus, ratio

    all_columns = []
    for _, path in datasets:
        all_columns.extend(projected_columns(read_cell_rows(path)))
    max_dose = max((r["dose"] for r in all_columns), default=0.0)
    if max_dose <= 0:
        max_dose = 1.0

    fig = plt.figure(figsize=(11.4, 7.0), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[4.2, 1.35], hspace=0.08, wspace=0.08)
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    bar_axes = [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    image = None
    for ax, bar_ax, (title, path) in zip(axes, bar_axes, datasets):
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
        tumor_cell, normal_cell, tumor_nucleus, normal_nucleus, ratio = panel_metrics(rows)
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
        bar_values = [max(tumor_cell, 1.e-16), max(normal_cell, 1.e-16)]
        bar_ax.bar(["Cancer", "Normal"], bar_values, color=["#c83f31", "#2f8f5f"], width=0.58)
        bar_ax.set_yscale("log")
        bar_ax.set_ylim(min(bar_values) * 0.55, max(bar_values) * 2.8)
        bar_ax.set_ylabel("Mean cell dose\n(Gy)")
        bar_ax.set_title(f"Mean cell dose, ratio={ratio:.1f}x", fontsize=10, pad=10)
        bar_ax.grid(axis="y", alpha=0.25)
        for index, value in enumerate(bar_values):
            bar_ax.text(index, value * 1.15, f"{value:.2e}", ha="center", va="bottom", fontsize=8)
        bar_ax.text(0.98, 0.95,
                    f"Mean nucleus\nCancer {tumor_nucleus:.2e} Gy\nNormal {normal_nucleus:.2e} Gy",
                    transform=bar_ax.transAxes, ha="right", va="top", fontsize=8,
                    bbox={"boxstyle": "round,pad=0.25", "facecolor": "white",
                          "edgecolor": "#777777", "alpha": 0.85})
    axes[0].set_ylabel("z relative to tumor center (um)")
    axes[1].legend(loc="upper right")
    axes[1].tick_params(labelleft=False)
    fig.suptitle("Q2 Representative tumor micro-region projected dose map")
    fig.colorbar(image, ax=axes, label="Projected cell dose summed over y (Gy)", fraction=0.035, pad=0.02)
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
                rows.append({"x_mm": -45.0 + x / 1000.0, "z_mm": 30.0 + z / 1000.0,
                             "cell_type": 1 if (ix + iz) % 2 == 0 else 0})

    xs = [(r["x_mm"] + 45.0) * 1000.0 for r in rows]
    zs = [(r["z_mm"] - 30.0) * 1000.0 for r in rows]
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


def main():
    require_root_when_outputs_exist()
    plot_q1_depth_dose()
    plot_q1_dose_heatmap()
    plot_q1_proton_energy_heatmap_grid()
    plot_q1_gamma_energy_heatmap_grid()
    plot_q1_proton_energy_scan()
    plot_q1_gamma_energy_scan()
    plot_q1_region_dose()
    plot_q1_let_spectra()
    plot_q2_boron_cell_model()
    plot_q2_mixed_geometry_layout()
    plot_q2_micro_dose_map()
    plot_q2_nucleus_dose_scatter()
    plot_q2_secondary_yield()
    plot_q2_cell_dose_spectra()
    plot_q2_b10_concentration_scan()
    plot_q2_neutron_fluence_scan()
    plot_q2_neutron_fluence_projected_maps()
    plot_q2_boron_distribution()


if __name__ == "__main__":
    main()
