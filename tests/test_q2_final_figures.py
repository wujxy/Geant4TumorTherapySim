import importlib.util
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_DIR / "scripts" / "plot_q2_final_results.py"


def load_module():
    spec = importlib.util.spec_from_file_location("plot_q2_final_results", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_final_figure_output_contract():
    text = SCRIPT_PATH.read_text()

    assert 'FIG_DIR = PROJECT_DIR / "figures2"' in text
    assert "F1_b10_distribution_geometry.png" in text
    assert "F2_forced_capture_quantitative.png" in text
    assert "F3_forced_capture_singlecell_distribution.png" in text
    assert "F4_therapy_comparison_projected_maps.png" in text
    assert 'for mode in ("uniform", "cytoplasm", "shell")' in text


def test_f1_radius_arrows_start_at_cell_center():
    text = SCRIPT_PATH.read_text()

    assert "def draw_radius_arrow" in text
    assert "xytext=(0.0, 0.0)" in text
    assert 'draw_radius_arrow(ax, 2.5, "nucleus radius"' in text
    assert 'draw_radius_arrow(ax, 5.0, "cell radius"' in text
    assert 'draw_radius_arrow(ax, 4.0, "shell start"' in text


def test_f3_uses_three_tumor_modes_and_one_cytoplasm_normal_control():
    text = SCRIPT_PATH.read_text()

    assert '"Tumor: cytoplasm-only"' in text
    assert '"Normal control: cytoplasm-only"' in text
    assert '"Normal control: uniform"' not in text
    assert '"Normal control: outer shell"' not in text
    assert "draw_cell_boundaries" in text
    assert "apply_readable_style" in text


def test_f4_prefers_single_seed_biased_bnct_and_keeps_unbiased_fallback():
    text = SCRIPT_PATH.read_text()

    assert "def therapy_input_paths" in text
    assert "output_q2B_{name}_biased_seed1.root" in text
    assert "output_q2B_{name}_seed*.root" in text
    assert "def aggregate_cell_rows" in text
    assert '"n_events": total_events' in text
    assert '"n_li7": total_li7' in text
    assert '"n_li7_weighted": total_li7_weighted' in text
    assert "weighted Li7" in text


def test_bnct_statistics_runner_stops_at_capture_threshold():
    text = (PROJECT_DIR / "scripts" / "run_q2B_bnct_statistics.sh").read_text()

    assert 'TARGET_CAPTURES="${TARGET_CAPTURES:-100}"' in text
    assert 'EVENTS_PER_SEED="${EVENTS_PER_SEED:-2000000}"' in text
    assert "output_q2B_neutron_${mode}_seed${seed}.root" in text
    assert "while (( captures < TARGET_CAPTURES ))" in text


def test_selectivity_uses_tumor_over_total():
    module = load_module()

    assert module.tumor_selectivity(3.0, 1.0) == 0.75
    assert module.tumor_selectivity(0.0, 0.0) == 0.0


def test_equal_tumor_dose_scaling():
    module = load_module()

    scaled_tumor, scaled_normal, scale = module.scale_to_tumor_dose(0.25, 0.05, 1.0)

    assert scaled_tumor == 1.0
    assert scaled_normal == 0.2
    assert scale == 4.0


def test_projected_dose_colormap_renders_masked_zero_dose_as_black():
    module = load_module()

    rgba = module.projected_dose_colormap()(float("nan"))

    assert tuple(rgba) == (0.0, 0.0, 0.0, 1.0)


def test_source_mode_validation():
    module = load_module()

    module.require_source_mode({"source_mode": 1}, 1, "capture.root")
    try:
        module.require_source_mode({"source_mode": 0}, 1, "beam.root")
    except ValueError as error:
        assert "beam.root" in str(error)
    else:
        raise AssertionError("beam input must be rejected for a capture-only figure")


def test_mean_std_accepts_generators():
    module = load_module()

    mean, std = module.mean_std(value for value in (1.0, 2.0, 3.0))

    assert mean == 2.0
    assert round(std, 6) == 1.0
