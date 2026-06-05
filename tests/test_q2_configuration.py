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
    heatmap_block = text.split("def plot_q2_micro_dose_map():", 1)[1].split("def plot_q2_mixed_geometry_layout():", 1)[0]

    assert "fig.add_gridspec(3, 2" in heatmap_block
    assert "Mean cell dose" in text
    assert "Mean nucleus dose" in heatmap_block
    assert "cell_bar_ax.bar" in heatmap_block
    assert "nucleus_bar_ax.bar" in heatmap_block
    assert ".errorbar(" not in heatmap_block


def test_q2_heatmap_uses_y_projected_columns_not_central_slice():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()
    heatmap_block = text.split("def plot_q2_micro_dose_map():", 1)[1].split("def plot_q2_mixed_geometry_layout():", 1)[0]

    assert "projected_columns" in heatmap_block
    assert "central_y_slice" not in heatmap_block
    assert "Projected cell dose" in heatmap_block


def test_q2_heatmap_uses_high_statistics_results_and_linear_color_scale():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()
    heatmap_block = text.split("def plot_q2_micro_dose_map():", 1)[1].split("def plot_q2_mixed_geometry_layout():", 1)[0]

    assert 'neutron_fluence_root_path("uniform", 200000)' in heatmap_block
    assert 'neutron_fluence_root_path("shell", 200000)' in heatmap_block
    assert "LogNorm(" not in heatmap_block
    assert "vmin=0" in heatmap_block
    assert "vmax=max_dose" in heatmap_block
    assert "linear scale" in heatmap_block


def test_q2_b10_scan_points_and_paths():
    import sys

    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    import plot_assignment_results as plot

    assert plot.B10_SCAN_PPM == [1000, 3000, 10000, 30000, 100000, 300000, 500000]
    assert plot.b10_scan_root_path("uniform", 1000).name == "output_problem2_bnct_uniform_1000ppm.root"
    assert plot.b10_scan_root_path("shell", 500000).name == "output_problem2_bnct_shell_500000ppm.root"


def test_q2_b10_scan_defaults_to_high_statistics_runs():
    standalone_runner = (PROJECT_DIR / "scripts" / "run_q2_b10_scan.sh").read_text()
    workflow_runner = (PROJECT_DIR / "scripts" / "run_assignment_workflow.sh").read_text()

    assert 'B10_SCAN_EVENTS="${B10_SCAN_EVENTS:-200000}"' in standalone_runner
    assert 'B10_SCAN_EVENTS="${B10_SCAN_EVENTS:-200000}"' in workflow_runner


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


def test_q2_gamma_and_proton_macros_use_shared_cell_patch():
    expected_common = [
        "/therapy/mode problem2",
        "/therapy/boronMode none",
        "/therapy/sourcePosition -45 -600 30 mm",
        "/therapy/sourceDirection 0 1 0",
        "/therapy/beamRadius 150 um",
        "/therapy/cellPatchSize 200 200 200 um",
        "/therapy/cellPitch 12 um",
        "/therapy/cellDiameter 10 um",
        "/therapy/nucleusRadius 2.5 um",
        "/run/beamOn 20000",
    ]
    macro_expectations = {
        "problem2_gamma.mac": ["/therapy/outputFile output_problem2_gamma.root", "/gun/particle gamma", "/gun/energy 1 MeV"],
        "problem2_proton.mac": ["/therapy/outputFile output_problem2_proton.root", "/gun/particle proton", "/gun/energy 45 MeV"],
    }

    for macro_name, specific_lines in macro_expectations.items():
        text = (PROJECT_DIR / "macros" / macro_name).read_text()
        for line in expected_common + specific_lines:
            assert line in text


def test_q2_therapy_comparison_runner_generates_control_macros():
    script = (PROJECT_DIR / "scripts" / "run_q2_therapy_comparison.sh").read_text()

    assert 'declare -A particles=(["gamma"]="gamma" ["proton"]="proton")' in script
    assert 'declare -A energies=(["gamma"]="1 MeV" ["proton"]="45 MeV")' in script
    assert "/therapy/mode problem2" in script
    assert "/therapy/boronMode none" in script
    assert "/therapy/beamRadius 150 um" in script
    assert 'output_problem2_${case_name}.root' in script
    assert "Q2_therapy_comparison_projected_maps.png" in script
    assert "Q2_therapy_comparison_summary.png" not in script
    assert "Q2_therapy_comparison_dose_bars.png" not in script
    assert "Q2_therapy_comparison_selectivity.png" not in script


def test_q2_therapy_comparison_registers_only_combined_figure():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()
    main_block = text.split("def main():", 1)[1]

    expected_functions = [
        "plot_q2_therapy_comparison_projected_maps()",
    ]
    expected_figures = [
        "Q2_therapy_comparison_projected_maps.png",
    ]
    removed_functions = [
        "plot_q2_therapy_comparison_summary()",
        "plot_q2_therapy_comparison_dose_bars()",
        "plot_q2_therapy_comparison_selectivity()",
        "plot_q2_therapy_comparison_cell_spectra()",
        "plot_q2_therapy_comparison_secondary_yield()",
    ]
    removed_figures = [
        "Q2_therapy_comparison_summary.png",
        "Q2_therapy_comparison_dose_bars.png",
        "Q2_therapy_comparison_selectivity.png",
        "Q2_therapy_comparison_cell_spectra.png",
        "Q2_therapy_comparison_secondary_yield.png",
    ]

    for function_call in expected_functions:
        assert function_call in main_block
    for figure_name in expected_figures:
        assert figure_name in text
    for function_call in removed_functions:
        assert function_call not in main_block
    for figure_name in removed_figures:
        assert figure_name not in text


def test_q2_therapy_comparison_combined_figure_uses_bars_and_shared_localization_axis():
    text = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()
    combined_block = text.split("def plot_q2_therapy_comparison_projected_maps():", 1)[1].split("def plot_q2_b10_concentration_scan", 1)[0]

    assert "fig.add_gridspec(3, 4" in combined_block
    assert "fig.add_subplot(grid[1, :])" in combined_block
    assert "fig.add_subplot(grid[2, :])" in combined_block
    assert "Mean whole-cell dose" in combined_block
    assert "Cell localization" in combined_block
    assert "dose_ax.bar" in combined_block
    assert "localization_ax.bar" in combined_block
    assert 'hatch="//"' in combined_block
    assert ".errorbar(" not in combined_block
    assert "Whole-cell normal burden" not in combined_block
    assert "nucleus_localization" not in combined_block


def test_q2_therapy_comparison_summary_metrics_are_defined():
    import sys

    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    import plot_assignment_results as plot

    assert plot.therapy_comparison_root_path("gamma").name == "output_problem2_gamma.root"
    assert plot.therapy_comparison_root_path("proton").name == "output_problem2_proton.root"
    assert plot.normal_burden(2.0, 0.5) == 0.25
    assert plot.normal_burden(0.0, 0.5) == 0.0


def test_report_includes_q2_therapy_comparison_section():
    report = (PROJECT_DIR / "G4sim_reporter.md").read_text()

    assert "### 4.7 BNCT 与常规射线在同一细胞 patch 下的对比" in report
    assert "不是替代 Q1" in report
    assert "Q2_therapy_comparison_summary.png" not in report
    assert "Q2_therapy_comparison_projected_maps.png" in report
    assert "Q2_therapy_comparison_dose_bars.png" not in report
    assert "Q2_therapy_comparison_selectivity.png" not in report
    assert "Q2_therapy_comparison_cell_spectra.png" not in report
    assert "Q2_therapy_comparison_secondary_yield.png" not in report
    assert "正常细胞核的保护更强" in report
    assert "肿瘤细胞核输送剂量的能力弱于 uniform" in report


def test_report_documents_high_statistics_q2_figures():
    report = (PROJECT_DIR / "G4sim_reporter.md").read_text()
    hotspot_section = report.split("### 4.4 固定浓度下的热点图与剂量比较", 1)[1].split("### 4.5 B10 浓度扫描", 1)[0]
    concentration_section = report.split("### 4.5 B10 浓度扫描", 1)[1].split("### 4.6 相对中子注量扫描", 1)[0]

    assert "`200000` histories" in hotspot_section
    assert "共享线性色标" in hotspot_section
    assert "每个浓度点使用 `200000` histories" in concentration_section
