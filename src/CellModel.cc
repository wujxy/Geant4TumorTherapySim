#include "CellModel.hh"

#include "G4LogicalVolume.hh"
#include "G4Orb.hh"
#include "G4PVPlacement.hh"
#include "G4Sphere.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"

#include "CLHEP/Units/PhysicalConstants.h"

#include <algorithm>
#include <cmath>

namespace {
G4double SphereMass(G4double radius)
{
  constexpr G4double density = 1.0 * g / cm3;
  const G4double volume = 4.0 * CLHEP::pi * radius * radius * radius / 3.0;
  return density * volume;
}

G4int CountCells(G4double patchSize, G4double pitch, G4double radius)
{
  const G4double usable = std::max(0.0, patchSize - 2.0 * radius);
  return std::max(1, static_cast<G4int>(std::floor(usable / pitch)) + 1);
}
}

CellModel::CellModel(G4Material* water, G4Material* boronWater, G4bool checkOverlaps)
  : fWater(water), fBoronWater(boronWater), fCheckOverlaps(checkOverlaps)
{
}

G4LogicalVolume* CellModel::BuildSimpleCellLogical(const G4String& name) const
{
  const auto& config = TherapyConfig::Instance();
  auto solid = new G4Orb(name + "Solid", config.GetCellRadius());
  auto logical = new G4LogicalVolume(solid, fWater, name + "LV");
  logical->SetVisAttributes(new G4VisAttributes(G4Colour(0.55, 0.85, 0.55, 0.45)));
  return logical;
}

G4LogicalVolume* CellModel::BuildDetailedCellLogical(const G4String& name,
                                                     CellType cellType,
                                                     BoronMode boronMode) const
{
  const auto& config = TherapyConfig::Instance();
  const G4double cellRadius = config.GetCellRadius();
  const G4double nucleusRadius = config.GetNucleusRadius();
  const G4double innerRadius = std::max(nucleusRadius + 0.1 * micrometer, cellRadius - config.GetShellThickness());
  const G4bool isTumor = cellType == CellType::Tumor;

  G4Material* outerMaterial = fWater;
  if (isTumor && (boronMode == BoronMode::Uniform || boronMode == BoronMode::Shell)) {
    outerMaterial = fBoronWater;
  }

  auto outerSolid = new G4Orb(name + "OuterSolid", cellRadius);
  auto outerLogical = new G4LogicalVolume(outerSolid, outerMaterial, name + "LV");
  outerLogical->SetVisAttributes(new G4VisAttributes(isTumor ? G4Colour(0.9, 0.2, 0.1, 0.55)
                                                              : G4Colour(0.55, 0.85, 0.55, 0.45)));

  if (isTumor && boronMode == BoronMode::Shell) {
    auto innerSolid = new G4Orb(name + "CytoplasmSolid", innerRadius);
    auto innerLogical = new G4LogicalVolume(innerSolid, fWater, name + "CytoplasmLV");
    new G4PVPlacement(nullptr, G4ThreeVector(), innerLogical, name + "Cytoplasm", outerLogical, false, 0, fCheckOverlaps);
    innerLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.95, 0.65, 0.35, 0.45)));

    auto nucleusSolid = new G4Orb(name + "NucleusSolid", nucleusRadius);
    auto nucleusLogical = new G4LogicalVolume(nucleusSolid, fWater, name + "NucleusLV");
    new G4PVPlacement(nullptr, G4ThreeVector(), nucleusLogical, name + "Nucleus", innerLogical, false, 0, fCheckOverlaps);
    nucleusLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.2, 0.1, 0.8, 0.7)));
  } else {
    G4Material* nucleusMaterial = (isTumor && boronMode == BoronMode::Uniform) ? fBoronWater : fWater;
    auto nucleusSolid = new G4Orb(name + "NucleusSolid", nucleusRadius);
    auto nucleusLogical = new G4LogicalVolume(nucleusSolid, nucleusMaterial, name + "NucleusLV");
    new G4PVPlacement(nullptr, G4ThreeVector(), nucleusLogical, name + "Nucleus", outerLogical, false, 0, fCheckOverlaps);
    nucleusLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.2, 0.1, 0.8, 0.7)));
  }

  return outerLogical;
}

void CellModel::BuildPatch(G4LogicalVolume* mother,
                           const G4ThreeVector& motherGlobalPosition,
                           CellType cellType,
                           G4int firstCellID,
                           std::vector<CellInfo>& cells,
                           const G4ThreeVector& patchCenter) const
{
  const auto& config = TherapyConfig::Instance();
  const G4bool detailed = config.GetMode() == TherapyMode::Problem2;
  const BoronMode boronMode = config.GetBoronMode();
  const G4String prefix = cellType == CellType::Tumor ? "TumorCell" : "NormalCell";

  G4LogicalVolume* cellLogical = detailed
    ? BuildDetailedCellLogical(prefix, cellType, boronMode)
    : BuildSimpleCellLogical(prefix);

  const G4double radius = config.GetCellRadius();
  const G4ThreeVector patchSize = config.GetCellPatchSize();
  const G4double pitch = config.GetCellPitch();
  const G4int nx = CountCells(patchSize.x(), pitch, radius);
  const G4int ny = CountCells(patchSize.y(), pitch, radius);
  const G4int nz = CountCells(patchSize.z(), pitch, radius);

  const G4double cellMass = SphereMass(radius);
  const G4double nucleusMass = detailed ? SphereMass(config.GetNucleusRadius()) : 0.;
  const G4double shellMass = detailed ? std::max(0.0, cellMass - SphereMass(radius - config.GetShellThickness())) : 0.;

  G4int id = firstCellID;
  for (G4int ix = 0; ix < nx; ++ix) {
    for (G4int iy = 0; iy < ny; ++iy) {
      for (G4int iz = 0; iz < nz; ++iz) {
        const G4double x = (ix - 0.5 * (nx - 1)) * pitch;
        const G4double y = (iy - 0.5 * (ny - 1)) * pitch;
        const G4double z = (iz - 0.5 * (nz - 1)) * pitch;
        const G4ThreeVector localPosition(x, y, z);
        new G4PVPlacement(nullptr, patchCenter + localPosition, cellLogical, prefix, mother, false, id, false);

        CellInfo info;
        info.id = id;
        info.type = cellType;
        info.position = motherGlobalPosition + patchCenter + localPosition;
        info.mass = cellMass;
        info.nucleusMass = nucleusMass;
        info.boronRegionMass = (cellType == CellType::Tumor && boronMode == BoronMode::Shell) ? shellMass : cellMass;
        cells.push_back(info);
        ++id;
      }
    }
  }
}
