#ifndef CELL_MODEL_HH
#define CELL_MODEL_HH

#include "TherapyAnalysisManager.hh"
#include "TherapyConfig.hh"

#include "G4ThreeVector.hh"
#include "globals.hh"

#include <vector>

class G4LogicalVolume;
class G4Material;

class CellModel {
public:
  CellModel(G4Material* water, G4Material* boronWater, G4bool checkOverlaps);

  void BuildPatch(G4LogicalVolume* mother,
                  const G4ThreeVector& motherGlobalPosition,
                  CellType cellType,
                  G4int firstCellID,
                  std::vector<CellInfo>& cells) const;

private:
  G4LogicalVolume* BuildSimpleCellLogical(const G4String& name) const;
  G4LogicalVolume* BuildDetailedCellLogical(const G4String& name,
                                            CellType cellType,
                                            BoronMode boronMode) const;

  G4Material* fWater;
  G4Material* fBoronWater;
  G4bool fCheckOverlaps;
};

#endif
