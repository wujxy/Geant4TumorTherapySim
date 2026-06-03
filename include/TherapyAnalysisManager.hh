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
  G4int nAlpha = 0;
  G4int nLi7 = 0;
  G4int nGamma = 0;
  G4int nElectron = 0;
};

struct CellAccumulator {
  CellInfo info;
  G4double edepCell = 0.;
  G4double edepNucleus = 0.;
  G4double edepBoronRegion = 0.;
  G4int hits = 0;
  G4int alphaHits = 0;
  G4int liHits = 0;
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
                        G4int cellID,
                        G4bool inTumorRegion,
                        G4bool inNormalRegion,
                        G4bool inNucleus,
                        G4bool inBoronRegion,
                        const G4String& particleName,
                        const G4String& processName,
                        const G4String& volumeName,
                        G4int eventID,
                        G4int trackID);

  void AddSecondary(const G4String& particleName);

  G4double TumorRegionMass() const { return fTumorRegionMass; }
  G4double NormalRegionMass() const { return fNormalRegionMass; }

private:
  TherapyAnalysisManager() = default;

  G4double DoseGy(G4double edep, G4double mass) const;
  void CreateObjects(G4bool saveStepTree);
  void FillRunTree(G4int nEvents, G4int nCells);
  void FillCellTree();

  EventAccumulator fEvent;
  std::map<G4int, CellAccumulator> fCells;
  G4double fTumorRegionMass = 0.;
  G4double fNormalRegionMass = 0.;
  G4bool fIsOpen = false;
};

#endif
