#include "TherapyAnalysisManager.hh"

#include "TherapyConfig.hh"

#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"

#include "CLHEP/Units/PhysicalConstants.h"

#include <algorithm>
#include <cmath>

namespace {
constexpr G4int kRunTree = 0;
constexpr G4int kEventTree = 1;
constexpr G4int kCellTree = 2;
constexpr G4int kStepTree = 3;

G4int CellTypeCode(CellType type)
{
  return type == CellType::Tumor ? 1 : 0;
}
}

void EventAccumulator::Reset()
{
  edepTotal = 0.;
  edepTumorRegion = 0.;
  edepNormalRegion = 0.;
  edepTumorCells = 0.;
  edepNormalCells = 0.;
  edepNucleusTumor = 0.;
  edepNucleusNormal = 0.;
  edepBoronRegion = 0.;
  nAlpha = 0;
  nLi7 = 0;
  nGamma = 0;
  nElectron = 0;
}

TherapyAnalysisManager& TherapyAnalysisManager::Instance()
{
  static TherapyAnalysisManager instance;
  return instance;
}

G4double TherapyAnalysisManager::DoseGy(G4double edep, G4double mass) const
{
  if (mass <= 0.) return 0.;
  return (edep / mass) / gray;
}

void TherapyAnalysisManager::BeginRun(G4int nEvents, const std::vector<CellInfo>& cells)
{
  const auto& config = TherapyConfig::Instance();
  auto analysis = G4AnalysisManager::Instance();
  analysis->SetDefaultFileType("root");
  analysis->SetVerboseLevel(1);
  analysis->OpenFile(config.GetOutputFile());

  fCells.clear();
  for (const auto& cell : cells) {
    CellAccumulator acc;
    acc.info = cell;
    fCells[cell.id] = acc;
  }

  const G4ThreeVector tumorSize = config.GetTumorSize();
  constexpr G4double density = 1.0 * g / cm3;
  fTumorRegionMass = density * tumorSize.x() * tumorSize.y() * tumorSize.z();
  const G4double torsoVolume = (260. * mm) * (120. * mm) * (500. * mm);
  const G4double neckRadius = 50. * mm;
  const G4double headRadius = 90. * mm;
  const G4double headCenterZ = 430. * mm;
  const G4double neckBottomZ = 250. * mm;
  const G4double headNeckIntersectionOffset = std::sqrt(headRadius * headRadius - neckRadius * neckRadius);
  const G4double neckTopZ = headCenterZ - headNeckIntersectionOffset;
  const G4double neckVolume = CLHEP::pi * neckRadius * neckRadius * (neckTopZ - neckBottomZ);
  const G4double headVolume = 4. * CLHEP::pi * headRadius * headRadius * headRadius / 3.;
  const G4double headNeckCapHeight = headRadius - headNeckIntersectionOffset;
  const G4double headNeckCutVolume =
    CLHEP::pi * headNeckCapHeight * headNeckCapHeight * (headRadius - headNeckCapHeight / 3.);
  const G4double legVolume = 2. * CLHEP::pi * (55. * mm) * (55. * mm) * (820. * mm);
  const G4double phantomVolume = torsoVolume + neckVolume + (headVolume - headNeckCutVolume) + legVolume;
  fNormalRegionMass = density * std::max(0., phantomVolume - tumorSize.x() * tumorSize.y() * tumorSize.z());

  CreateObjects(config.GetSaveStepTree());
  FillRunTree(nEvents, static_cast<G4int>(cells.size()));
  fEvent.Reset();
  fIsOpen = true;
}

void TherapyAnalysisManager::CreateObjects(G4bool saveStepTree)
{
  auto analysis = G4AnalysisManager::Instance();

  analysis->CreateNtuple("RunTree", "Run configuration");
  analysis->CreateNtupleIColumn("mode");
  analysis->CreateNtupleIColumn("boronMode");
  analysis->CreateNtupleIColumn("nEvents");
  analysis->CreateNtupleIColumn("nCells");
  analysis->CreateNtupleDColumn("tumorSizeX_mm");
  analysis->CreateNtupleDColumn("tumorSizeY_mm");
  analysis->CreateNtupleDColumn("tumorSizeZ_mm");
  analysis->CreateNtupleDColumn("cellDiameter_um");
  analysis->CreateNtupleDColumn("cellPitch_um");
  analysis->CreateNtupleDColumn("boronPPM");
  analysis->CreateNtupleDColumn("killDoseThreshold_Gy");
  analysis->FinishNtuple();

  analysis->CreateNtuple("EventTree", "Per-event scoring");
  analysis->CreateNtupleIColumn("eventID");
  analysis->CreateNtupleDColumn("edepTotal_MeV");
  analysis->CreateNtupleDColumn("edepTumorRegion_MeV");
  analysis->CreateNtupleDColumn("edepNormalRegion_MeV");
  analysis->CreateNtupleDColumn("doseTumorRegion_Gy");
  analysis->CreateNtupleDColumn("doseNormalRegion_Gy");
  analysis->CreateNtupleDColumn("edepTumorCells_MeV");
  analysis->CreateNtupleDColumn("edepNormalCells_MeV");
  analysis->CreateNtupleDColumn("edepNucleusTumor_MeV");
  analysis->CreateNtupleDColumn("edepNucleusNormal_MeV");
  analysis->CreateNtupleDColumn("edepBoronRegion_MeV");
  analysis->CreateNtupleIColumn("nAlpha");
  analysis->CreateNtupleIColumn("nLi7");
  analysis->CreateNtupleIColumn("nGamma");
  analysis->CreateNtupleIColumn("nElectron");
  analysis->FinishNtuple();

  analysis->CreateNtuple("CellTree", "Accumulated cell scoring");
  analysis->CreateNtupleIColumn("cellID");
  analysis->CreateNtupleIColumn("cellType");
  analysis->CreateNtupleDColumn("x_mm");
  analysis->CreateNtupleDColumn("y_mm");
  analysis->CreateNtupleDColumn("z_mm");
  analysis->CreateNtupleDColumn("edepCell_MeV");
  analysis->CreateNtupleDColumn("doseCell_Gy");
  analysis->CreateNtupleDColumn("edepNucleus_MeV");
  analysis->CreateNtupleDColumn("doseNucleus_Gy");
  analysis->CreateNtupleDColumn("edepBoronRegion_MeV");
  analysis->CreateNtupleDColumn("doseBoronRegion_Gy");
  analysis->CreateNtupleIColumn("hits");
  analysis->CreateNtupleIColumn("alphaHits");
  analysis->CreateNtupleIColumn("liHits");
  analysis->CreateNtupleIColumn("killedFlag");
  analysis->FinishNtuple();

  if (saveStepTree) {
    analysis->CreateNtuple("StepTree", "Detailed step scoring");
    analysis->CreateNtupleIColumn("eventID");
    analysis->CreateNtupleIColumn("trackID");
    analysis->CreateNtupleIColumn("cellID");
    analysis->CreateNtupleDColumn("x_mm");
    analysis->CreateNtupleDColumn("y_mm");
    analysis->CreateNtupleDColumn("z_mm");
    analysis->CreateNtupleDColumn("edep_MeV");
    analysis->CreateNtupleDColumn("stepLength_um");
    analysis->CreateNtupleDColumn("LET_MeV_per_um");
    analysis->FinishNtuple();
  }

  analysis->CreateH1("hDoseTumor", "Tumor region event dose;Dose (Gy);Events", 100, 0., 5.);
  analysis->CreateH1("hDoseNormal", "Normal tissue event dose;Dose (Gy);Events", 100, 0., 5.);
  analysis->CreateH1("hDoseTumorCells", "Tumor cell dose;Dose (Gy);Cells", 100, 0., 20.);
  analysis->CreateH1("hDoseNormalCells", "Normal cell dose;Dose (Gy);Cells", 100, 0., 20.);
  analysis->CreateH1("hDoseNucleusTumor", "Tumor nucleus dose;Dose (Gy);Cells", 100, 0., 20.);
  analysis->CreateH1("hDoseNucleusNormal", "Normal nucleus dose;Dose (Gy);Cells", 100, 0., 20.);
  analysis->CreateH1("hLETTumor", "Tumor LET;LET (MeV/um);Steps", 200, 0., 2.);
  analysis->CreateH1("hLETNormal", "Normal LET;LET (MeV/um);Steps", 200, 0., 2.);
  analysis->CreateH1("hDepthDose", "Depth-dose profile;y (mm);Energy deposit (MeV)", 200, -200., 200.);
  analysis->CreateH1("hSecondaryParticles", "Secondaries;type;count", 4, 0., 4.);
  analysis->CreateH3("hVoxelDose3D", "Tumor/normal voxel edep;x (mm);y (mm);z (mm)",
                     100, -140., 140., 100, -80., 80., 80, -20., 100.);
}

void TherapyAnalysisManager::FillRunTree(G4int nEvents, G4int nCells)
{
  auto analysis = G4AnalysisManager::Instance();
  const auto& config = TherapyConfig::Instance();
  const G4ThreeVector tumorSize = config.GetTumorSize();
  G4int col = 0;
  analysis->FillNtupleIColumn(kRunTree, col++, config.ModeCode());
  analysis->FillNtupleIColumn(kRunTree, col++, config.BoronModeCode());
  analysis->FillNtupleIColumn(kRunTree, col++, nEvents);
  analysis->FillNtupleIColumn(kRunTree, col++, nCells);
  analysis->FillNtupleDColumn(kRunTree, col++, tumorSize.x() / mm);
  analysis->FillNtupleDColumn(kRunTree, col++, tumorSize.y() / mm);
  analysis->FillNtupleDColumn(kRunTree, col++, tumorSize.z() / mm);
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetCellDiameter() / micrometer);
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetCellPitch() / micrometer);
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetBoronPPM());
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetKillDoseThreshold() / gray);
  analysis->AddNtupleRow(kRunTree);
}

void TherapyAnalysisManager::BeginEvent()
{
  fEvent.Reset();
}

void TherapyAnalysisManager::EndEvent(G4int eventID)
{
  auto analysis = G4AnalysisManager::Instance();
  G4int col = 0;
  analysis->FillNtupleIColumn(kEventTree, col++, eventID);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepTotal / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepTumorRegion / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNormalRegion / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, DoseGy(fEvent.edepTumorRegion, fTumorRegionMass));
  analysis->FillNtupleDColumn(kEventTree, col++, DoseGy(fEvent.edepNormalRegion, fNormalRegionMass));
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepTumorCells / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNormalCells / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusTumor / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusNormal / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepBoronRegion / MeV);
  analysis->FillNtupleIColumn(kEventTree, col++, fEvent.nAlpha);
  analysis->FillNtupleIColumn(kEventTree, col++, fEvent.nLi7);
  analysis->FillNtupleIColumn(kEventTree, col++, fEvent.nGamma);
  analysis->FillNtupleIColumn(kEventTree, col++, fEvent.nElectron);
  analysis->AddNtupleRow(kEventTree);

  analysis->FillH1(0, DoseGy(fEvent.edepTumorRegion, fTumorRegionMass));
  analysis->FillH1(1, DoseGy(fEvent.edepNormalRegion, fNormalRegionMass));
}

void TherapyAnalysisManager::AddEnergyDeposit(G4double edep,
                                              G4double stepLength,
                                              const G4ThreeVector& position,
                                              G4int cellID,
                                              G4bool inTumorRegion,
                                              G4bool inNormalRegion,
                                              G4bool inPhantom,
                                              G4bool inNucleus,
                                              G4bool inBoronRegion,
                                              const G4String& particleName,
                                              const G4String&,
                                              const G4String&,
                                              G4int eventID,
                                              G4int trackID)
{
  if (edep <= 0.) return;

  auto analysis = G4AnalysisManager::Instance();
  fEvent.edepTotal += edep;

  if (inTumorRegion) fEvent.edepTumorRegion += edep;
  if (inNormalRegion) fEvent.edepNormalRegion += edep;

  const G4double let = stepLength > 0. ? (edep / MeV) / (stepLength / micrometer) : 0.;
  if (inTumorRegion) analysis->FillH1(6, let);
  if (inNormalRegion) analysis->FillH1(7, let);
  if (inPhantom) {
    analysis->FillH1(8, position.y() / mm, edep / MeV);
    analysis->FillH3(0, position.x() / mm, position.y() / mm, position.z() / mm, edep / MeV);
  }

  auto found = fCells.find(cellID);
  if (found != fCells.end()) {
    auto& cell = found->second;
    const G4bool isTumorCell = cell.info.type == CellType::Tumor;
    cell.edepCell += edep;
    cell.hits += 1;
    if (particleName == "alpha") cell.alphaHits += 1;
    if (particleName.find("Li7") != G4String::npos) cell.liHits += 1;

    if (isTumorCell) fEvent.edepTumorCells += edep;
    else fEvent.edepNormalCells += edep;

    if (inNucleus) {
      cell.edepNucleus += edep;
      if (isTumorCell) fEvent.edepNucleusTumor += edep;
      else fEvent.edepNucleusNormal += edep;
    }
    if (inBoronRegion) {
      cell.edepBoronRegion += edep;
      fEvent.edepBoronRegion += edep;
    }
  }

  if (TherapyConfig::Instance().GetSaveStepTree()) {
    G4int col = 0;
    analysis->FillNtupleIColumn(kStepTree, col++, eventID);
    analysis->FillNtupleIColumn(kStepTree, col++, trackID);
    analysis->FillNtupleIColumn(kStepTree, col++, cellID);
    analysis->FillNtupleDColumn(kStepTree, col++, position.x() / mm);
    analysis->FillNtupleDColumn(kStepTree, col++, position.y() / mm);
    analysis->FillNtupleDColumn(kStepTree, col++, position.z() / mm);
    analysis->FillNtupleDColumn(kStepTree, col++, edep / MeV);
    analysis->FillNtupleDColumn(kStepTree, col++, stepLength / micrometer);
    analysis->FillNtupleDColumn(kStepTree, col++, let);
    analysis->AddNtupleRow(kStepTree);
  }
}

void TherapyAnalysisManager::AddSecondary(const G4String& particleName)
{
  auto analysis = G4AnalysisManager::Instance();
  if (particleName == "alpha") {
    ++fEvent.nAlpha;
    analysis->FillH1(9, 0.5);
  } else if (particleName.find("Li7") != G4String::npos) {
    ++fEvent.nLi7;
    analysis->FillH1(9, 1.5);
  } else if (particleName == "gamma") {
    ++fEvent.nGamma;
    analysis->FillH1(9, 2.5);
  } else if (particleName == "e-") {
    ++fEvent.nElectron;
    analysis->FillH1(9, 3.5);
  }
}

void TherapyAnalysisManager::FillCellTree()
{
  auto analysis = G4AnalysisManager::Instance();
  const auto& config = TherapyConfig::Instance();
  for (const auto& item : fCells) {
    const auto& cell = item.second;
    const G4double doseCell = DoseGy(cell.edepCell, cell.info.mass);
    const G4double doseNucleus = DoseGy(cell.edepNucleus, cell.info.nucleusMass);
    const G4double doseBoron = DoseGy(cell.edepBoronRegion, cell.info.boronRegionMass);
    const G4int killed = doseCell >= config.GetKillDoseThreshold() / gray ? 1 : 0;

    G4int col = 0;
    analysis->FillNtupleIColumn(kCellTree, col++, cell.info.id);
    analysis->FillNtupleIColumn(kCellTree, col++, CellTypeCode(cell.info.type));
    analysis->FillNtupleDColumn(kCellTree, col++, cell.info.position.x() / mm);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.info.position.y() / mm);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.info.position.z() / mm);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.edepCell / MeV);
    analysis->FillNtupleDColumn(kCellTree, col++, doseCell);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.edepNucleus / MeV);
    analysis->FillNtupleDColumn(kCellTree, col++, doseNucleus);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.edepBoronRegion / MeV);
    analysis->FillNtupleDColumn(kCellTree, col++, doseBoron);
    analysis->FillNtupleIColumn(kCellTree, col++, cell.hits);
    analysis->FillNtupleIColumn(kCellTree, col++, cell.alphaHits);
    analysis->FillNtupleIColumn(kCellTree, col++, cell.liHits);
    analysis->FillNtupleIColumn(kCellTree, col++, killed);
    analysis->AddNtupleRow(kCellTree);

    if (cell.info.type == CellType::Tumor) {
      analysis->FillH1(2, doseCell);
      analysis->FillH1(4, doseNucleus);
    } else {
      analysis->FillH1(3, doseCell);
      analysis->FillH1(5, doseNucleus);
    }
  }
}

void TherapyAnalysisManager::EndRun()
{
  if (!fIsOpen) return;
  FillCellTree();
  auto analysis = G4AnalysisManager::Instance();
  analysis->Write();
  analysis->CloseFile();
  fIsOpen = false;
}
