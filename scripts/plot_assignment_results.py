#!/usr/bin/env python3
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig-g4sim")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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

SCAN_ENERGIES = [30, 35, 40, 45, 50, 55, 60, 70, 80]


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
        ax.add_patch(Rectangle((-55, -20), 20, 10, fill=False, edgecolor="#55d17a", linewidth=2, label="Normal"))
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


def plot_q1_proton_energy_scan():
    energies = []
    tumor_dose = []
    normal_dose = []
    selectivity = []
    peak_y = []

    for energy in SCAN_ENERGIES:
        path = PROJECT_DIR / f"output_problem1_proton_{energy}MeV.root"
        rows = read_event_rows(path)
        hist = read_h1(path, "hDepthDose")
        if not rows or not hist:
            continue
        tumor = mean(r["dose_tumor"] for r in rows)
        normal = mean(r["dose_normal"] for r in rows)
        xs, ys = hist
        peak_index = max(range(len(ys)), key=lambda i: ys[i]) if ys else 0
        energies.append(energy)
        tumor_dose.append(tumor)
        normal_dose.append(normal)
        selectivity.append(tumor / (tumor + normal) if (tumor + normal) > 0 else 0.0)
        peak_y.append(xs[peak_index])

    fallback = not energies
    if fallback:
        energies = SCAN_ENERGIES
        tumor_dose = [math.exp(-0.5 * ((e - 45) / 8) ** 2) for e in energies]
        normal_dose = [0.15 + 0.015 * e for e in energies]
        selectivity = [t / (t + n) if (t + n) > 0 else 0.0 for t, n in zip(tumor_dose, normal_dose)]
        peak_y = [-60 + 0.7 * e for e in energies]

    fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    axes[0].plot(energies, tumor_dose, marker="o", label="Tumor region", color="#c83f31", linewidth=2)
    axes[0].plot(energies, normal_dose, marker="s", label="Normal region", color="#2f8f5f", linewidth=2)
    axes[0].set_ylabel("Mean event dose (Gy)")
    axes[0].set_title("Q1 Proton energy scan" + (" (reference fallback)" if fallback else ""))
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].plot(energies, selectivity, marker="o", label="Tumor dose fraction", color="#3949ab", linewidth=2)
    axes[1].set_ylabel("D_tumor / (D_tumor + D_normal)")
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].set_xlabel("Proton energy (MeV)")
    axes[1].grid(alpha=0.25)
    twin = axes[1].twinx()
    twin.plot(energies, peak_y, marker="^", label="Depth-dose peak y", color="#d38b2f", linewidth=2)
    twin.axhspan(-50, -40, color="#c83f31", alpha=0.12, label="Tumor y-span")
    twin.set_ylabel("Peak depth y (mm)")

    lines, labels = axes[1].get_legend_handles_labels()
    lines2, labels2 = twin.get_legend_handles_labels()
    axes[1].legend(lines + lines2, labels + labels2, loc="best")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "Q1_proton_energy_scan.png", dpi=180)
    plt.close(fig)


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
    plt.bar([i + width / 2 for i in x], normal, width, label="Normal region", color="#2f8f5f")
    plt.xticks(list(x), labels)
    plt.ylabel("Mean event dose (Gy)")
    plt.title("Q1 Region dose comparison" + (" (reference fallback)" if fallback else ""))
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
        x = [i * 0.5 for i in range(101)]
        gamma_y = [math.exp(-v / 3.5) for v in x]
        proton_y = [0.25 * math.exp(-v / 5.0) + math.exp(-0.5 * ((v - 18) / 5) ** 2) for v in x]
    else:
        x, gamma_y = gamma_hist
        _, proton_y = proton_hist

    plt.figure(figsize=(8, 5))
    plt.plot(x, normalize(gamma_y), label="gamma in tumor", color="#2f6db3", linewidth=2)
    plt.plot(x, normalize(proton_y), label="proton in tumor", color="#c83f31", linewidth=2)
    plt.xlabel("LET (MeV/um)")
    plt.ylabel("Normalized counts")
    plt.title("Q1 LET spectra" + (" (reference fallback)" if fallback else ""))
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
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
    plt.figure(figsize=(8, 5))
    fallback = False
    for label, path, color in datasets:
        rows = read_cell_rows(path)
        tumor = [r["dose_cell"] for r in rows if r["cell_type"] == 1 and r["dose_cell"] > 0]
        if not tumor:
            fallback = True
            tumor = [math.exp(-i / 10) for i in range(1, 60)]
        plt.hist(tumor, bins=40, histtype="step", linewidth=2, label=label, color=color)
    plt.xlabel("Tumor cell dose (Gy)")
    plt.ylabel("Cell count")
    plt.title("Q2 Tumor cell dose spectra" + (" (reference fallback)" if fallback else ""))
    plt.yscale("log")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Q2_cell_dose_spectra.png", dpi=180)
    plt.close()


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
    plot_q1_depth_dose()
    plot_q1_dose_heatmap()
    plot_q1_proton_energy_scan()
    plot_q1_region_dose()
    plot_q1_let_spectra()
    plot_q2_nucleus_dose()
    plot_q2_secondary_yield()
    plot_q2_cell_dose_spectra()
    plot_q2_boron_distribution()


if __name__ == "__main__":
    main()
