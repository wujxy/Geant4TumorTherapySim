from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_q1_head_neck_keeps_spherical_head_and_cuts_overlapping_neck():
    text = (PROJECT_DIR / "src" / "HumanPhantom.cc").read_text()

    assert '#include "G4SubtractionSolid.hh"' in text
    assert 'auto headSolid = new G4Orb("HeadSolid", kHeadRadius);' in text
    assert 'auto neckSolid = new G4SubtractionSolid(' in text
    assert '"NeckEnvelopeSolid"' in text
    assert '"NeckHeadCutSolid"' in text
    assert "kHeadCenterZ - kNeckEnvelopeCenterZ" in text


def test_q1_report_documents_neck_cut_geometry():
    report = (PROJECT_DIR / "G4sim_reporter.md").read_text()

    assert "保留完整球形头部" in report
    assert "从颈部圆柱中扣除" in report
    assert "采用点相切" not in report
