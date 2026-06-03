#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"
#include "TherapyConfig.hh"

#include "G4PhysListFactory.hh"
#include "G4RunManagerFactory.hh"
#include "G4UIExecutive.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"

#include <string>

int main(int argc, char** argv)
{
  // Construct the singleton before macro parsing so /therapy commands exist.
  (void)TherapyConfig::Instance();

  auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);
  auto* detector = new DetectorConstruction;
  runManager->SetUserInitialization(detector);

  G4PhysListFactory factory;
  auto* physicsList = factory.GetReferencePhysList("QGSP_BIC_HP");
  runManager->SetUserInitialization(physicsList);
  runManager->SetUserInitialization(new ActionInitialization(detector));

  auto* visManager = new G4VisExecutive;
  visManager->Initialize();

  auto* uiManager = G4UImanager::GetUIpointer();
  if (argc > 1 && std::string(argv[1]) == "--interactive") {
    auto* ui = new G4UIExecutive(argc, argv);
    const G4String macro = argc > 2 ? argv[2] : "macros/vis.mac";
    uiManager->ApplyCommand("/control/execute " + macro);
    ui->SessionStart();
    delete ui;
  } else if (argc > 1) {
    const G4String command = "/control/execute ";
    uiManager->ApplyCommand(command + argv[1]);
  } else {
    auto* ui = new G4UIExecutive(argc, argv);
    uiManager->ApplyCommand("/control/execute macros/vis.mac");
    ui->SessionStart();
    delete ui;
  }

  delete visManager;
  delete runManager;
  return 0;
}
