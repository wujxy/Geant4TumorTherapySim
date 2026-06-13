#include "SteppingAction.hh"

#include "TherapyAnalysisManager.hh"
#include "TherapyConfig.hh"

#include "G4Event.hh"
#include "G4LogicalVolume.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4Track.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VProcess.hh"
#include "G4VTouchable.hh"

G4bool SteppingAction::TouchableContains(const G4VTouchable* touchable, const G4String& token) const
{
  if (!touchable) return false;
  for (G4int depth = 0; depth <= touchable->GetHistoryDepth(); ++depth) {
    auto volume = touchable->GetVolume(depth);
    if (!volume) continue;
    if (volume->GetName().find(token) != G4String::npos) return true;
    auto logical = volume->GetLogicalVolume();
    if (logical && logical->GetName().find(token) != G4String::npos) return true;
  }
  return false;
}

G4int SteppingAction::ExtractCellID(const G4VTouchable* touchable) const
{
  if (!touchable) return -1;
  for (G4int depth = 0; depth <= touchable->GetHistoryDepth(); ++depth) {
    auto volume = touchable->GetVolume(depth);
    if (!volume) continue;
    const G4String name = volume->GetName();
    const G4int copyNo = touchable->GetCopyNumber(depth);
    if ((name.find("TumorCell") != G4String::npos || name.find("NormalCell") != G4String::npos) && copyNo > 0) {
      return copyNo;
    }
  }
  return -1;
}

G4int SteppingAction::FindCellDepth(const G4VTouchable* touchable) const
{
  if (!touchable) return -1;
  for (G4int depth = 0; depth <= touchable->GetHistoryDepth(); ++depth) {
    auto volume = touchable->GetVolume(depth);
    if (!volume) continue;
    const G4String name = volume->GetName();
    if ((name.find("TumorCell") != G4String::npos || name.find("NormalCell") != G4String::npos)
        && name.find("Nucleus") == G4String::npos
        && name.find("Cytoplasm") == G4String::npos
        && touchable->GetCopyNumber(depth) > 0) {
      return depth;
    }
  }
  return -1;
}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  const G4double edep = step->GetTotalEnergyDeposit();
  const auto prePoint = step->GetPreStepPoint();
  const auto postPoint = step->GetPostStepPoint();
  const G4ThreeVector scoringPosition =
    0.5 * (prePoint->GetPosition() + postPoint->GetPosition());
  const auto touchable = prePoint->GetTouchable();
  const G4int cellID = ExtractCellID(touchable);

  const G4bool inTumorRegion = TouchableContains(touchable, "TumorRegion");
  const G4bool inPhantom =
    TouchableContains(touchable, "Torso") ||
    TouchableContains(touchable, "Neck") ||
    TouchableContains(touchable, "Head") ||
    TouchableContains(touchable, "Leg");
  const G4bool inNormalRegion = inPhantom && !inTumorRegion;
  const G4bool inNucleus = TouchableContains(touchable, "Nucleus");
  G4String currentVolumeName = "unknown";
  if (prePoint->GetPhysicalVolume()) {
    currentVolumeName = prePoint->GetPhysicalVolume()->GetName();
  }
  const auto boronMode = TherapyConfig::Instance().GetBoronMode();
  const G4bool inTumorCell = TouchableContains(touchable, "TumorCell");
  const G4bool inBoronRegion =
    inTumorCell &&
    ((boronMode == BoronMode::Uniform) ||
     (boronMode == BoronMode::Cytoplasm && currentVolumeName.find("TumorCell") != G4String::npos) ||
     (boronMode == BoronMode::Shell && currentVolumeName.find("TumorCell") != G4String::npos));

  auto track = step->GetTrack();
  const auto particleName = track->GetParticleDefinition()->GetParticleName();
  if (inTumorRegion && track->GetParentID() == 0 && particleName == "neutron") {
    TherapyAnalysisManager::Instance().MarkPrimaryNeutronReachedTumor();
  }
  G4String processName = "init";
  if (prePoint->GetProcessDefinedStep()) {
    processName = prePoint->GetProcessDefinedStep()->GetProcessName();
  }
  G4String volumeName = currentVolumeName;
  const auto currentEvent = G4RunManager::GetRunManager()->GetCurrentEvent();
  const G4int eventID = currentEvent ? currentEvent->GetEventID() : -1;

  G4ThreeVector cellLocalStart(0., 0., 0.);
  G4ThreeVector cellLocalEnd(0., 0., 0.);
  G4bool hasCellLocal = false;
  if (cellID > 0) {
    // All cell placements use rotation = nullptr; cell-local position is just
    // global - cell_center. We retrieve the center from CellInfo (kept in the
    // analysis manager's cell map).
    const G4ThreeVector cellCenter = TherapyAnalysisManager::Instance().GetCellCenter(cellID);
    cellLocalStart = prePoint->GetPosition() - cellCenter;
    cellLocalEnd = postPoint->GetPosition() - cellCenter;
    hasCellLocal = true;
  }

  TherapyAnalysisManager::Instance().AddEnergyDeposit(edep,
                                                      step->GetStepLength(),
                                                      scoringPosition,
                                                      cellLocalStart,
                                                      cellLocalEnd,
                                                      hasCellLocal,
                                                      cellID,
                                                      inTumorRegion,
                                                      inNormalRegion,
                                                      inPhantom,
                                                      inNucleus,
                                                      inBoronRegion,
                                                      particleName,
                                                      processName,
                                                      volumeName,
                                                      eventID,
                                                      track->GetTrackID(),
                                                      track->GetWeight());

}
