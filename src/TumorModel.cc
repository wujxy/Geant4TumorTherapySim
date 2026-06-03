#include "TumorModel.hh"

#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4VisAttributes.hh"

TumorModel::TumorModel(G4Material* material, G4bool checkOverlaps)
  : fMaterial(material), fCheckOverlaps(checkOverlaps)
{
}

G4LogicalVolume* TumorModel::BuildRegion(G4LogicalVolume* mother,
                                         const G4String& name,
                                         const G4ThreeVector& size,
                                         const G4ThreeVector& position,
                                         const G4Colour& colour,
                                         G4int copyNo) const
{
  auto solid = new G4Box(name + "Solid", 0.5 * size.x(), 0.5 * size.y(), 0.5 * size.z());
  auto logical = new G4LogicalVolume(solid, fMaterial, name + "LV");
  new G4PVPlacement(nullptr, position, logical, name, mother, false, copyNo, fCheckOverlaps);
  auto vis = new G4VisAttributes(colour);
  vis->SetForceSolid(true);
  logical->SetVisAttributes(vis);
  return logical;
}
