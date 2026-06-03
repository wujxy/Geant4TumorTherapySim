#ifndef TUMOR_MODEL_HH
#define TUMOR_MODEL_HH

#include "G4Colour.hh"
#include "G4ThreeVector.hh"
#include "globals.hh"

class G4LogicalVolume;
class G4Material;

class TumorModel {
public:
  TumorModel(G4Material* material, G4bool checkOverlaps);

  G4LogicalVolume* BuildRegion(G4LogicalVolume* mother,
                               const G4String& name,
                               const G4ThreeVector& size,
                               const G4ThreeVector& position,
                               const G4Colour& colour,
                               G4int copyNo) const;

private:
  G4Material* fMaterial;
  G4bool fCheckOverlaps;
};

#endif
