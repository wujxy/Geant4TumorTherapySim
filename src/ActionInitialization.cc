#include "ActionInitialization.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "SteppingAction.hh"
#include "TrackingAction.hh"

ActionInitialization::ActionInitialization(const DetectorConstruction* detector)
  : fDetector(detector)
{
}

void ActionInitialization::Build() const
{
  SetUserAction(new PrimaryGeneratorAction(fDetector));
  SetUserAction(new RunAction(fDetector));
  SetUserAction(new EventAction);
  SetUserAction(new SteppingAction);
  SetUserAction(new TrackingAction);
}
