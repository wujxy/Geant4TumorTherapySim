#include "PrimaryGeneratorAction.hh"

#include "DetectorConstruction.hh"
#include "TherapyAnalysisManager.hh"
#include "TherapyConfig.hh"

#include "G4Alpha.hh"
#include "G4Event.hh"
#include "G4Exception.hh"
#include "G4Gamma.hh"
#include "G4IonTable.hh"
#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

#include <algorithm>
#include <cmath>
#include <vector>

namespace {
G4ThreeVector IsotropicDirection()
{
  const G4double cosTheta = 2. * G4UniformRand() - 1.;
  const G4double sinTheta = std::sqrt(std::max(0., 1. - cosTheta * cosTheta));
  const G4double phi = CLHEP::twopi * G4UniformRand();
  return G4ThreeVector(sinTheta * std::cos(phi), sinTheta * std::sin(phi), cosTheta);
}
}

PrimaryGeneratorAction::PrimaryGeneratorAction(const DetectorConstruction* detector)
  : fDetector(detector)
{
  fParticleGun = new G4ParticleGun(1);
  fParticleGun->SetParticleDefinition(G4Gamma::Definition());
  fParticleGun->SetParticleEnergy(1. * MeV);
  fParticleGun->SetParticlePosition(TherapyConfig::Instance().GetSourcePosition());
  fParticleGun->SetParticleMomentumDirection(TherapyConfig::Instance().GetSourceDirection());
}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fParticleGun;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event)
{
  if (TherapyConfig::Instance().GetSourceMode() == SourceMode::B10Capture) {
    GenerateB10Capture(event);
    return;
  }
  GenerateBeam(event);
}

void PrimaryGeneratorAction::GenerateBeam(G4Event* event)
{
  const auto& config = TherapyConfig::Instance();
  const G4ThreeVector direction = config.GetSourceDirection().unit();
  G4ThreeVector u = direction.cross(G4ThreeVector(0., 0., 1.));
  if (u.mag2() < 1.e-12) {
    u = direction.cross(G4ThreeVector(1., 0., 0.));
  }
  u = u.unit();
  const G4ThreeVector v = direction.cross(u).unit();

  const G4double r = config.GetBeamRadius() * std::sqrt(G4UniformRand());
  const G4double phi = CLHEP::twopi * G4UniformRand();
  const G4ThreeVector offset = r * std::cos(phi) * u + r * std::sin(phi) * v;

  fParticleGun->SetParticlePosition(config.GetSourcePosition() + offset);
  fParticleGun->SetParticleMomentumDirection(direction);
  fParticleGun->GeneratePrimaryVertex(event);
}

void PrimaryGeneratorAction::GenerateB10Capture(G4Event* event)
{
  const auto& config = TherapyConfig::Instance();
  if (config.GetMode() != TherapyMode::Problem2 ||
      (config.GetBoronMode() != BoronMode::Uniform &&
       config.GetBoronMode() != BoronMode::Cytoplasm &&
       config.GetBoronMode() != BoronMode::Shell)) {
    G4Exception("PrimaryGeneratorAction::GenerateB10Capture",
                "InvalidB10CaptureConfiguration",
                FatalException,
                "b10Capture requires /therapy/mode problem2 and boronMode uniform, cytoplasm, or shell.");
    return;
  }

  std::vector<const CellInfo*> tumorCells;
  for (const auto& cell : fDetector->GetCells()) {
    if (cell.type == CellType::Tumor) tumorCells.push_back(&cell);
  }
  if (tumorCells.empty()) {
    G4Exception("PrimaryGeneratorAction::GenerateB10Capture",
                "NoTumorCells",
                FatalException,
                "b10Capture requires at least one tumor cell.");
    return;
  }

  const auto index = std::min(static_cast<std::size_t>(G4UniformRand() * tumorCells.size()),
                              tumorCells.size() - 1);
  const CellInfo& cell = *tumorCells[index];
  const G4double outerRadius = config.GetCellRadius();
  G4double innerRadius = 0.;
  if (config.GetBoronMode() == BoronMode::Cytoplasm) {
    innerRadius = config.GetNucleusRadius();
  } else if (config.GetBoronMode() == BoronMode::Shell) {
    innerRadius = std::max(0., outerRadius - config.GetShellThickness());
  }
  const G4double radius = std::cbrt(std::pow(innerRadius, 3) +
                                   G4UniformRand() *
                                     (std::pow(outerRadius, 3) - std::pow(innerRadius, 3)));
  const G4ThreeVector position = cell.position + radius * IsotropicDirection();
  const G4ThreeVector axis = IsotropicDirection();
  const G4bool excitedBranch = G4UniformRand() < 0.94;
  const G4double alphaEnergy = excitedBranch ? 1.47 * MeV : 1.78 * MeV;
  const G4double liEnergy = excitedBranch ? 0.84 * MeV : 1.01 * MeV;

  TherapyAnalysisManager::Instance().RecordForcedCapture(excitedBranch ? 1 : 0,
                                                         radius,
                                                         alphaEnergy + liEnergy);

  fParticleGun->SetParticlePosition(position);
  fParticleGun->SetParticleDefinition(G4Alpha::Definition());
  fParticleGun->SetParticleEnergy(alphaEnergy);
  fParticleGun->SetParticleMomentumDirection(axis);
  fParticleGun->GeneratePrimaryVertex(event);

  fParticleGun->SetParticleDefinition(G4IonTable::GetIonTable()->GetIon(3, 7, 0.));
  fParticleGun->SetParticleEnergy(liEnergy);
  fParticleGun->SetParticleMomentumDirection(-axis);
  fParticleGun->GeneratePrimaryVertex(event);

  if (excitedBranch) {
    fParticleGun->SetParticleDefinition(G4Gamma::Definition());
    fParticleGun->SetParticleEnergy(0.478 * MeV);
    fParticleGun->SetParticleMomentumDirection(IsotropicDirection());
    fParticleGun->GeneratePrimaryVertex(event);
  }
}
