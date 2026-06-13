#ifndef THERAPY_ANALYSIS_MANAGER_HH
#define THERAPY_ANALYSIS_MANAGER_HH

#include "G4String.hh"
#include "G4ThreeVector.hh"
#include "globals.hh"

#include <map>
#include <vector>

enum class CellType {
  Normal = 0,
  Tumor = 1
};

struct CellInfo {
  G4int id = -1;
  CellType type = CellType::Normal;
  G4ThreeVector position;
  G4double mass = 0.;
  G4double nucleusMass = 0.;
  G4double boronRegionMass = 0.;
};

struct EventAccumulator {
  void Reset();

  G4double edepTotal = 0.;
  G4double edepTumorRegion = 0.;
  G4double edepNormalRegion = 0.;
  G4double edepTumorCells = 0.;
  G4double edepNormalCells = 0.;
  G4double edepNucleusTumor = 0.;
  G4double edepNucleusNormal = 0.;
  G4double edepBoronRegion = 0.;
  G4double edepNucleusTumorGamma = 0.;
  G4double edepNucleusTumorProton = 0.;
  G4double edepNucleusTumorAlpha = 0.;
  G4double edepNucleusTumorLi7 = 0.;
  G4double edepNucleusNormalGamma = 0.;
  G4double edepNucleusNormalProton = 0.;
  G4double edepNucleusNormalAlpha = 0.;
  G4double edepNucleusNormalLi7 = 0.;
  G4int nAlpha = 0;
  G4int nLi7 = 0;
  G4int nGamma = 0;
  G4int nElectron = 0;
  G4double nAlphaWeighted = 0.;
  G4double nLi7Weighted = 0.;
  G4double nGammaWeighted = 0.;
  G4double nElectronWeighted = 0.;
  G4int forcedCaptureBranch = -1;
  G4double forcedCaptureRadius = 0.;
  G4double forcedInitialHighLET = 0.;
  G4int primaryNeutronReachedTumor = 0;
};

struct CellAccumulator {
  CellInfo info;
  G4double edepCell = 0.;
  G4double edepNucleus = 0.;
  G4double edepBoronRegion = 0.;
  G4double edepNucleusGamma = 0.;
  G4double edepNucleusProton = 0.;
  G4double edepNucleusAlpha = 0.;
  G4double edepNucleusLi7 = 0.;
  G4int hits = 0;
  G4int alphaHits = 0;
  G4int liHits = 0;
  G4int alphaNucleusHits = 0;
  G4int liNucleusHits = 0;
};

class TherapyAnalysisManager {
public:
  static TherapyAnalysisManager& Instance();

  void BeginRun(G4int nEvents, const std::vector<CellInfo>& cells);
  void EndRun();
  void BeginEvent();
  void EndEvent(G4int eventID);

  void AddEnergyDeposit(G4double edep,
                        G4double stepLength,
                        const G4ThreeVector& position,
                        const G4ThreeVector& cellLocalPosition,
                        const G4ThreeVector& cellLocalEndPosition,
                        G4bool hasCellLocal,
                        G4int cellID,
                        G4bool inTumorRegion,
                        G4bool inNormalRegion,
                        G4bool inPhantom,
                        G4bool inNucleus,
                        G4bool inBoronRegion,
                        const G4String& particleName,
                        const G4String& processName,
                        const G4String& volumeName,
                        G4int eventID,
                        G4int trackID,
                        G4double weight);

  void AddSecondary(const G4String& particleName, G4double weight);
  void RecordForcedCapture(G4int branch, G4double radius, G4double initialHighLET);
  void MarkPrimaryNeutronReachedTumor();

  G4double TumorRegionMass() const { return fTumorRegionMass; }
  G4double NormalRegionMass() const { return fNormalRegionMass; }
  G4ThreeVector GetCellCenter(G4int cellID) const;

private:
  TherapyAnalysisManager() = default;

  G4double DoseGy(G4double edep, G4double mass) const;
  void CreateObjects(G4bool saveStepTree);
  void FillRunTree(G4int nEvents, G4int nCells);
  void FillCellTree();

  EventAccumulator fEvent;
  G4int fPendingForcedCaptureBranch = -1;
  G4double fPendingForcedCaptureRadius = 0.;
  G4double fPendingForcedInitialHighLET = 0.;
  std::map<G4int, CellAccumulator> fCells;
  G4double fTumorRegionMass = 0.;
  G4double fNormalRegionMass = 0.;
  G4bool fIsOpen = false;
};

#endif
