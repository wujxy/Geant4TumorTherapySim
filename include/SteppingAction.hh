#ifndef STEPPING_ACTION_HH
#define STEPPING_ACTION_HH

#include "G4UserSteppingAction.hh"
#include "G4VTouchable.hh"
#include "globals.hh"

class G4Step;

class SteppingAction : public G4UserSteppingAction {
public:
  SteppingAction() = default;
  ~SteppingAction() override = default;

  void UserSteppingAction(const G4Step* step) override;

private:
  G4bool TouchableContains(const G4VTouchable* touchable, const G4String& token) const;
  G4int ExtractCellID(const G4VTouchable* touchable) const;
  G4int FindCellDepth(const G4VTouchable* touchable) const;
};

#endif
