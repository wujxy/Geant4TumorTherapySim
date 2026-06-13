#include "B10CaptureBiasOperator.hh"

#include "G4BOptnChangeCrossSection.hh"
#include "G4BiasingProcessInterface.hh"
#include "G4BiasingProcessSharedData.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleTable.hh"
#include "G4ProcessManager.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"
#include "G4ios.hh"

#include <cfloat>

B10CaptureBiasOperator::B10CaptureBiasOperator(G4double biasFactor)
  : G4VBiasingOperator("B10CaptureBias"), fBiasFactor(biasFactor)
{
  fNeutron = G4ParticleTable::GetParticleTable()->FindParticle("neutron");
}

B10CaptureBiasOperator::~B10CaptureBiasOperator()
{
  for (auto& [process, operation] : fOperations) {
    (void)process;
    delete operation;
  }
}

void B10CaptureBiasOperator::StartRun()
{
  if (!fSetup || !fNeutron) return;
  const auto sharedData =
    G4BiasingProcessInterface::GetSharedData(fNeutron->GetProcessManager());
  if (sharedData) {
    for (const auto wrapper : sharedData->GetPhysicsBiasingProcessInterfaces()) {
      const auto processName = wrapper->GetWrappedProcess()->GetProcessName();
      fOperations[wrapper] = new G4BOptnChangeCrossSection("B10CaptureBias-" + processName);
      G4cout << "[B10 capture bias] wrapped process=" << processName << G4endl;
    }
  }
  fSetup = false;
}

G4VBiasingOperation* B10CaptureBiasOperator::ProposeOccurenceBiasingOperation(
  const G4Track* track,
  const G4BiasingProcessInterface* callingProcess)
{
  if (track->GetDefinition() != fNeutron) return nullptr;
  const auto found = fOperations.find(callingProcess);
  if (found == fOperations.end()) return nullptr;

  const G4double analogInteractionLength =
    callingProcess->GetWrappedProcess()->GetCurrentInteractionLength();
  if (analogInteractionLength > DBL_MAX / 10.) return nullptr;
  const G4double analogXS = 1. / analogInteractionLength;
  auto operation = found->second;
  const auto previous = callingProcess->GetPreviousOccurenceBiasingOperation();

  if (!previous || operation->GetInteractionOccured()) {
    operation->SetBiasedCrossSection(fBiasFactor * analogXS);
    operation->Sample();
  } else {
    if (previous != operation) return nullptr;
    operation->UpdateForStep(callingProcess->GetPreviousStepSize());
    operation->SetBiasedCrossSection(fBiasFactor * analogXS);
    operation->UpdateForStep(0.0);
  }
  return operation;
}

void B10CaptureBiasOperator::OperationApplied(
  const G4BiasingProcessInterface* callingProcess,
  G4BiasingAppliedCase,
  G4VBiasingOperation* occurenceOperationApplied,
  G4double,
  G4VBiasingOperation*,
  const G4VParticleChange*)
{
  const auto found = fOperations.find(callingProcess);
  if (found != fOperations.end() && found->second == occurenceOperationApplied) {
    found->second->SetInteractionOccured();
  }
}
