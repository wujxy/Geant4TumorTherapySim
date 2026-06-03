#ifndef RUN_ACTION_HH
#define RUN_ACTION_HH

#include "G4UserRunAction.hh"

class DetectorConstruction;
class G4Run;

class RunAction : public G4UserRunAction {
public:
  explicit RunAction(const DetectorConstruction* detector);
  ~RunAction() override = default;

  void BeginOfRunAction(const G4Run* run) override;
  void EndOfRunAction(const G4Run* run) override;

private:
  const DetectorConstruction* fDetector;
};

#endif
