# Geant4 Radiotherapy Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reproducible workflow, `任务总结.md`, and Q1/Q2 figures for the Geant4 tumor radiotherapy assignment.

**Architecture:** Keep the existing `Geant4TumorTherapySim` simulation as the source of truth. Add a thin workflow layer that builds the executable, runs the four assignment macros, converts ROOT outputs into publication-ready figures, and writes a Chinese summary report that explains geometry, physics, scoring, and conclusions.

**Tech Stack:** Geant4 11.4.0, ROOT, CMake, Bash, Python 3, matplotlib, PyROOT.

---

## File Structure

- Create `scripts/run_assignment_workflow.sh`: one-command workflow for environment setup, build, simulation runs, and plotting.
- Create `scripts/plot_assignment_results.py`: reads ROOT outputs when available and generates Q1/Q2 figures; falls back to deterministic pedagogical curves only when ROOT files are absent.
- Create `任务总结.md`: Chinese assignment summary referencing generated figures and the Geant4 implementation.
- Create `figures/`: output directory for Q1 and Q2 PNG figures.
- Use existing `macros/problem1_gamma.mac`, `macros/problem1_proton.mac`, `macros/problem2_bnct_uniform.mac`, `macros/problem2_bnct_shell.mac`.

### Task 1: Baseline Build And Environment

**Files:**
- Read: `setup.sh`
- Read: `/home/NagaiYoru/packages/setup-geant4-root.sh`
- Read: `CMakeLists.txt`

- [ ] **Step 1: Verify environment entrypoint**

Run: `source /home/NagaiYoru/packages/setup-geant4-root.sh && geant4-config --version && root-config --version`

Expected: Geant4 and ROOT versions are printed.

- [ ] **Step 2: Configure project**

Run: `source /home/NagaiYoru/packages/setup-geant4-root.sh && cmake -S . -B build`

Expected: CMake exits with code 0 and writes build files.

- [ ] **Step 3: Build executable**

Run: `source /home/NagaiYoru/packages/setup-geant4-root.sh && cmake --build build -j2`

Expected: `build/tumor_therapy` exists.

### Task 2: Workflow Script

**Files:**
- Create: `scripts/run_assignment_workflow.sh`

- [ ] **Step 1: Create workflow script**

The script must:
- source `/home/NagaiYoru/packages/setup-geant4-root.sh`;
- configure and build the project;
- run Q1 gamma, Q1 proton, Q2 BNCT uniform, Q2 BNCT shell macros;
- call `scripts/plot_assignment_results.py`;
- print the generated figure paths.

- [ ] **Step 2: Run smoke workflow**

Run: `bash scripts/run_assignment_workflow.sh`

Expected: ROOT outputs and PNG figures are created, or the script stops at the first real error.

### Task 3: Plotting Script And Figures

**Files:**
- Create: `scripts/plot_assignment_results.py`
- Create: `figures/Q1_depth_dose.png`
- Create: `figures/Q1_region_dose_comparison.png`
- Create: `figures/Q1_let_spectra.png`
- Create: `figures/Q2_bnct_nucleus_dose.png`
- Create: `figures/Q2_bnct_secondary_yield.png`
- Create: `figures/Q2_boron_distribution.png`

- [ ] **Step 1: Implement ROOT readers**

Use PyROOT to read `EventTree`, `CellTree`, `hDepthDose`, and LET histograms from each ROOT file.

- [ ] **Step 2: Implement deterministic fallback**

If ROOT files are missing, generate clearly labeled deterministic reference curves so the report can still compile as a workflow artifact.

- [ ] **Step 3: Generate all figures**

Run: `source /home/NagaiYoru/packages/setup-geant4-root.sh && python3 scripts/plot_assignment_results.py`

Expected: six PNG figures are written under `figures/`.

### Task 4: Chinese Summary Report

**Files:**
- Create: `任务总结.md`

- [ ] **Step 1: Write report**

The report must include:
- assignment interpretation from `G4_rad.md` and the prompt image;
- simplified human geometry and tumor dimensions;
- Q1 gamma/proton source, physics, scoring, and comparison;
- Q2 BNCT neutron source, B10 material model, uniform/shell distributions, scoring, and comparison;
- workflow commands;
- figure references;
- limitations and next improvements.

- [ ] **Step 2: Verify references**

Run: `grep -n "figures/" 任务总结.md`

Expected: every referenced figure exists on disk.

### Task 5: Final Verification

**Files:**
- Verify: `任务总结.md`
- Verify: `figures/*.png`
- Verify: `scripts/run_assignment_workflow.sh`
- Verify: `scripts/plot_assignment_results.py`

- [ ] **Step 1: List deliverables**

Run: `find figures -maxdepth 1 -type f -name '*.png' -print | sort`

Expected: Q1 and Q2 figure files are listed.

- [ ] **Step 2: Check git diff**

Run: `git status --short`

Expected: Only planned report, scripts, plan, and figures are changed/created.

