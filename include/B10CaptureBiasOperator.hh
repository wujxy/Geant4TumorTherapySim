#ifndef B10_CAPTURE_BIAS_OPERATOR_HH
#define B10_CAPTURE_BIAS_OPERATOR_HH

#include "G4VBiasingOperator.hh"

#include <map>

class G4BiasingProcessInterface;
class G4BOptnChangeCrossSection;
class G4ParticleDefinition;

class B10CaptureBiasOperator : public G4VBiasingOperator {
public:
  explicit B10CaptureBiasOperator(G4double biasFactor);
  ~B10CaptureBiasOperator() override;

  void StartRun() override;

private:
  G4VBiasingOperation* ProposeOccurenceBiasingOperation(
    const G4Track* track,
    const G4BiasingProcessInterface* callingProcess) override;
  G4VBiasingOperation* ProposeFinalStateBiasingOperation(
    const G4Track*, const G4BiasingProcessInterface*) override { return nullptr; }
  G4VBiasingOperation* ProposeNonPhysicsBiasingOperation(
    const G4Track*, const G4BiasingProcessInterface*) override { return nullptr; }

  using G4VBiasingOperator::OperationApplied;
  void OperationApplied(const G4BiasingProcessInterface* callingProcess,
                        G4BiasingAppliedCase,
                        G4VBiasingOperation* occurenceOperationApplied,
                        G4double,
                        G4VBiasingOperation*,
                        const G4VParticleChange*) override;

  G4double fBiasFactor;
  G4bool fSetup = true;
  const G4ParticleDefinition* fNeutron = nullptr;
  std::map<const G4BiasingProcessInterface*, G4BOptnChangeCrossSection*> fOperations;
};

#endif
