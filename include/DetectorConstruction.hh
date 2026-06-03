#ifndef DETECTOR_CONSTRUCTION_HH
#define DETECTOR_CONSTRUCTION_HH

#include "TherapyAnalysisManager.hh"

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

#include <vector>

class G4LogicalVolume;
class G4Material;

class DetectorConstruction : public G4VUserDetectorConstruction {
public:
  DetectorConstruction();
  ~DetectorConstruction() override = default;

  G4VPhysicalVolume* Construct() override;

  const std::vector<CellInfo>& GetCells() const { return fCells; }

private:
  void DefineMaterials();

  G4Material* fWater = nullptr;
  G4Material* fBoronWater = nullptr;
  std::vector<CellInfo> fCells;
};

#endif
