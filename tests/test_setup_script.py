from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_setup_script_sources_local_geant4_and_root_environment():
    text = (PROJECT_DIR / "setup.sh").read_text()

    assert "/home/NagaiYoru/packages/root" in text
    assert "/home/NagaiYoru/packages/geant4-11.4.0" in text
    assert "juno_env" not in text
    assert "CMAKE_PREFIX_PATH" in text
