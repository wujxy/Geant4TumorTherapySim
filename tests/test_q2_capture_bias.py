from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def read(path):
    return (PROJECT_DIR / path).read_text()


def test_capture_bias_configuration_is_explicit_and_recorded():
    header = read("include/TherapyConfig.hh")
    config = read("src/TherapyConfig.cc")
    analysis = read("src/TherapyAnalysisManager.cc")

    assert "GetB10CaptureBias" in header
    assert '"/therapy/b10CaptureBias"' in config
    assert "fB10CaptureBias(1.0)" in config
    assert 'CreateNtupleDColumn("b10CaptureBias")' in analysis


def test_neutron_capture_bias_is_limited_to_borated_logical_volumes():
    main = read("main.cc")
    detector = read("src/DetectorConstruction.cc")
    operator = read("src/B10CaptureBiasOperator.cc")

    assert 'PhysicsBias("neutron", {"neutronInelastic"})' in main
    assert 'GetName() == "B10_Borated_Water"' in detector
    assert "AttachTo(logical)" in detector
    assert "SetBiasedCrossSection(fBiasFactor * analogXS)" in operator


def test_scoring_uses_geant4_statistical_weights():
    stepping = read("src/SteppingAction.cc")
    tracking = read("src/TrackingAction.cc")
    header = read("include/TherapyAnalysisManager.hh")
    analysis = read("src/TherapyAnalysisManager.cc")

    assert "track->GetWeight()" in stepping
    assert "track->GetWeight()" in tracking
    assert "G4double weight" in header
    assert "nLi7Weighted" in header
    assert 'CreateNtupleDColumn("nLi7Weighted")' in analysis
    assert 'CreateNtupleDColumn("weight")' in analysis


def test_single_seed_biased_f4_workflow_and_plot_annotation():
    runner = read("scripts/run_q2B_biased_single_seed.sh")
    plotter = read("scripts/plot_q2_final_results.py")
    docs = read("docs/q2_final_figures_handoff.md")

    assert "B10_CAPTURE_BIAS" in runner
    assert "/therapy/b10CaptureBias ${bias}" in runner
    assert "/run/beamOn ${events}" in runner
    assert "b10_capture_bias" in plotter
    assert "weighted Li7" in plotter
    assert "截面偏置" in docs
