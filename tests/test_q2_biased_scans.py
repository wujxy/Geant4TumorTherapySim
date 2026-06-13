from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def read(path):
    return (PROJECT_DIR / path).read_text()


def test_event_tree_records_whether_primary_neutron_reaches_tumor():
    header = read("include/TherapyAnalysisManager.hh")
    stepping = read("src/SteppingAction.cc")
    analysis = read("src/TherapyAnalysisManager.cc")

    assert "primaryNeutronReachedTumor" in header
    assert "MarkPrimaryNeutronReachedTumor" in header
    assert "track->GetParentID() == 0" in stepping
    assert 'particleName == "neutron"' in stepping
    assert 'CreateNtupleIColumn("primaryNeutronReachedTumor")' in analysis


def test_experiment_c_uses_weighted_capture_bias_and_new_outputs():
    runner = read("scripts/run_q2C_ppm_scan.sh")

    assert 'B10_CAPTURE_BIAS="${B10_CAPTURE_BIAS:-1000}"' in runner
    assert "/therapy/sourceMode beam" in runner
    assert "/therapy/b10CaptureBias ${bias}" in runner
    assert "output_q2C_biased_${mode}_${uppm}ppm.root" in runner
    assert "PPM_LIST=(30000 100000 200000 300000)" in runner


def test_depth_scan_changes_only_uniform_tumor_depth():
    runner = read("scripts/run_q2E_depth_scan.sh")

    assert "DEPTH_Y_MM=(-110 -95 -80 -65 -50)" in runner
    assert 'B10_CAPTURE_BIAS="${B10_CAPTURE_BIAS:-1}"' in runner
    assert "/therapy/boronMode uniform" in runner
    assert "/therapy/boronPPM ${UNIFORM_PPM}" in runner
    assert "/therapy/sourceMode beam" in runner
    assert "/therapy/b10CaptureBias ${B10_CAPTURE_BIAS}" in runner
    assert "/therapy/tumorPosition 0 ${tumor_y} 0 mm" in runner
    assert "output_q2E_depth_y${tag}_analog.root" in runner


def test_biased_scan_plotter_uses_weighted_li7_reach_fraction_and_projected_maps():
    plotter = read("scripts/plot_q2_biased_scans.py")

    assert 'Sum("nLi7Weighted")' in plotter
    assert 'Sum("primaryNeutronReachedTumor")' in plotter
    assert "projected_columns" in plotter
    assert "Q2_biased_ppm_scan.png" in plotter
    assert "Q2_biased_ppm_projected_maps.png" in plotter
    assert "Q2_tumor_depth_scan.png" in plotter
    assert "Q2_tumor_depth_projected_maps.png" in plotter
    assert "not analog-validated" in plotter


def test_depth_maps_show_cell_layout_with_shared_linear_zero_based_scale():
    plotter = read("scripts/plot_q2_biased_scans.py")
    depth_block = plotter.split("def plot_depth_maps(data):", 1)[1].split("def main():", 1)[0]

    assert 'summary["columns"]' in depth_block
    assert "read_h3_xy" not in depth_block
    assert "Normalize(vmin=0.0" in depth_block
    assert '(1, "o"' in depth_block
    assert '(0, "s"' in depth_block
    assert "masked_less_equal" not in depth_block
    assert "Circle((0, 0), 150.0" in depth_block
    assert "Projected cell-column dose summed over y (Gy)" in depth_block
