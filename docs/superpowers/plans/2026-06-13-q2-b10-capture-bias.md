# Q2 B10 Capture Bias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 100x neutron-capture occurrence bias in B10-bearing cell volumes, with statistically weighted scoring that reconstructs the analog F4 result.

**Architecture:** Wrap neutron `neutronInelastic`, which owns the HP `B10(n,alpha)Li7` channel, with Geant4 generic biasing physics and attach a constant cross-section-change operator only to logical volumes made from `B10_Borated_Water`. Preserve raw secondary counts for sampled statistics while multiplying all energy-deposition scoring and weighted secondary yields by Geant4 track weights.

**Tech Stack:** C++17, Geant4 11.4 generic biasing, ROOT ntuples, Python/pytest, matplotlib.

---

### Task 1: Configuration and physics bias

**Files:**
- Modify: `include/TherapyConfig.hh`
- Modify: `src/TherapyConfig.cc`
- Create: `include/B10CaptureBiasOperator.hh`
- Create: `src/B10CaptureBiasOperator.cc`
- Modify: `include/DetectorConstruction.hh`
- Modify: `src/DetectorConstruction.cc`
- Modify: `main.cc`
- Test: `tests/test_q2_capture_bias.py`

- [ ] Add `/therapy/b10CaptureBias`, defaulting to `1.0` and rejecting values below one.
- [ ] Register `G4GenericBiasingPhysics` for neutron `nCapture`.
- [ ] Attach a constant cross-section-change operator to B10-bearing logical volumes when factor > 1.
- [ ] Store the configured factor in RunTree.

### Task 2: Weighted scoring

**Files:**
- Modify: `include/TherapyAnalysisManager.hh`
- Modify: `src/TherapyAnalysisManager.cc`
- Modify: `src/SteppingAction.cc`
- Test: `tests/test_q2_capture_bias.py`

- [ ] Multiply every energy-deposition score and histogram fill by `track->GetWeight()`.
- [ ] Preserve integer raw alpha/Li7 counts and add weighted alpha/Li7 yields.
- [ ] Add track weight to StepTree for auditability.

### Task 3: Single-seed F4 workflow and reporting

**Files:**
- Create: `scripts/run_q2B_biased_single_seed.sh`
- Modify: `scripts/plot_assignment_results.py`
- Modify: `scripts/plot_q2_final_results.py`
- Modify: `docs/q2_final_figures_handoff.md`
- Test: `tests/test_q2_capture_bias.py`

- [ ] Run one 200k-history seed per BNCT mode with 100x capture bias.
- [ ] Plot weighted doses and annotate raw/weighted captures and bias factor.
- [ ] Reject mixed bias factors when aggregating files.
- [ ] Document that the plotted dose is reconstructed with Geant4 statistical weights.

### Task 4: Verification

- [ ] Run pytest.
- [ ] Build the executable.
- [ ] Run factor-1 and factor-100 smoke macros.
- [ ] Verify factor-100 increases raw captures while weighted output remains physically normalized.
- [ ] Generate the biased single-seed F4 figure.
