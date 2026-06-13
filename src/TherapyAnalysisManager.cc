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
constexpr G4double kCellLocalSamplingStep = 0.1 * micrometer;

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
  edepNucleusTumorGamma = 0.;
  edepNucleusTumorProton = 0.;
  edepNucleusTumorAlpha = 0.;
  edepNucleusTumorLi7 = 0.;
  edepNucleusNormalGamma = 0.;
  edepNucleusNormalProton = 0.;
  edepNucleusNormalAlpha = 0.;
  edepNucleusNormalLi7 = 0.;
  nAlpha = 0;
  nLi7 = 0;
  nGamma = 0;
  nElectron = 0;
  nAlphaWeighted = 0.;
  nLi7Weighted = 0.;
  nGammaWeighted = 0.;
  nElectronWeighted = 0.;
  forcedCaptureBranch = -1;
  forcedCaptureRadius = 0.;
  forcedInitialHighLET = 0.;
  primaryNeutronReachedTumor = 0;
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

G4ThreeVector TherapyAnalysisManager::GetCellCenter(G4int cellID) const
{
  auto it = fCells.find(cellID);
  if (it == fCells.end()) return G4ThreeVector();
  return it->second.info.position;
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
  const G4double neckEnvelopeHeight = 180. * mm;
  const G4double neckHeadOverlapVolume =
    2. * CLHEP::pi / 3. *
    (std::pow(headRadius, 3) - std::pow(headRadius * headRadius - neckRadius * neckRadius, 1.5));
  const G4double neckVolume =
    CLHEP::pi * neckRadius * neckRadius * neckEnvelopeHeight - neckHeadOverlapVolume;
  const G4double headVolume = 4. * CLHEP::pi * headRadius * headRadius * headRadius / 3.;
  const G4double legVolume = 2. * CLHEP::pi * (55. * mm) * (55. * mm) * (820. * mm);
  const G4double phantomVolume = torsoVolume + neckVolume + headVolume + legVolume;
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
  analysis->CreateNtupleIColumn("sourceMode");
  analysis->CreateNtupleIColumn("nEvents");
  analysis->CreateNtupleIColumn("nCells");
  analysis->CreateNtupleDColumn("tumorSizeX_mm");
  analysis->CreateNtupleDColumn("tumorSizeY_mm");
  analysis->CreateNtupleDColumn("tumorSizeZ_mm");
  analysis->CreateNtupleDColumn("cellDiameter_um");
  analysis->CreateNtupleDColumn("cellPitch_um");
  analysis->CreateNtupleDColumn("boronPPM");
  analysis->CreateNtupleDColumn("b10CaptureBias");
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
  analysis->CreateNtupleDColumn("nAlphaWeighted");
  analysis->CreateNtupleDColumn("nLi7Weighted");
  analysis->CreateNtupleDColumn("nGammaWeighted");
  analysis->CreateNtupleDColumn("nElectronWeighted");
  analysis->CreateNtupleDColumn("edepNucleusTumorGamma_MeV");
  analysis->CreateNtupleDColumn("edepNucleusTumorProton_MeV");
  analysis->CreateNtupleDColumn("edepNucleusTumorAlpha_MeV");
  analysis->CreateNtupleDColumn("edepNucleusTumorLi7_MeV");
  analysis->CreateNtupleDColumn("edepNucleusNormalGamma_MeV");
  analysis->CreateNtupleDColumn("edepNucleusNormalProton_MeV");
  analysis->CreateNtupleDColumn("edepNucleusNormalAlpha_MeV");
  analysis->CreateNtupleDColumn("edepNucleusNormalLi7_MeV");
  analysis->CreateNtupleIColumn("forcedCaptureBranch");
  analysis->CreateNtupleDColumn("forcedCaptureRadius_um");
  analysis->CreateNtupleDColumn("forcedInitialHighLET_MeV");
  analysis->CreateNtupleIColumn("primaryNeutronReachedTumor");
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
  analysis->CreateNtupleDColumn("edepNucleusGamma_MeV");
  analysis->CreateNtupleDColumn("edepNucleusProton_MeV");
  analysis->CreateNtupleDColumn("edepNucleusAlpha_MeV");
  analysis->CreateNtupleDColumn("edepNucleusLi7_MeV");
  analysis->CreateNtupleIColumn("alphaNucleusHits");
  analysis->CreateNtupleIColumn("liNucleusHits");
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
    analysis->CreateNtupleDColumn("weight");
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
  analysis->CreateH1("hDepthDose", "Depth dose;Depth y (mm);Deposited energy (MeV)", 200, -200., 200.);
  analysis->CreateH1("hSecondaryParticles", "Secondaries;type;count", 4, 0., 4.);
  // Cell-local radial 1D spectra (index 10, 11): edep per radial bin, all cells of one type stacked
  analysis->CreateH1("hCellRadialNormal",
                     "Normal cell radial edep;r (um);Deposited energy (MeV)", 50, 0., 5.);
  analysis->CreateH1("hCellRadialTumor",
                     "Tumor cell radial edep;r (um);Deposited energy (MeV)", 50, 0., 5.);
  analysis->CreateH3("hVoxelDose3D", "Tumor/normal voxel edep;x (mm);y (mm);z (mm)",
                     100, -80., 80., 100, -140., 140., 80, -20., 100.);
  // Cell-local (r_xy, z_local) 2D edep maps for stacked single-cell visualization (H2 index 0, 1)
  analysis->CreateH2("hCellLocalNormal",
                     "Normal cell local edep;r_xy (um);z_local (um);MeV",
                     50, 0., 5., 50, -5., 5.);
  analysis->CreateH2("hCellLocalTumor",
                     "Tumor cell local edep;r_xy (um);z_local (um);MeV",
                     50, 0., 5., 50, -5., 5.);
}

void TherapyAnalysisManager::FillRunTree(G4int nEvents, G4int nCells)
{
  auto analysis = G4AnalysisManager::Instance();
  const auto& config = TherapyConfig::Instance();
  const G4ThreeVector tumorSize = config.GetTumorSize();
  G4int col = 0;
  analysis->FillNtupleIColumn(kRunTree, col++, config.ModeCode());
  analysis->FillNtupleIColumn(kRunTree, col++, config.BoronModeCode());
  analysis->FillNtupleIColumn(kRunTree, col++, config.SourceModeCode());
  analysis->FillNtupleIColumn(kRunTree, col++, nEvents);
  analysis->FillNtupleIColumn(kRunTree, col++, nCells);
  analysis->FillNtupleDColumn(kRunTree, col++, tumorSize.x() / mm);
  analysis->FillNtupleDColumn(kRunTree, col++, tumorSize.y() / mm);
  analysis->FillNtupleDColumn(kRunTree, col++, tumorSize.z() / mm);
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetCellDiameter() / micrometer);
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetCellPitch() / micrometer);
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetBoronPPM());
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetB10CaptureBias());
  analysis->FillNtupleDColumn(kRunTree, col++, config.GetKillDoseThreshold() / gray);
  analysis->AddNtupleRow(kRunTree);
}

void TherapyAnalysisManager::BeginEvent()
{
  fEvent.Reset();
  fEvent.forcedCaptureBranch = fPendingForcedCaptureBranch;
  fEvent.forcedCaptureRadius = fPendingForcedCaptureRadius;
  fEvent.forcedInitialHighLET = fPendingForcedInitialHighLET;
  fPendingForcedCaptureBranch = -1;
  fPendingForcedCaptureRadius = 0.;
  fPendingForcedInitialHighLET = 0.;
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
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.nAlphaWeighted);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.nLi7Weighted);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.nGammaWeighted);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.nElectronWeighted);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusTumorGamma / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusTumorProton / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusTumorAlpha / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusTumorLi7 / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusNormalGamma / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusNormalProton / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusNormalAlpha / MeV);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.edepNucleusNormalLi7 / MeV);
  analysis->FillNtupleIColumn(kEventTree, col++, fEvent.forcedCaptureBranch);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.forcedCaptureRadius / micrometer);
  analysis->FillNtupleDColumn(kEventTree, col++, fEvent.forcedInitialHighLET / MeV);
  analysis->FillNtupleIColumn(kEventTree, col++, fEvent.primaryNeutronReachedTumor);
  analysis->AddNtupleRow(kEventTree);

  analysis->FillH1(0, DoseGy(fEvent.edepTumorRegion, fTumorRegionMass));
  analysis->FillH1(1, DoseGy(fEvent.edepNormalRegion, fNormalRegionMass));
}

void TherapyAnalysisManager::AddEnergyDeposit(G4double edep,
                                              G4double stepLength,
                                              const G4ThreeVector& position,
                                              const G4ThreeVector& cellLocalPosition,
                                              const G4ThreeVector& cellLocalEndPosition,
                                              G4bool hasCellLocal,
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
                                              G4int trackID,
                                              G4double weight)
{
  if (edep <= 0.) return;

  auto analysis = G4AnalysisManager::Instance();
  const G4double weightedEdep = edep * weight;
  fEvent.edepTotal += weightedEdep;

  if (inTumorRegion) fEvent.edepTumorRegion += weightedEdep;
  if (inNormalRegion) fEvent.edepNormalRegion += weightedEdep;

  const G4double let = stepLength > 0. ? (edep / MeV) / (stepLength / micrometer) : 0.;
  if (inTumorRegion) analysis->FillH1(6, let, weight);
  if (inNormalRegion) analysis->FillH1(7, let, weight);
  if (inPhantom) {
    analysis->FillH1(8, position.y() / mm, weightedEdep / MeV);
    analysis->FillH3(0, position.x() / mm, position.y() / mm, position.z() / mm, weightedEdep / MeV);
  }

  auto found = fCells.find(cellID);
  if (found != fCells.end()) {
    auto& cell = found->second;
    const G4bool isTumorCell = cell.info.type == CellType::Tumor;
    const G4bool isAlpha = (particleName == "alpha");
    const G4bool isLi7 = (particleName.find("Li7") != G4String::npos);
    const G4bool isGamma = (particleName == "gamma" || particleName == "e-" || particleName == "e+");
    const G4bool isProton = (particleName == "proton");

    cell.edepCell += weightedEdep;
    cell.hits += 1;
    if (isAlpha) cell.alphaHits += 1;
    if (isLi7) cell.liHits += 1;

    if (isTumorCell) fEvent.edepTumorCells += weightedEdep;
    else fEvent.edepNormalCells += weightedEdep;

    if (inNucleus) {
      cell.edepNucleus += weightedEdep;
      if (isAlpha) {
        cell.edepNucleusAlpha += weightedEdep;
        cell.alphaNucleusHits += 1;
      } else if (isLi7) {
        cell.edepNucleusLi7 += weightedEdep;
        cell.liNucleusHits += 1;
      } else if (isProton) {
        cell.edepNucleusProton += weightedEdep;
      } else if (isGamma) {
        cell.edepNucleusGamma += weightedEdep;
      }
      if (isTumorCell) {
        fEvent.edepNucleusTumor += weightedEdep;
        if (isAlpha) fEvent.edepNucleusTumorAlpha += weightedEdep;
        else if (isLi7) fEvent.edepNucleusTumorLi7 += weightedEdep;
        else if (isProton) fEvent.edepNucleusTumorProton += weightedEdep;
        else if (isGamma) fEvent.edepNucleusTumorGamma += weightedEdep;
      } else {
        fEvent.edepNucleusNormal += weightedEdep;
        if (isAlpha) fEvent.edepNucleusNormalAlpha += weightedEdep;
        else if (isLi7) fEvent.edepNucleusNormalLi7 += weightedEdep;
        else if (isProton) fEvent.edepNucleusNormalProton += weightedEdep;
        else if (isGamma) fEvent.edepNucleusNormalGamma += weightedEdep;
      }
    }
    if (inBoronRegion) {
      cell.edepBoronRegion += weightedEdep;
      fEvent.edepBoronRegion += weightedEdep;
    }

    const G4bool fillCellLocal =
      TherapyConfig::Instance().GetSourceMode() == SourceMode::B10Capture && (isAlpha || isLi7);
    if (hasCellLocal && fillCellLocal) {
      const G4double edepMeV = weightedEdep / MeV;
      const G4ThreeVector localDelta = cellLocalEndPosition - cellLocalPosition;
      const G4int nSamples =
        std::max(1, static_cast<G4int>(std::ceil(localDelta.mag() / kCellLocalSamplingStep)));
      const G4double sampleEdepMeV = edepMeV / nSamples;
      for (G4int sample = 0; sample < nSamples; ++sample) {
        const G4double fraction = (sample + 0.5) / nSamples;
        const G4ThreeVector localSample = cellLocalPosition + fraction * localDelta;
        const G4double r_um = localSample.mag() / micrometer;
        const G4double rxy_planar_um =
          std::sqrt(localSample.x() * localSample.x() +
                    localSample.y() * localSample.y()) / micrometer;
        const G4double z_um = localSample.z() / micrometer;
        if (isTumorCell) {
          analysis->FillH1(11, r_um, sampleEdepMeV);
          analysis->FillH2(1, rxy_planar_um, z_um, sampleEdepMeV);
        } else {
          analysis->FillH1(10, r_um, sampleEdepMeV);
          analysis->FillH2(0, rxy_planar_um, z_um, sampleEdepMeV);
        }
      }
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
    analysis->FillNtupleDColumn(kStepTree, col++, weightedEdep / MeV);
    analysis->FillNtupleDColumn(kStepTree, col++, stepLength / micrometer);
    analysis->FillNtupleDColumn(kStepTree, col++, let);
    analysis->FillNtupleDColumn(kStepTree, col++, weight);
    analysis->AddNtupleRow(kStepTree);
  }
}

void TherapyAnalysisManager::AddSecondary(const G4String& particleName, G4double weight)
{
  auto analysis = G4AnalysisManager::Instance();
  if (particleName == "alpha") {
    ++fEvent.nAlpha;
    fEvent.nAlphaWeighted += weight;
    analysis->FillH1(9, 0.5, weight);
  } else if (particleName.find("Li7") != G4String::npos) {
    ++fEvent.nLi7;
    fEvent.nLi7Weighted += weight;
    analysis->FillH1(9, 1.5, weight);
  } else if (particleName == "gamma") {
    ++fEvent.nGamma;
    fEvent.nGammaWeighted += weight;
    analysis->FillH1(9, 2.5, weight);
  } else if (particleName == "e-") {
    ++fEvent.nElectron;
    fEvent.nElectronWeighted += weight;
    analysis->FillH1(9, 3.5, weight);
  }
}

void TherapyAnalysisManager::MarkPrimaryNeutronReachedTumor()
{
  fEvent.primaryNeutronReachedTumor = 1;
}

void TherapyAnalysisManager::RecordForcedCapture(G4int branch,
                                                 G4double radius,
                                                 G4double initialHighLET)
{
  fPendingForcedCaptureBranch = branch;
  fPendingForcedCaptureRadius = radius;
  fPendingForcedInitialHighLET = initialHighLET;
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
    analysis->FillNtupleDColumn(kCellTree, col++, cell.edepNucleusGamma / MeV);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.edepNucleusProton / MeV);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.edepNucleusAlpha / MeV);
    analysis->FillNtupleDColumn(kCellTree, col++, cell.edepNucleusLi7 / MeV);
    analysis->FillNtupleIColumn(kCellTree, col++, cell.alphaNucleusHits);
    analysis->FillNtupleIColumn(kCellTree, col++, cell.liNucleusHits);
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
