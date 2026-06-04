import importlib.util
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_DIR / "scripts" / "plot_assignment_results.py"


def load_plot_module():
    spec = importlib.util.spec_from_file_location("plot_assignment_results", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gamma_scan_energy_points_and_file_tags():
    plot = load_plot_module()

    assert plot.GAMMA_SCAN_ENERGIES == [0.2, 0.5, 1, 2, 4, 6, 8, 10, 15]
    assert plot.energy_tag(0.2) == "0p2MeV"
    assert plot.energy_tag(1) == "1MeV"
    assert plot.scan_root_path("gamma", 0.5).name == "output_problem1_gamma_0p5MeV.root"
    assert plot.scan_root_path("proton", 45).name == "output_problem1_proton_45MeV.root"


def test_gamma_scan_plot_functions_are_registered():
    plot = load_plot_module()

    assert callable(plot.plot_q1_gamma_energy_heatmap_grid)
    assert callable(plot.plot_q1_gamma_energy_scan)


def test_let_plot_uses_low_let_zoom_and_mean_helper():
    plot = load_plot_module()

    assert plot.LET_PLOT_XMAX == 2.0
    assert plot.LET_HISTOGRAM_BINS == 200
    assert plot.histogram_weighted_mean([0.1, 0.3], [2, 1]) == 0.16666666666666666
