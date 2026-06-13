# Q2 Cytoplasm-only Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cytoplasm-only B10 control and update Q2 F1-F3 figures.

**Architecture:** Extend the existing boron-mode enum and detailed-cell geometry, then reuse the forced-capture generator with a nucleus-to-cell radial interval. Extend the q2D workflow and final plotting script without changing existing uniform/shell semantics.

**Tech Stack:** Geant4 C++, ROOT/PyROOT, Python, matplotlib, pytest-style contract tests.

---

### Task 1: Add failing contracts

**Files:**
- Modify: `tests/test_q2_forced_capture.py`
- Modify: `tests/test_q2_final_figures.py`

- [ ] Add assertions for the `cytoplasm` enum/configuration, smoke macro, q2D workflow, and four-column F3 layout.
- [ ] Run the focused tests and confirm they fail because cytoplasm support is absent.

### Task 2: Implement cytoplasm simulation mode

**Files:**
- Modify: `include/TherapyConfig.hh`
- Modify: `src/TherapyConfig.cc`
- Modify: `src/CellModel.cc`
- Modify: `src/PrimaryGeneratorAction.cc`
- Modify: `src/SteppingAction.cc`
- Create: `macros/smoke_b10capture_cytoplasm.mac`

- [ ] Add `BoronMode::Cytoplasm` and UI/name mappings.
- [ ] Build tumor cytoplasm from borated water while keeping the nucleus ordinary water.
- [ ] Sample forced-capture radii from nucleus radius to cell radius.
- [ ] Score the tumor cytoplasm as the boron region.
- [ ] Run focused tests and the deterministic smoke macro.

### Task 3: Extend workflow and figures

**Files:**
- Modify: `scripts/run_q2D_forced_capture.sh`
- Modify: `scripts/plot_q2_final_results.py`

- [ ] Generate three cytoplasm seeds at `342857 ppm` so total B10 matches the
  `300000 ppm` uniform case.
- [ ] Add cytoplasm to F1 and F2.
- [ ] Redesign F3 as three tumor columns plus one cytoplasm normal control.
- [ ] Mark nucleus and shell boundaries on both heatmaps and radial plots.
- [ ] Increase typography across F1-F4.

### Task 4: Generate data and verify

**Files:**
- Modify: `docs/q2_final_figures_handoff.md`

- [ ] Build the executable.
- [ ] Run three cytoplasm seeds at 100k captures each.
- [ ] Regenerate F1-F3 and inspect F3.
- [ ] Run all Python tests, syntax checks, and `git diff --check`.
- [ ] Document the new control and figure interpretation.
