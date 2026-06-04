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
