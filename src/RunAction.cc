#include "RunAction.hh"

#include "DetectorConstruction.hh"
#include "TherapyAnalysisManager.hh"

#include "G4Run.hh"

RunAction::RunAction(const DetectorConstruction* detector)
  : fDetector(detector)
{
}

void RunAction::BeginOfRunAction(const G4Run* run)
{
  TherapyAnalysisManager::Instance().BeginRun(run->GetNumberOfEventToBeProcessed(), fDetector->GetCells());
}

void RunAction::EndOfRunAction(const G4Run*)
{
  TherapyAnalysisManager::Instance().EndRun();
}
