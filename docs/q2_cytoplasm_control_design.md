# Q2 Cytoplasm-only Control Design

## Goal

Add a B10 distribution control that is uniform in tumor-cell cytoplasm but excludes
the nucleus, then use it in the final F1-F3 figures.

## Simulation Semantics

- New boron mode: `cytoplasm`.
- In detailed tumor cells, the cytoplasm from `r=2.5 um` to `r=5 um` uses borated
  water, while the nucleus uses ordinary water.
- In forced-capture runs, each reaction position is sampled uniformly by volume
  between the configured nucleus radius and cell radius.
- The q2D cytoplasm concentration is `342857 ppm`, compensating for its `87.5%`
  volume fraction so that total B10 matches the `300000 ppm` uniform case.
- Existing `uniform` and `shell` modes retain their current meanings.

## Figure Changes

- F1 shows uniform, cytoplasm-only, and outer-shell B10 geometry.
- F2 compares all three forced-capture modes.
- F3 uses four columns: uniform tumor, cytoplasm tumor, shell tumor, and one
  cytoplasm-mode normal control.
- F3 heatmaps and radial plots mark the nucleus boundary at `2.5 um` and shell
  start at `4 um`.
- Final figures use larger title, axis-label, tick-label, and legend fonts.

## Verification

- Configuration and source generation accept `cytoplasm`.
- A deterministic 1000-event smoke run produces a readable ROOT file and samples
  forced-capture radii only in `2.5-5 um`.
- Three 100k-capture cytoplasm outputs are generated.
- F1-F3 render from the updated three-mode dataset.
