# Head Neck Contact Geometry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the point-contact head/neck phantom geometry with an overlap-free face-contact construction where the neck cylinder reaches into the spherical head envelope.

**Architecture:** Keep `Neck` and `Head` as separate scoring volumes, but make the geometry legal by subtracting the inserted neck cylinder from the head sphere. Use shared local constants in `HumanPhantom.cc` for the head radius, neck radius, neck bottom, and derived neck top so the contact plane is reproducible.

**Tech Stack:** Geant4 C++ solids (`G4Tubs`, `G4Orb`, `G4SubtractionSolid`), Python `pytest` source-level regression tests, CMake build.

---

### Task 1: Regression Test

**Files:**
- Create: `tests/test_q1_head_neck_geometry.py`

- [ ] **Step 1: Write the failing test**

```python
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_q1_head_neck_uses_subtracted_head_for_overlap_free_insertion():
    text = (PROJECT_DIR / "src" / "HumanPhantom.cc").read_text()

    assert '#include "G4SubtractionSolid.hh"' in text
    assert "auto headSolid = new G4SubtractionSolid" in text
    assert "HeadSphereSolid" in text
    assert "HeadNeckCutSolid" in text

    assert "std::sqrt(kHeadRadius * kHeadRadius - kNeckRadius * kNeckRadius)" in text
    assert "kNeckTopZ = kHeadCenterZ - kHeadNeckIntersectionOffset" in text
    assert "kNeckHalfHeight = 0.5 * (kNeckTopZ - kNeckBottomZ)" in text
    assert "kNeckCenterZ = 0.5 * (kNeckTopZ + kNeckBottomZ)" in text


def test_q1_report_documents_inserted_neck_geometry():
    report = (PROJECT_DIR / "G4sim_reporter.md").read_text()

    assert "高度约 `105.2 mm`" in report
    assert "`z = 302.6 mm`" in report
    assert "颈部上端进入头部球体" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_q1_head_neck_geometry.py -q`

Expected: FAIL because the current head is a plain `G4Orb` and the report still documents a `90 mm` neck at `z = 295 mm`.

### Task 2: Geometry Implementation

**Files:**
- Modify: `src/HumanPhantom.cc`

- [ ] **Step 1: Add CSG include and local constants**

Use `G4SubtractionSolid.hh`, `<cmath>`, and constants for `kNeckRadius`, `kHeadRadius`, `kHeadCenterZ`, `kNeckBottomZ`, `kNeckTopZ`, `kNeckHalfHeight`, and `kNeckCenterZ`.

- [ ] **Step 2: Replace point-contact neck placement**

Create `NeckSolid` with `kNeckHalfHeight` and place it at `kNeckCenterZ`.

- [ ] **Step 3: Replace plain head orb with subtracted head solid**

Create `HeadSphereSolid`, create a local `HeadNeckCutSolid` cylinder tall enough to cover the inserted neck part, subtract it from the sphere at the sphere-local offset `kNeckCenterZ - kHeadCenterZ`, and place the resulting `HeadSolid` at `kHeadCenterZ`.

- [ ] **Step 4: Run focused source test**

Run: `pytest tests/test_q1_head_neck_geometry.py -q`

Expected: PASS.

### Task 3: Documentation and Mass Estimate

**Files:**
- Modify: `src/TherapyAnalysisManager.cc`
- Modify: `G4sim_reporter.md`

- [ ] **Step 1: Update normal-region mass estimate**

Use the same neck radius and derived neck top in `TherapyAnalysisManager.cc`; subtract the cylindrical inserted volume once from the summed phantom volume because it is cut out of the head solid.

- [ ] **Step 2: Update report geometry table**

Document the neck as radius `50 mm`, height about `105.2 mm`, center `z = 302.6 mm`, and note that the head sphere is CSG-subtracted by the inserted neck volume.

- [ ] **Step 3: Run source tests**

Run: `pytest tests/test_q1_head_neck_geometry.py -q`

Expected: PASS.

### Task 4: Build and Geant4 Overlap Verification

**Files:**
- No source changes unless build or overlap verification exposes an issue.

- [ ] **Step 1: Build existing target**

Run: `cmake --build build`

Expected: exit code 0.

- [ ] **Step 2: Run a short visual macro overlap check**

Run: `./build/tumor_therapy macros/vis.mac`

Expected: exit code 0 and no `Overlap` or `GeomVol1002` geometry warning in output.
