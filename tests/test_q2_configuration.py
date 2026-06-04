from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_q2_macros_use_target_beam_radius():
    for name in ("problem2_bnct_uniform.mac", "problem2_bnct_shell.mac"):
        text = (PROJECT_DIR / "macros" / name).read_text()
        assert "/therapy/beamRadius 150 um" in text
        assert "/run/beamOn 20000" in text


def test_q2_detector_uses_mixed_cell_patch():
    text = (PROJECT_DIR / "src" / "DetectorConstruction.cc").read_text()

    assert "BuildMixedPatch" in text
    assert "120. * micrometer" not in text
    assert "-120. * micrometer" not in text


def test_q2_mixed_patch_keeps_xz_column_cell_type_fixed_along_y():
    text = (PROJECT_DIR / "src" / "CellModel.cc").read_text()

    assert "((ix + iz) % 2) == 0" in text
    assert "((ix + iy + iz) % 2) == 0" not in text


def test_q2_heatmap_embeds_mean_dose_bars_below_maps():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()

    assert "fig.add_gridspec(2, 2" in text
    assert "Mean cell dose" in text
    assert "bar_ax.bar" in text


def test_q2_heatmap_uses_y_projected_columns_not_central_slice():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()
    heatmap_block = text.split("def plot_q2_micro_dose_map():", 1)[1].split("def plot_q2_mixed_geometry_layout():", 1)[0]

    assert "projected_columns" in heatmap_block
    assert "central_y_slice" not in heatmap_block
    assert "Projected cell dose" in heatmap_block


def test_q2_b10_scan_points_and_paths():
    import sys

    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    import plot_assignment_results as plot

    assert plot.B10_SCAN_PPM == [1000, 3000, 10000, 30000, 100000, 300000, 500000]
    assert plot.b10_scan_root_path("uniform", 1000).name == "output_problem2_bnct_uniform_1000ppm.root"
    assert plot.b10_scan_root_path("shell", 500000).name == "output_problem2_bnct_shell_500000ppm.root"


def test_q2_neutron_fluence_scan_points_and_paths():
    import sys

    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    import plot_assignment_results as plot

    assert plot.NEUTRON_FLUENCE_EVENTS == [2000, 5000, 10000, 20000, 50000, 100000, 200000]
    assert plot.NEUTRON_FLUENCE_MAP_EVENTS == [5000, 20000, 100000, 200000]
    assert plot.neutron_fluence_root_path("uniform", 2000).name == "output_problem2_bnct_uniform_fluence_2000events.root"
    assert plot.neutron_fluence_root_path("shell", 200000).name == "output_problem2_bnct_shell_fluence_200000events.root"


def test_q2_neutron_fluence_plots_are_registered():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()
    main_block = text.split("def main():", 1)[1]

    assert "plot_q2_neutron_fluence_scan()" in main_block
    assert "plot_q2_neutron_fluence_projected_maps()" in main_block
    assert "Q2_neutron_fluence_scan.png" in text
    assert "Q2_neutron_fluence_projected_maps.png" in text


def test_q2_neutron_fluence_runner_generates_fixed_b10_macros():
    script = (PROJECT_DIR / "scripts" / "run_q2_neutron_fluence_scan.sh").read_text()

    assert "fluence_events=(2000 5000 10000 20000 50000 100000 200000)" in script
    assert "/therapy/boronPPM 500000" in script
    assert "output_problem2_bnct_${mode}_fluence_${events}events.root" in script


def test_q2_dose_localization_fraction_handles_zero_denominator():
    import sys

    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    import plot_assignment_results as plot

    assert plot.dose_localization_fraction(3.0, 1.0) == 0.75
    assert plot.dose_localization_fraction(0.0, 0.0) == 0.0


def test_q2_redundant_bar_figures_are_not_generated():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()
    main_block = text.split("def main():", 1)[1]

    assert "plot_q2_nucleus_dose()" not in main_block
    assert "plot_q2_selectivity_index()" not in main_block
    assert "Q2_bnct_selectivity_index.png" not in main_block
    assert "Q2_nucleus_dose_selectivity.png" not in main_block
