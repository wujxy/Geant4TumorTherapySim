#include "DetectorConstruction.hh"

#include "CellModel.hh"
#include "HumanPhantom.hh"
#include "TherapyConfig.hh"
#include "TumorModel.hh"

#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4Element.hh"
#include "G4Isotope.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"

#include <algorithm>

DetectorConstruction::DetectorConstruction() = default;

void DetectorConstruction::DefineMaterials()
{
  auto nist = G4NistManager::Instance();
  fWater = nist->FindOrBuildMaterial("G4_WATER");
  fWorldMaterial = nist->FindOrBuildMaterial("G4_AIR");

  auto b10 = new G4Isotope("B10", 5, 10, 10.012937 * g / mole);
  auto b10Element = new G4Element("EnrichedB10", "B10", 1);
  b10Element->AddIsotope(b10, 100. * perCent);

  const auto& config = TherapyConfig::Instance();
  const G4double boronFraction = std::max(0.0, config.GetBoronPPM()) * 1.e-6;
  fBoronWater = new G4Material("B10_Borated_Water", 1.0 * g / cm3, 2);
  fBoronWater->AddMaterial(fWater, std::max(0.0, 1.0 - boronFraction));
  fBoronWater->AddElement(b10Element, boronFraction);
}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  fCells.clear();
  DefineMaterials();

  const auto& config = TherapyConfig::Instance();
  const G4bool checkOverlaps = true;

  auto worldSolid = new G4Box("WorldSolid", 1.5 * m, 1.5 * m, 1.5 * m);
  auto worldLogical = new G4LogicalVolume(worldSolid, fWorldMaterial, "WorldLV");
  auto worldPhysical = new G4PVPlacement(nullptr, G4ThreeVector(), worldLogical, "World", nullptr, false, 0, checkOverlaps);
  worldLogical->SetVisAttributes(G4VisAttributes::GetInvisible());

  HumanPhantom phantom(fWater, checkOverlaps);
  auto phantomResult = phantom.Build(worldLogical);

  TumorModel regionBuilder(fWater, checkOverlaps);
  auto tumorLogical = regionBuilder.BuildRegion(phantomResult.torsoLogical,
                                                "TumorRegion",
                                                config.GetTumorSize(),
                                                config.GetTumorPosition(),
                                                G4Colour(1.0, 0.0, 0.0, 0.45),
                                                10);
  auto normalLogical = regionBuilder.BuildRegion(phantomResult.torsoLogical,
                                                 "NormalRegion",
                                                 config.GetTumorSize(),
                                                 config.GetNormalPosition(),
                                                 G4Colour(0.35, 0.7, 1.0, 0.35),
                                                 20);

  CellModel cellModel(fWater, fBoronWater, checkOverlaps);
  if (config.GetMode() == TherapyMode::Problem2) {
    cellModel.BuildPatch(tumorLogical, config.GetTumorPosition(), CellType::Tumor, 1, fCells,
                         G4ThreeVector(-120. * micrometer, 0., 0.));
    cellModel.BuildPatch(tumorLogical, config.GetTumorPosition(), CellType::Normal, 100000, fCells,
                         G4ThreeVector(120. * micrometer, 0., 0.));
  } else {
    cellModel.BuildPatch(tumorLogical, config.GetTumorPosition(), CellType::Tumor, 1, fCells);
    cellModel.BuildPatch(normalLogical, config.GetNormalPosition(), CellType::Normal, 100000, fCells);
  }

  return worldPhysical;
}
