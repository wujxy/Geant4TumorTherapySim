#include "TrackingAction.hh"

#include "TherapyAnalysisManager.hh"

#include "G4ParticleDefinition.hh"
#include "G4Track.hh"

void TrackingAction::PreUserTrackingAction(const G4Track* track)
{
  if (track->GetParentID() <= 0) return;
  TherapyAnalysisManager::Instance().AddSecondary(
    track->GetParticleDefinition()->GetParticleName(),
    track->GetWeight());
}
