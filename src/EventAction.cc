#include "EventAction.hh"

#include "TherapyAnalysisManager.hh"

#include "G4Event.hh"

void EventAction::BeginOfEventAction(const G4Event*)
{
  TherapyAnalysisManager::Instance().BeginEvent();
}

void EventAction::EndOfEventAction(const G4Event* event)
{
  TherapyAnalysisManager::Instance().EndEvent(event->GetEventID());
}
