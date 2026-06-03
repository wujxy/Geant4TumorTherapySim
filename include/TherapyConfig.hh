#ifndef THERAPY_CONFIG_HH
#define THERAPY_CONFIG_HH

#include "G4String.hh"
#include "G4ThreeVector.hh"
#include "globals.hh"

#include <memory>

class TherapyMessenger;

enum class TherapyMode {
  Problem1 = 0,
  Problem2 = 1
};

enum class BoronMode {
  None = 0,
  Uniform = 1,
  Shell = 2
};

class TherapyConfig {
public:
  static TherapyConfig& Instance();

  TherapyConfig(const TherapyConfig&) = delete;
  TherapyConfig& operator=(const TherapyConfig&) = delete;

  TherapyMode GetMode() const { return fMode; }
  BoronMode GetBoronMode() const { return fBoronMode; }

  void SetMode(const G4String& value);
  void SetBoronMode(const G4String& value);
  void SetOutputFile(const G4String& value) { fOutputFile = value; }
  void SetSaveStepTree(G4bool value) { fSaveStepTree = value; }
  void SetTumorPosition(const G4ThreeVector& value) { fTumorPosition = value; }
  void SetNormalPosition(const G4ThreeVector& value) { fNormalPosition = value; }
  void SetSourcePosition(const G4ThreeVector& value) { fSourcePosition = value; }
  void SetSourceDirection(const G4ThreeVector& value);
  void SetBeamRadius(G4double value) { fBeamRadius = value; }
  void SetCellPatchSize(const G4ThreeVector& value) { fCellPatchSize = value; }
  void SetCellPitch(G4double value) { fCellPitch = value; }
  void SetCellDiameter(G4double value) { fCellDiameter = value; }
  void SetNucleusRadius(G4double value) { fNucleusRadius = value; }
  void SetBoronPPM(G4double value) { fBoronPPM = value; }
  void SetKillDoseThreshold(G4double value) { fKillDoseThreshold = value; }

  G4String GetOutputFile() const { return fOutputFile; }
  G4bool GetSaveStepTree() const { return fSaveStepTree; }
  G4ThreeVector GetTumorPosition() const { return fTumorPosition; }
  G4ThreeVector GetNormalPosition() const { return fNormalPosition; }
  G4ThreeVector GetSourcePosition() const { return fSourcePosition; }
  G4ThreeVector GetSourceDirection() const { return fSourceDirection; }
  G4double GetBeamRadius() const { return fBeamRadius; }
  G4ThreeVector GetTumorSize() const { return fTumorSize; }
  G4ThreeVector GetCellPatchSize() const { return fCellPatchSize; }
  G4double GetCellPitch() const { return fCellPitch; }
  G4double GetCellDiameter() const { return fCellDiameter; }
  G4double GetCellRadius() const { return 0.5 * fCellDiameter; }
  G4double GetNucleusRadius() const { return fNucleusRadius; }
  G4double GetShellThickness() const { return fShellThickness; }
  G4double GetBoronPPM() const { return fBoronPPM; }
  G4double GetKillDoseThreshold() const { return fKillDoseThreshold; }

  G4int ModeCode() const;
  G4int BoronModeCode() const;
  G4String ModeName() const;
  G4String BoronModeName() const;

private:
  TherapyConfig();
  ~TherapyConfig();

  TherapyMode fMode;
  BoronMode fBoronMode;
  G4String fOutputFile;
  G4bool fSaveStepTree;

  G4ThreeVector fTumorSize;
  G4ThreeVector fTumorPosition;
  G4ThreeVector fNormalPosition;
  G4ThreeVector fSourcePosition;
  G4ThreeVector fSourceDirection;
  G4double fBeamRadius;

  G4ThreeVector fCellPatchSize;
  G4double fCellPitch;
  G4double fCellDiameter;
  G4double fNucleusRadius;
  G4double fShellThickness;
  G4double fBoronPPM;
  G4double fKillDoseThreshold;

  std::unique_ptr<TherapyMessenger> fMessenger;
};

#endif
