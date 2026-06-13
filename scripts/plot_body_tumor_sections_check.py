#!/usr/bin/env python3
"""Draw x-z and y-z sections for checking the agreed tumor coordinates."""

import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig-g4sim")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_DIR / "figures" / "body_tumor_xz_yz_check.png"

TUMOR_CENTER = (0.0, -80.0, 0.0)
TUMOR_SIZE = (10.0, 20.0, 30.0)

TORSO_X = (-60.0, 60.0)
TORSO_Y = (-130.0, 130.0)
TORSO_Z = (-250.0, 250.0)

BODY_FACE = "#a9cfb3"
BODY_EDGE = "#285b40"
TUMOR_FACE = "#d94d3d"
TUMOR_EDGE = "#941f16"
BEAM_COLOR = "#2c5ca8"


def add_tumor(ax, horizontal_min, vertical_min, width, height):
    ax.add_patch(Rectangle(
        (horizontal_min, vertical_min),
        width,
        height,
        facecolor=TUMOR_FACE,
        edgecolor=TUMOR_EDGE,
        linewidth=2.0,
        label="Tumor region",
        zorder=5,
    ))
    ax.plot(
        horizontal_min + width / 2,
        vertical_min + height / 2,
        marker="x",
        color="black",
        markersize=8,
        markeredgewidth=2,
        zorder=6,
    )


def add_xz_body(ax):
    ax.add_patch(Rectangle(
        (TORSO_X[0], TORSO_Z[0]),
        TORSO_X[1] - TORSO_X[0],
        TORSO_Z[1] - TORSO_Z[0],
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
        label="Water-equivalent body",
    ))

    neck_top = [
        (x, 430.0 - math.sqrt(90.0**2 - x**2))
        for x in range(50, -51, -2)
    ]
    ax.add_patch(Polygon(
        [(-50.0, 250.0), (50.0, 250.0), *neck_top],
        closed=True,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
    ))
    ax.add_patch(Circle(
        (0.0, 430.0),
        90.0,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
    ))
    ax.add_patch(Rectangle(
        (-55.0, -1070.0),
        110.0,
        820.0,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
    ))


def add_yz_body(ax):
    ax.add_patch(Rectangle(
        (TORSO_Y[0], TORSO_Z[0]),
        TORSO_Y[1] - TORSO_Y[0],
        TORSO_Z[1] - TORSO_Z[0],
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
        label="Water-equivalent body",
    ))
    neck_top = [
        (y, 430.0 - math.sqrt(90.0**2 - y**2))
        for y in range(50, -51, -2)
    ]
    ax.add_patch(Polygon(
        [(-50.0, 250.0), (50.0, 250.0), *neck_top],
        closed=True,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
    ))
    ax.add_patch(Circle(
        (0.0, 430.0),
        90.0,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
    ))
    for center_y in (-65.0, 65.0):
        ax.add_patch(Rectangle(
            (center_y - 55.0, -1070.0),
            110.0,
            820.0,
            facecolor=BODY_FACE,
            edgecolor=BODY_EDGE,
            linewidth=1.7,
        ))


def style_axis(ax, xlabel):
    ax.set_xlabel(xlabel)
    ax.set_ylabel("z (mm), body height")
    ax.set_facecolor("#f4f6f7")
    ax.grid(color="white", linewidth=0.8, alpha=0.9)
    ax.spines[["top", "right"]].set_visible(False)


def draw_xz(ax):
    add_xz_body(ax)
    add_tumor(
        ax,
        TUMOR_CENTER[0] - TUMOR_SIZE[0] / 2,
        TUMOR_CENTER[2] - TUMOR_SIZE[2] / 2,
        TUMOR_SIZE[0],
        TUMOR_SIZE[2],
    )

    ax.annotate(
        "",
        xy=(0, TORSO_Z[1]),
        xytext=(0, TUMOR_CENTER[2]),
        arrowprops={"arrowstyle": "<->", "color": BEAM_COLOR, "lw": 2.0},
        zorder=7,
    )
    ax.text(12, 125, "25 cm", color=BEAM_COLOR, fontsize=11, fontweight="bold", va="center")
    ax.text(13, -25, "Tumor center\nx = 0, z = 0 mm", fontsize=8.5, color="#222222")
    ax.axvline(0, color="#555555", linestyle=":", linewidth=1.1)

    ax.set_title("x-z depth section at tumor position y = -80 mm")
    ax.set_xlim(-95, 95)
    ax.set_ylim(-1120, 550)
    ax.set_aspect("equal", adjustable="box")
    style_axis(ax, "x (mm), body depth")


def draw_yz(ax):
    add_yz_body(ax)
    add_tumor(
        ax,
        TUMOR_CENTER[1] - TUMOR_SIZE[1] / 2,
        TUMOR_CENTER[2] - TUMOR_SIZE[2] / 2,
        TUMOR_SIZE[1],
        TUMOR_SIZE[2],
    )

    ax.plot(
        [TORSO_Y[0], TORSO_Y[0]],
        [TORSO_Z[0], TORSO_Z[1]],
        color=BODY_EDGE,
        linestyle="--",
        linewidth=1.3,
    )
    ax.annotate(
        "",
        xy=(TUMOR_CENTER[1], 0),
        xytext=(TORSO_Y[0], 0),
        arrowprops={"arrowstyle": "<->", "color": "#111111", "lw": 2.0},
        zorder=7,
    )
    ax.text(-105, 8, "5 cm", ha="center", fontsize=11, fontweight="bold")
    ax.text(-72, -40, "Tumor center\ny = -80, z = 0 mm", fontsize=8.5, color="#222222")

    ax.annotate(
        "Beam direction (+y)",
        xy=(TORSO_Y[0], 55),
        xytext=(-195, 55),
        arrowprops={"arrowstyle": "-|>", "color": BEAM_COLOR, "lw": 2.1},
        color=BEAM_COLOR,
        va="center",
        fontsize=10,
    )
    ax.text(
        -128,
        230,
        "Entrance surface\ny = -130 mm",
        color=BODY_EDGE,
        fontsize=8.5,
    )

    ax.set_title("y-z front section at body depth center x = 0 mm")
    ax.set_xlim(-160, 215)
    ax.set_ylim(-290, 550)
    ax.set_aspect("equal", adjustable="box")
    style_axis(ax, "y (mm), body width / beam direction")


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(11.5, 8.0),
        gridspec_kw={"width_ratios": [0.95, 1.05]},
    )
    draw_xz(axes[0])
    draw_yz(axes[1])

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle(
        "Body and tumor coordinate check",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.5,
        0.945,
        "Tumor center (x, y, z) = (0, -80, 0) mm | size = 10 x 20 x 30 mm",
        ha="center",
        fontsize=10,
        color="#333333",
    )
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.10, top=0.89, wspace=0.20)
    fig.savefig(OUTPUT, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
