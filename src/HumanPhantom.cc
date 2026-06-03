#include "HumanPhantom.hh"

#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4LogicalVolume.hh"
#include "G4Orb.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4Tubs.hh"
#include "G4VisAttributes.hh"

HumanPhantom::HumanPhantom(G4Material* material, G4bool checkOverlaps)
  : fMaterial(material), fCheckOverlaps(checkOverlaps)
{
}

HumanPhantomResult HumanPhantom::Build(G4LogicalVolume* worldLogical) const
{
  HumanPhantomResult result;

  auto torsoSolid = new G4Box("TorsoSolid", 130. * mm, 60. * mm, 250. * mm);
  auto torsoLogical = new G4LogicalVolume(torsoSolid, fMaterial, "TorsoLV");
  new G4PVPlacement(nullptr, G4ThreeVector(), torsoLogical, "Torso", worldLogical, false, 0, fCheckOverlaps);
  torsoLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.0, 0.75, 0.25, 0.35)));
  result.torsoLogical = torsoLogical;

  auto neckSolid = new G4Tubs("NeckSolid", 0., 50. * mm, 45. * mm, 0., 360. * deg);
  auto neckLogical = new G4LogicalVolume(neckSolid, fMaterial, "NeckLV");
  new G4PVPlacement(nullptr, G4ThreeVector(0., 0., 295. * mm), neckLogical, "Neck", worldLogical, false, 0, fCheckOverlaps);
  neckLogical->SetVisAttributes(new G4VisAttributes(G4Colour(1.0, 0.45, 0.0, 0.35)));

  auto headSolid = new G4Orb("HeadSolid", 90. * mm);
  auto headLogical = new G4LogicalVolume(headSolid, fMaterial, "HeadLV");
  new G4PVPlacement(nullptr, G4ThreeVector(0., 0., 430. * mm), headLogical, "Head", worldLogical, false, 0, fCheckOverlaps);
  headLogical->SetVisAttributes(new G4VisAttributes(G4Colour(1.0, 0.75, 0.0, 0.35)));

  auto legSolid = new G4Tubs("LegSolid", 0., 55. * mm, 410. * mm, 0., 360. * deg);
  auto legLogical = new G4LogicalVolume(legSolid, fMaterial, "LegLV");
  new G4PVPlacement(nullptr, G4ThreeVector(-65. * mm, 0., -660. * mm), legLogical, "LeftLeg", worldLogical, false, 1, fCheckOverlaps);
  new G4PVPlacement(nullptr, G4ThreeVector(65. * mm, 0., -660. * mm), legLogical, "RightLeg", worldLogical, false, 2, fCheckOverlaps);
  legLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.0, 0.60, 0.90, 0.35)));

  return result;
}
