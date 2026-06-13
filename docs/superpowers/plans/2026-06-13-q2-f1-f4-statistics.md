# Q2 F1 Radius Arrows and F4 BNCT Statistics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make F1 radius annotations geometrically explicit and increase F4 real-neutron BNCT hotspot statistics through multi-seed accumulation.

**Architecture:** Add a reusable F1 center-to-boundary radius annotation helper. Preserve each F4 ROOT run independently, then aggregate CellTree rows by cell ID and sum event/capture counts before equal-tumor-dose normalization.

**Tech Stack:** Python, matplotlib, PyROOT, Bash, Geant4.

---

### Task 1: Add failing contracts

**Files:**
- Modify: `tests/test_q2_final_figures.py`

- [ ] Require `draw_radius_arrow`, multi-file BNCT inputs, cell-ID aggregation, and F4 statistics labels.
- [ ] Run the focused zero-dependency test runner and confirm failures are caused by missing behavior.

### Task 2: Implement plotting and aggregation

**Files:**
- Modify: `scripts/plot_q2_final_results.py`

- [ ] Draw nucleus, cell, and shell-start radius arrows from `(0,0)` to their boundaries.
- [ ] Load the existing q2B BNCT final ROOT plus supplemental seed ROOT files.
- [ ] Aggregate CellTree dose channels by cell ID and sum incident-neutron/Li7 counts.
- [ ] Display total neutrons and Li7 captures in BNCT map annotations.

### Task 3: Add supplemental BNCT runner

**Files:**
- Create: `scripts/run_q2B_bnct_statistics.sh`
- Modify: `tests/test_q2_final_figures.py`

- [ ] Generate independent uniform/shell real-neutron macros at `2M` events per seed.
- [ ] Stop only after each mode has at least `100` total Li7 captures, including the existing final ROOT file.
- [ ] Preserve all ROOT files for reproducible aggregation.

### Task 4: Run and verify

**Files:**
- Modify: `docs/q2_final_figures_handoff.md`

- [ ] Run supplemental BNCT seeds until both modes reach the capture threshold.
- [ ] Regenerate F1 and F4 and inspect them.
- [ ] Run the build, complete zero-dependency test suite, syntax checks, and `git diff --check`.
- [ ] Record final neutron/capture statistics and interpretation.

