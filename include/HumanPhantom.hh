#ifndef HUMAN_PHANTOM_HH
#define HUMAN_PHANTOM_HH

#include "globals.hh"

class G4LogicalVolume;
class G4Material;

struct HumanPhantomResult {
  G4LogicalVolume* torsoLogical = nullptr;
};

class HumanPhantom {
public:
  HumanPhantom(G4Material* material, G4bool checkOverlaps);
  HumanPhantomResult Build(G4LogicalVolume* worldLogical) const;

private:
  G4Material* fMaterial;
  G4bool fCheckOverlaps;
};

#endif
