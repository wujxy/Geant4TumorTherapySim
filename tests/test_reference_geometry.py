from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_reference_geometry_matches_assignment_figure():
    config = (PROJECT_DIR / "src" / "TherapyConfig.cc").read_text()
    phantom = (PROJECT_DIR / "src" / "HumanPhantom.cc").read_text()

    assert "fTumorSize(10. * mm, 20. * mm, 30. * mm)" in config
    assert "fTumorPosition(0., -80. * mm, 0.)" in config
    assert "fSourcePosition(0., -600. * mm, 0.)" in config
    assert "fSourceDirection(0., 1., 0.)" in config
    assert 'new G4Box("TorsoSolid", 60. * mm, 130. * mm, 250. * mm)' in phantom
    assert 'G4ThreeVector(0., -65. * mm, -660. * mm)' in phantom
    assert 'G4ThreeVector(0., 65. * mm, -660. * mm)' in phantom
    assert 'auto neckSolid = new G4SubtractionSolid(' in phantom


def test_experiment_macros_use_positive_y_beam_and_negative_y_tumor_position():
    for path in sorted((PROJECT_DIR / "macros").glob("*.mac")):
        text = path.read_text()
        if "/therapy/tumorPosition" not in text:
            continue
        assert "/therapy/tumorPosition 0 -80 0 mm" in text, path.name
        if "/therapy/sourceMode b10Capture" in text:
            continue
        assert "/therapy/sourcePosition 0 -600 0 mm" in text, path.name
        assert "/therapy/sourceDirection 0 1 0" in text, path.name


def test_q1_depth_scoring_follows_y_axis():
    analysis = (PROJECT_DIR / "src" / "TherapyAnalysisManager.cc").read_text()

    assert 'CreateH1("hDepthDose", "Depth dose;Depth y (mm);Deposited energy (MeV)"' in analysis
    assert "analysis->FillH1(8, position.y() / mm, weightedEdep / MeV);" in analysis


def test_reference_geometry_distances_are_explicit_in_section_plot():
    plot = (PROJECT_DIR / "scripts" / "plot_body_tumor_sections_check.py").read_text()

    assert "TUMOR_CENTER = (0.0, -80.0, 0.0)" in plot
    assert "TUMOR_SIZE = (10.0, 20.0, 30.0)" in plot
    assert "TORSO_Y = (-130.0, 130.0)" in plot
    assert "TORSO_X = (-60.0, 60.0)" in plot


def test_q1_body_tumor_figure_uses_current_geometry_and_compact_three_panel_layout():
    plot = (PROJECT_DIR / "scripts" / "plot_q1_body_tumor_geometry.py").read_text()

    assert 'OUTPUT = PROJECT_DIR / "figures" / "Q1_body_tumor_xz_section.png"' in plot
    assert "TUMOR_CENTER = (0.0, -80.0, 0.0)" in plot
    assert "TUMOR_SIZE = (10.0, 20.0, 30.0)" in plot
    assert "BEAM_Z = TUMOR_CENTER[2]" in plot
    assert "add_top_distance(ax" in plot
    assert 'ax.text(label_x, 125, "25 cm"' in plot
    assert "draw_front_view(axes[0])" in plot
    assert "draw_side_view(axes[1])" in plot
    assert "draw_tumor_detail(axes[2])" in plot
    assert '"wspace": 0.08' in plot
