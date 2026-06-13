#!/usr/bin/env python3
"""Draw the current Geant4 human phantom and Q1 tumor geometry."""

import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig-g4sim")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_DIR / "figures" / "Q1_body_tumor_xz_section.png"

TUMOR_CENTER = (0.0, -80.0, 0.0)
TUMOR_SIZE = (10.0, 20.0, 30.0)
BEAM_Z = TUMOR_CENTER[2]

TORSO_X = (-60.0, 60.0)
TORSO_Y = (-130.0, 130.0)
TORSO_Z = (-250.0, 250.0)
HEAD_RADIUS = 90.0
HEAD_CENTER_Z = 430.0
NECK_RADIUS = 50.0
NECK_BOTTOM_Z = 250.0
LEG_RADIUS = 55.0
LEG_CENTER_Z = -660.0
LEG_HALF_HEIGHT = 410.0
LEG_CENTERS_Y = (-65.0, 65.0)

BODY_FACE = "#b8d9c0"
BODY_EDGE = "#285b40"
TUMOR_FACE = "#dc5546"
TUMOR_EDGE = "#97251b"
BEAM_COLOR = "#2c5ca8"
DIM_COLOR = "#222222"


def add_box(ax, xy, width, height, label=None, zorder=1):
    ax.add_patch(Rectangle(
        xy,
        width,
        height,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.6,
        label=label,
        zorder=zorder,
    ))


def add_neck_projection(ax):
    arc = [
        (coordinate, HEAD_CENTER_Z - math.sqrt(HEAD_RADIUS**2 - coordinate**2))
        for coordinate in range(int(NECK_RADIUS), -int(NECK_RADIUS) - 1, -2)
    ]
    ax.add_patch(Polygon(
        [(-NECK_RADIUS, NECK_BOTTOM_Z), (NECK_RADIUS, NECK_BOTTOM_Z), *arc],
        closed=True,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.6,
        zorder=2,
    ))


def add_head(ax):
    ax.add_patch(Circle(
        (0.0, HEAD_CENTER_Z),
        HEAD_RADIUS,
        facecolor=BODY_FACE,
        edgecolor=BODY_EDGE,
        linewidth=1.7,
        zorder=3,
    ))


def add_tumor(ax, horizontal_center, horizontal_size, annotate=True):
    x0 = horizontal_center - horizontal_size / 2
    z0 = TUMOR_CENTER[2] - TUMOR_SIZE[2] / 2
    ax.add_patch(Rectangle(
        (x0, z0),
        horizontal_size,
        TUMOR_SIZE[2],
        facecolor=TUMOR_FACE,
        edgecolor=TUMOR_EDGE,
        linewidth=1.8,
        label="Tumor region",
        zorder=8,
    ))
    ax.plot(
        horizontal_center,
        TUMOR_CENTER[2],
        marker="x",
        color="black",
        markersize=6.5,
        markeredgewidth=1.8,
        zorder=9,
    )
    if annotate:
        ax.annotate(
            "tumor",
            xy=(horizontal_center, TUMOR_CENTER[2]),
            xytext=(horizontal_center + 24, TUMOR_CENTER[2] + 38),
            arrowprops={"arrowstyle": "->", "color": TUMOR_EDGE, "lw": 1.2},
            color=TUMOR_EDGE,
            fontsize=8,
            zorder=10,
        )


def add_top_distance(ax, arrow_x, label_x):
    ax.annotate(
        "",
        xy=(arrow_x, TORSO_Z[1]),
        xytext=(arrow_x, TUMOR_CENTER[2]),
        arrowprops={"arrowstyle": "<->", "color": DIM_COLOR, "lw": 1.5},
        zorder=10,
    )
    ax.text(label_x, 125, "25 cm", fontsize=8, fontweight="bold", va="center")


def style_full_body_axis(ax, xlabel):
    ax.set_xlim(auto=True)
    ax.set_ylim(-1110, 545)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_ylabel("z (mm)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_facecolor("#f5f7f8")
    ax.grid(color="white", linewidth=0.7, alpha=0.95)
    ax.spines[["top", "right"]].set_visible(False)


def draw_front_view(ax):
    add_box(
        ax,
        (TORSO_Y[0], TORSO_Z[0]),
        TORSO_Y[1] - TORSO_Y[0],
        TORSO_Z[1] - TORSO_Z[0],
        label="Water-equivalent body",
    )
    add_neck_projection(ax)
    add_head(ax)
    for center_y in LEG_CENTERS_Y:
        add_box(
            ax,
            (center_y - LEG_RADIUS, LEG_CENTER_Z - LEG_HALF_HEIGHT),
            2 * LEG_RADIUS,
            2 * LEG_HALF_HEIGHT,
        )
    add_tumor(ax, TUMOR_CENTER[1], TUMOR_SIZE[1])
    add_top_distance(ax, 105, 112)
    ax.annotate(
        "+y beam",
        xy=(TUMOR_CENTER[1] - TUMOR_SIZE[1] / 2, BEAM_Z),
        xytext=(-205, BEAM_Z),
        arrowprops={"arrowstyle": "-|>", "color": BEAM_COLOR, "lw": 1.8},
        color=BEAM_COLOR,
        fontsize=8,
        va="center",
    )
    ax.set_xlim(-215, 155)
    ax.set_title("(a) Front view\n$y$-$z$ projection", fontsize=10, fontweight="bold")
    style_full_body_axis(ax, "y (mm)")


def draw_side_view(ax):
    add_box(
        ax,
        (TORSO_X[0], TORSO_Z[0]),
        TORSO_X[1] - TORSO_X[0],
        TORSO_Z[1] - TORSO_Z[0],
        label="Water-equivalent body",
    )
    add_neck_projection(ax)
    add_head(ax)
    add_box(
        ax,
        (-LEG_RADIUS, LEG_CENTER_Z - LEG_HALF_HEIGHT),
        2 * LEG_RADIUS,
        2 * LEG_HALF_HEIGHT,
    )
    add_tumor(ax, TUMOR_CENTER[0], TUMOR_SIZE[0])
    add_top_distance(ax, 42, 49)
    ax.axvline(0, color="#666666", linestyle=":", linewidth=1.0)
    ax.set_xlim(-105, 105)
    ax.set_title("(b) Side view\n$x$-$z$ projection", fontsize=10, fontweight="bold")
    style_full_body_axis(ax, "x (mm)")


def draw_tumor_detail(ax):
    add_box(
        ax,
        (TORSO_Y[0], -75),
        TORSO_Y[1] - TORSO_Y[0],
        150,
        label="Water-equivalent body",
    )
    add_tumor(ax, TUMOR_CENTER[1], TUMOR_SIZE[1], annotate=False)

    entrance_y = TORSO_Y[0]
    tumor_y = TUMOR_CENTER[1]
    ax.annotate(
        "",
        xy=(tumor_y, 36),
        xytext=(entrance_y, 36),
        arrowprops={"arrowstyle": "<->", "color": DIM_COLOR, "lw": 1.6},
    )
    ax.text((entrance_y + tumor_y) / 2, 42, "50 mm", ha="center", fontsize=8, fontweight="bold")
    ax.axvline(entrance_y, color=BODY_EDGE, linestyle="--", linewidth=1.1)
    ax.text(entrance_y + 3, 59, "entrance surface", color=BODY_EDGE, fontsize=7.5)

    ax.annotate(
        "+y beam",
        xy=(TUMOR_CENTER[1] - TUMOR_SIZE[1] / 2, BEAM_Z),
        xytext=(-158, BEAM_Z),
        arrowprops={"arrowstyle": "-|>", "color": BEAM_COLOR, "lw": 1.8},
        color=BEAM_COLOR,
        fontsize=8,
        va="center",
    )
    ax.text(
        -122,
        -66,
        "center: (0, -80, 0) mm\nsize: 10 x 20 x 30 mm",
        fontsize=7.5,
        color="#222222",
    )
    ax.set_xlim(-165, -40)
    ax.set_ylim(-75, 75)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("y (mm)", fontsize=8)
    ax.set_ylabel("z (mm)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_facecolor("#f5f7f8")
    ax.grid(color="white", linewidth=0.7, alpha=0.95)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("(c) Tumor-region detail\n$y$-$z$ section", fontsize=10, fontweight="bold")


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(9.6, 7.5),
        gridspec_kw={"width_ratios": [0.37, 0.23, 0.62], "wspace": 0.08},
    )
    draw_front_view(axes[0])
    draw_side_view(axes[1])
    draw_tumor_detail(axes[2])

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=9)
    fig.suptitle(
        "Current Geant4 human phantom and tumor geometry",
        fontsize=14,
        fontweight="bold",
        y=0.975,
    )
    fig.text(
        0.5,
        0.942,
        "Tumor center (x, y, z) = (0, -80, 0) mm | beam direction: +y",
        ha="center",
        fontsize=9,
        color="#333333",
    )
    fig.subplots_adjust(left=0.06, right=0.99, bottom=0.09, top=0.88)
    fig.savefig(OUTPUT, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
