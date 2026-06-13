#ifndef PRIMARY_GENERATOR_ACTION_HH
#define PRIMARY_GENERATOR_ACTION_HH

#include "G4VUserPrimaryGeneratorAction.hh"

class G4Event;
class G4ParticleGun;
class DetectorConstruction;

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction {
public:
  explicit PrimaryGeneratorAction(const DetectorConstruction* detector);
  ~PrimaryGeneratorAction() override;

  void GeneratePrimaries(G4Event* event) override;

private:
  void GenerateBeam(G4Event* event);
  void GenerateB10Capture(G4Event* event);

  const DetectorConstruction* fDetector;
  G4ParticleGun* fParticleGun;
};

#endif
