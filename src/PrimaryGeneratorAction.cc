#include "PrimaryGeneratorAction.hh"

#include "TherapyConfig.hh"

#include "G4Event.hh"
#include "G4Gamma.hh"
#include "G4ParticleGun.hh"
#include "G4Proton.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction()
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
