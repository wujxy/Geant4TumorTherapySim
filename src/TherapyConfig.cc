#include "TherapyConfig.hh"

#include "G4SystemOfUnits.hh"
#include "G4UIcommand.hh"
#include "G4UIcmdWith3Vector.hh"
#include "G4UIcmdWith3VectorAndUnit.hh"
#include "G4UIcmdWithABool.hh"
#include "G4UIcmdWithADoubleAndUnit.hh"
#include "G4UIcmdWithADouble.hh"
#include "G4UIcmdWithAString.hh"
#include "G4UIdirectory.hh"
#include "G4UImessenger.hh"

class TherapyMessenger : public G4UImessenger {
public:
  explicit TherapyMessenger(TherapyConfig* config)
    : fConfig(config)
  {
    fDirectory = new G4UIdirectory("/therapy/");
    fDirectory->SetGuidance("Tumor therapy simulation controls.");

    fModeCmd = new G4UIcmdWithAString("/therapy/mode", this);
    fModeCmd->SetGuidance("Set simulation mode: problem1 or problem2.");
    fModeCmd->SetCandidates("problem1 problem2");

    fBoronModeCmd = new G4UIcmdWithAString("/therapy/boronMode", this);
    fBoronModeCmd->SetGuidance("Set boron mode: none, uniform, or shell.");
    fBoronModeCmd->SetCandidates("none uniform shell");

    fOutputFileCmd = new G4UIcmdWithAString("/therapy/outputFile", this);
    fOutputFileCmd->SetGuidance("Set output ROOT file name.");

    fSaveStepTreeCmd = new G4UIcmdWithABool("/therapy/saveStepTree", this);
    fSaveStepTreeCmd->SetGuidance("Enable detailed StepTree output.");

    fTumorPositionCmd = new G4UIcmdWith3VectorAndUnit("/therapy/tumorPosition", this);
    fTumorPositionCmd->SetGuidance("Set tumor region center.");
    fTumorPositionCmd->SetUnitCategory("Length");

    fNormalPositionCmd = new G4UIcmdWith3VectorAndUnit("/therapy/normalPosition", this);
    fNormalPositionCmd->SetGuidance("Set normal control region center.");
    fNormalPositionCmd->SetUnitCategory("Length");

    fSourcePositionCmd = new G4UIcmdWith3VectorAndUnit("/therapy/sourcePosition", this);
    fSourcePositionCmd->SetGuidance("Set beam source center.");
    fSourcePositionCmd->SetUnitCategory("Length");

    fSourceDirectionCmd = new G4UIcmdWith3Vector("/therapy/sourceDirection", this);
    fSourceDirectionCmd->SetGuidance("Set beam direction vector.");

    fBeamRadiusCmd = new G4UIcmdWithADoubleAndUnit("/therapy/beamRadius", this);
    fBeamRadiusCmd->SetGuidance("Set circular beam radius.");
    fBeamRadiusCmd->SetUnitCategory("Length");

    fCellPatchSizeCmd = new G4UIcmdWith3VectorAndUnit("/therapy/cellPatchSize", this);
    fCellPatchSizeCmd->SetGuidance("Set representative cell patch size.");
    fCellPatchSizeCmd->SetUnitCategory("Length");

    fCellPitchCmd = new G4UIcmdWithADoubleAndUnit("/therapy/cellPitch", this);
    fCellPitchCmd->SetGuidance("Set lattice pitch for cell centers.");
    fCellPitchCmd->SetUnitCategory("Length");

    fCellDiameterCmd = new G4UIcmdWithADoubleAndUnit("/therapy/cellDiameter", this);
    fCellDiameterCmd->SetGuidance("Set spherical cell diameter.");
    fCellDiameterCmd->SetUnitCategory("Length");

    fNucleusRadiusCmd = new G4UIcmdWithADoubleAndUnit("/therapy/nucleusRadius", this);
    fNucleusRadiusCmd->SetGuidance("Set nucleus radius for problem2.");
    fNucleusRadiusCmd->SetUnitCategory("Length");

    fBoronPPMCmd = new G4UIcmdWithADouble("/therapy/boronPPM", this);
    fBoronPPMCmd->SetGuidance("Set B10 mass concentration in ppm for borated material.");

    fKillDoseThresholdCmd = new G4UIcmdWithADoubleAndUnit("/therapy/killDoseThreshold", this);
    fKillDoseThresholdCmd->SetGuidance("Set simple cell kill dose threshold.");
    fKillDoseThresholdCmd->SetUnitCategory("Dose");
  }

  ~TherapyMessenger()
  {
    delete fKillDoseThresholdCmd;
    delete fBoronPPMCmd;
    delete fNucleusRadiusCmd;
    delete fCellDiameterCmd;
    delete fCellPitchCmd;
    delete fCellPatchSizeCmd;
    delete fBeamRadiusCmd;
    delete fSourceDirectionCmd;
    delete fSourcePositionCmd;
    delete fNormalPositionCmd;
    delete fTumorPositionCmd;
    delete fSaveStepTreeCmd;
    delete fOutputFileCmd;
    delete fBoronModeCmd;
    delete fModeCmd;
    delete fDirectory;
  }

  void SetNewValue(G4UIcommand* command, G4String value) override
  {
    if (command == fModeCmd) fConfig->SetMode(value);
    else if (command == fBoronModeCmd) fConfig->SetBoronMode(value);
    else if (command == fOutputFileCmd) fConfig->SetOutputFile(value);
    else if (command == fSaveStepTreeCmd) fConfig->SetSaveStepTree(fSaveStepTreeCmd->GetNewBoolValue(value));
    else if (command == fTumorPositionCmd) fConfig->SetTumorPosition(fTumorPositionCmd->GetNew3VectorValue(value));
    else if (command == fNormalPositionCmd) fConfig->SetNormalPosition(fNormalPositionCmd->GetNew3VectorValue(value));
    else if (command == fSourcePositionCmd) fConfig->SetSourcePosition(fSourcePositionCmd->GetNew3VectorValue(value));
    else if (command == fSourceDirectionCmd) fConfig->SetSourceDirection(fSourceDirectionCmd->GetNew3VectorValue(value));
    else if (command == fBeamRadiusCmd) fConfig->SetBeamRadius(fBeamRadiusCmd->GetNewDoubleValue(value));
    else if (command == fCellPatchSizeCmd) fConfig->SetCellPatchSize(fCellPatchSizeCmd->GetNew3VectorValue(value));
    else if (command == fCellPitchCmd) fConfig->SetCellPitch(fCellPitchCmd->GetNewDoubleValue(value));
    else if (command == fCellDiameterCmd) fConfig->SetCellDiameter(fCellDiameterCmd->GetNewDoubleValue(value));
    else if (command == fNucleusRadiusCmd) fConfig->SetNucleusRadius(fNucleusRadiusCmd->GetNewDoubleValue(value));
    else if (command == fBoronPPMCmd) fConfig->SetBoronPPM(fBoronPPMCmd->GetNewDoubleValue(value));
    else if (command == fKillDoseThresholdCmd) fConfig->SetKillDoseThreshold(fKillDoseThresholdCmd->GetNewDoubleValue(value));
  }

private:
  TherapyConfig* fConfig;
  G4UIdirectory* fDirectory = nullptr;
  G4UIcmdWithAString* fModeCmd = nullptr;
  G4UIcmdWithAString* fBoronModeCmd = nullptr;
  G4UIcmdWithAString* fOutputFileCmd = nullptr;
  G4UIcmdWithABool* fSaveStepTreeCmd = nullptr;
  G4UIcmdWith3VectorAndUnit* fTumorPositionCmd = nullptr;
  G4UIcmdWith3VectorAndUnit* fNormalPositionCmd = nullptr;
  G4UIcmdWith3VectorAndUnit* fSourcePositionCmd = nullptr;
  G4UIcmdWith3Vector* fSourceDirectionCmd = nullptr;
  G4UIcmdWithADoubleAndUnit* fBeamRadiusCmd = nullptr;
  G4UIcmdWith3VectorAndUnit* fCellPatchSizeCmd = nullptr;
  G4UIcmdWithADoubleAndUnit* fCellPitchCmd = nullptr;
  G4UIcmdWithADoubleAndUnit* fCellDiameterCmd = nullptr;
  G4UIcmdWithADoubleAndUnit* fNucleusRadiusCmd = nullptr;
  G4UIcmdWithADouble* fBoronPPMCmd = nullptr;
  G4UIcmdWithADoubleAndUnit* fKillDoseThresholdCmd = nullptr;
};

TherapyConfig& TherapyConfig::Instance()
{
  static TherapyConfig instance;
  return instance;
}

TherapyConfig::TherapyConfig()
  : fMode(TherapyMode::Problem1),
    fBoronMode(BoronMode::None),
    fOutputFile("output.root"),
    fSaveStepTree(false),
    fTumorSize(20. * mm, 10. * mm, 30. * mm),
    fTumorPosition(-45. * mm, -45. * mm, 30. * mm),
    fNormalPosition(45. * mm, -45. * mm, 30. * mm),
    fSourcePosition(0., -600. * mm, 30. * mm),
    fSourceDirection(0., 1., 0.),
    fBeamRadius(5. * mm),
    fCellPatchSize(200. * micrometer, 200. * micrometer, 200. * micrometer),
    fCellPitch(12. * micrometer),
    fCellDiameter(10. * micrometer),
    fNucleusRadius(2.5 * micrometer),
    fShellThickness(1. * micrometer),
    fBoronPPM(1000.),
    fKillDoseThreshold(2. * gray)
{
  fMessenger = std::make_unique<TherapyMessenger>(this);
}

TherapyConfig::~TherapyConfig() = default;

void TherapyConfig::SetMode(const G4String& value)
{
  if (value == "problem2") {
    fMode = TherapyMode::Problem2;
  } else {
    fMode = TherapyMode::Problem1;
  }
}

void TherapyConfig::SetBoronMode(const G4String& value)
{
  if (value == "uniform") {
    fBoronMode = BoronMode::Uniform;
  } else if (value == "shell") {
    fBoronMode = BoronMode::Shell;
  } else {
    fBoronMode = BoronMode::None;
  }
}

void TherapyConfig::SetSourceDirection(const G4ThreeVector& value)
{
  if (value.mag2() > 0.) {
    fSourceDirection = value.unit();
  }
}

G4int TherapyConfig::ModeCode() const
{
  return static_cast<G4int>(fMode);
}

G4int TherapyConfig::BoronModeCode() const
{
  return static_cast<G4int>(fBoronMode);
}

G4String TherapyConfig::ModeName() const
{
  return fMode == TherapyMode::Problem2 ? "problem2" : "problem1";
}

G4String TherapyConfig::BoronModeName() const
{
  if (fBoronMode == BoronMode::Uniform) return "uniform";
  if (fBoronMode == BoronMode::Shell) return "shell";
  return "none";
}
