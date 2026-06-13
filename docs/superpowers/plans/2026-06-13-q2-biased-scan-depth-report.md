# Q2 Biased Scan And Depth Report Implementation Plan

## Outcome Note

Execution showed that the current occurrence-bias estimator is not independent of bias factor in the discrete micron-scale B10 geometry. The final concentration figures are therefore labeled exploratory and are not used for physical trend claims. The replacement depth experiment was rerun with analog (`bias=1`) neutron transport and is the validated beam-based result used in the final report.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace unreliable legacy Q2 scan evidence with reproducible weighted-bias ppm and tumor-depth experiments, generate final figures, and revise the final report in a formal academic style.

**Architecture:** Keep forced-capture F2/F3 and real-beam biased F4 unchanged. Add two independent real-neutron workflows: experiment C scans uniform-equivalent B10 ppm for uniform/shell modes with occurrence bias; experiment E scans only uniform B10 versus tumor depth. Both use Geant4 statistical weights and Li7 as the B10-capture proxy. A focused plotting script reads only the new ROOT files, validates source mode and bias factor, and produces weighted quantitative plots plus y-projected cell-dose maps.

**Tech Stack:** Geant4 11.4, ROOT/PyROOT, Bash, Python, NumPy, Matplotlib.

---

### Task 1: Restore Full Report Baseline

**Files:**
- Modify: `final_report.md`

- [ ] Restore the complete six-section report from Git HEAD.
- [ ] Preserve the current polished abstract and variable definitions where physically correct.
- [ ] Remove unsupported legacy scan conclusions during the final report revision task.

### Task 2: Define Scan Contracts With Tests

**Files:**
- Create: `tests/test_q2_biased_scans.py`
- Modify: `tests/test_q2_configuration.py`

- [ ] Add tests requiring experiment C to use `/therapy/sourceMode beam`, `/therapy/b10CaptureBias`, equal-total-B10 uniform/shell ppm conversion, and new biased output names.
- [ ] Add tests requiring the depth scan to vary only tumor/patch y position while keeping uniform B10, beam energy, bias, and source fixed.
- [ ] Add tests requiring weighted Li7, weighted dose, and projected-map panels in the new plotting script.
- [ ] Run the new tests and confirm they fail because the scripts do not yet exist.

### Task 3: Implement Biased Scan Runners

**Files:**
- Modify: `scripts/run_q2C_ppm_scan.sh`
- Create: `scripts/run_q2E_depth_scan.sh`

- [ ] Update experiment C defaults to `100x` occurrence bias and one reproducible seed per point.
- [ ] Output `output_q2C_biased_{uniform,shell}_{ppm}ppm.root`.
- [ ] Implement depth points `y = {-110,-95,-80,-65,-50} mm` with fixed uniform `300000 ppm`, `100x` bias, and `200000` histories.
- [ ] Output `output_q2E_depth_y{tag}_biased.root`.
- [ ] Run shell syntax checks and contract tests.

### Task 4: Implement Reproducible Scan Figures

**Files:**
- Create: `scripts/plot_q2_biased_scans.py`
- Modify: `tests/test_q2_biased_scans.py`

- [ ] Read and validate new ROOT files only; reject forced-capture files or mixed bias factors.
- [ ] For experiment C, calculate weighted Li7 per incident neutron, weighted mean tumor/normal cell dose, selectivity, and y-projected cell-dose maps.
- [ ] For the depth scan, calculate weighted Li7 per incident neutron, weighted mean tumor cell dose, total patch dose, and y-projected cell-dose maps.
- [ ] Produce `figures_final/Q2_biased_ppm_scan.png`, `figures_final/Q2_biased_ppm_projected_maps.png`, `figures_final/Q2_tumor_depth_scan.png`, and `figures_final/Q2_tumor_depth_projected_maps.png`.
- [ ] Annotate every figure with bias factor, histories, and weighted reconstruction.

### Task 5: Run Formal Experiments

**Files:**
- Generate: `output_q2C_biased_*.root`
- Generate: `output_q2E_depth_*.root`

- [ ] Build the simulation.
- [ ] Run experiment C with one seed per point, `200000` histories per point, and `100x` bias.
- [ ] Run the depth scan with one seed per point, `200000` histories per point, and `100x` bias.
- [ ] Verify ROOT files close normally, RunTree records bias=100, and EventTree entries equal requested histories.

### Task 6: Generate And Inspect Figures

**Files:**
- Generate: `figures_final/Q2_biased_ppm_scan.png`
- Generate: `figures_final/Q2_biased_ppm_projected_maps.png`
- Generate: `figures_final/Q2_tumor_depth_scan.png`
- Generate: `figures_final/Q2_tumor_depth_projected_maps.png`

- [ ] Run the focused plotter.
- [ ] Inspect all figures visually for shared scales, zero-dose rendering, readable labels, and statistically honest annotations.
- [ ] Report raw and weighted Li7 counts; do not claim monotonicity if the weighted estimates do not support it.

### Task 7: Rewrite Final Report

**Files:**
- Modify: `final_report.md`
- Modify: `docs/figures_final_real_data_audit.md`

- [ ] Correct the B10 branch energies and the conditional-capture command/implementation.
- [ ] Remove LQ/RBE sections not used by final figures.
- [ ] Replace legacy experiment E with the tumor-depth experiment.
- [ ] Replace legacy concentration and fluence figures/descriptions with the new reproducible biased scan results.
- [ ] Describe occurrence bias, statistical-weight reconstruction, one-seed limitations, and high-ppm limitations precisely.
- [ ] Use formal academic structure: motivation, methods, controlled variables, results, discussion, limitations, and conclusions.

### Task 8: Final Verification

**Files:**
- Verify all modified files.

- [ ] Run `cmake --build build -j4`.
- [ ] Run all Python tests.
- [ ] Run `python3 -m py_compile` on plotting scripts.
- [ ] Run `bash -n` on scan runners.
- [ ] Run `git diff --check`.
- [ ] Confirm all final-report image references exist.
