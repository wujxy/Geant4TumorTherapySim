from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_source_mode_configuration_contract():
    header = (PROJECT_DIR / "include" / "TherapyConfig.hh").read_text()
    source = (PROJECT_DIR / "src" / "TherapyConfig.cc").read_text()

    assert "enum class SourceMode" in header
    assert "GetSourceMode()" in header
    assert "SourceModeName()" in header
    assert '"/therapy/sourceMode"' in source
    assert '"beam b10Capture"' in source


def test_cytoplasm_boron_mode_configuration_contract():
    header = (PROJECT_DIR / "include" / "TherapyConfig.hh").read_text()
    source = (PROJECT_DIR / "src" / "TherapyConfig.cc").read_text()

    assert "Shell = 2" in header
    assert "Cytoplasm = 3" in header
    assert '"none uniform cytoplasm shell"' in source
    assert 'value == "cytoplasm"' in source
    assert 'return "cytoplasm"' in source


def test_forced_capture_generator_uses_detector_cells_and_real_branches():
    header = (PROJECT_DIR / "include" / "PrimaryGeneratorAction.hh").read_text()
    source = (PROJECT_DIR / "src" / "PrimaryGeneratorAction.cc").read_text()
    actions = (PROJECT_DIR / "src" / "ActionInitialization.cc").read_text()

    assert "PrimaryGeneratorAction(const DetectorConstruction* detector)" in header
    assert "new PrimaryGeneratorAction(fDetector)" in actions
    assert "GenerateB10Capture" in source
    assert "1.47 * MeV" in source
    assert "0.84 * MeV" in source
    assert "1.78 * MeV" in source
    assert "1.01 * MeV" in source
    assert "0.478 * MeV" in source


def test_cytoplasm_capture_excludes_nucleus_and_geometry_keeps_nucleus_unborated():
    generator = (PROJECT_DIR / "src" / "PrimaryGeneratorAction.cc").read_text()
    cell_model = (PROJECT_DIR / "src" / "CellModel.cc").read_text()
    stepping = (PROJECT_DIR / "src" / "SteppingAction.cc").read_text()

    assert "BoronMode::Cytoplasm" in generator
    assert "config.GetNucleusRadius()" in generator
    assert "boronMode == BoronMode::Cytoplasm" in cell_model
    assert "nucleusMaterial" in cell_model
    assert "BoronMode::Cytoplasm" in stepping


def test_forced_capture_output_contract():
    source = (PROJECT_DIR / "src" / "TherapyAnalysisManager.cc").read_text()
    header = (PROJECT_DIR / "include" / "TherapyAnalysisManager.hh").read_text()

    assert 'CreateNtupleIColumn("sourceMode")' in source
    assert 'CreateNtupleDColumn("edepNucleusTumorAlpha_MeV")' in source
    assert 'CreateNtupleDColumn("edepNucleusTumorLi7_MeV")' in source
    assert 'CreateNtupleIColumn("forcedCaptureBranch")' in source
    assert 'CreateNtupleDColumn("forcedCaptureRadius_um")' in source
    assert 'CreateNtupleDColumn("forcedInitialHighLET_MeV")' in source
    assert "RecordForcedCapture" in header


def test_q2d_workflow_and_plot_contract():
    runner = (PROJECT_DIR / "scripts" / "run_q2D_forced_capture.sh").read_text()
    plot = (PROJECT_DIR / "scripts" / "plot_assignment_results.py").read_text()

    assert 'CAPTURE_EVENTS="${CAPTURE_EVENTS:-100000}"' in runner
    assert "/therapy/sourceMode b10Capture" in runner
    assert "output_q2D_capture_${mode}_seed${s}.root" in runner
    assert "uniform cytoplasm shell" in runner
    assert 'if [[ "$mode" == cytoplasm ]]; then ppm=342857; fi' in runner
    assert "q2d_capture_paths" in plot
    assert "aggregate_q2d_capture_summary" in plot
    assert "fit_capture_yield_per_ppm" in plot
    assert "cylindrical_bin_volumes" in plot
    assert "spherical_shell_volumes" in plot
    assert "forced_capture_region_energy" in plot
    assert "Q2_forced_capture_microdose.png" in plot


def test_forced_capture_smoke_macros_are_deterministic():
    for mode in ("uniform", "cytoplasm", "shell"):
        text = (PROJECT_DIR / "macros" / f"smoke_b10capture_{mode}.mac").read_text()
        assert "/therapy/sourceMode b10Capture" in text
        assert f"/therapy/boronMode {mode}" in text
        assert "/random/setSeeds 11111111 98765431" in text
        assert "/run/beamOn 1000" in text


def test_cell_local_energy_is_distributed_along_step():
    source = (PROJECT_DIR / "src" / "SteppingAction.cc").read_text()
    analysis = (PROJECT_DIR / "src" / "TherapyAnalysisManager.cc").read_text()
    header = (PROJECT_DIR / "include" / "TherapyAnalysisManager.hh").read_text()

    assert "const G4ThreeVector scoringPosition" in source
    assert "0.5 * (prePoint->GetPosition() + postPoint->GetPosition())" in source
    assert "cellLocalStart = prePoint->GetPosition()" in source
    assert "cellLocalEnd = postPoint->GetPosition()" in source
    assert "const G4ThreeVector& cellLocalEndPosition" in header
    assert "kCellLocalSamplingStep = 0.1 * micrometer" in analysis
    assert "edepMeV / nSamples" in analysis
    assert "GetSourceMode() == SourceMode::B10Capture" in analysis


def test_detailed_cells_use_uniform_sub_bin_step_limit():
    source = (PROJECT_DIR / "src" / "CellModel.cc").read_text()
    main = (PROJECT_DIR / "main.cc").read_text()

    assert '#include "G4UserLimits.hh"' in source
    assert "kDetailedCellMaxStep = 0.05 * micrometer" in source
    assert "outerLogical->SetUserLimits" in source
    assert "innerLogical->SetUserLimits" in source
    assert "nucleusLogical->SetUserLimits" in source
    assert "config.GetSourceMode() == SourceMode::B10Capture" in source
    assert '#include "G4StepLimiterPhysics.hh"' in main
    assert "physicsList->RegisterPhysics(new G4StepLimiterPhysics)" in main
