# Geant4 Tumor Therapy Simulation

This project implements a first-version Geant4 detector simulation for two related tumor radiotherapy tasks.

## Tasks

1. **External beam comparison**: compare gamma and proton radiotherapy for spherical tumor/normal cells with a diameter of `10 um`. Tumor and normal cell materials are both water in this first version. The main outputs are dose spectra, LET spectra, depth-dose curves, and tumor-to-normal scoring ratios.
2. **BNCT cell-structure comparison**: model a detailed cell with nucleus and optional `10B` distribution. Two boron cases are supported: uniform distribution in tumor cells and concentration in the outer `1 um` shell.

The full tumor region is a macroscopic water box of `2 cm x 1 cm x 3 cm`. Directly instantiating every `10 um` cell in that volume would require billions of cells, so the program uses representative tumor and normal cell patches for cell-level spectra while preserving the full macroscopic scoring region.

## Build

```bash
source setup.sh
cmake -S . -B build
cmake --build build -j
```

## Run

```bash
./build/tumor_therapy macros/problem1_gamma.mac
./build/tumor_therapy macros/problem1_proton.mac
./build/tumor_therapy macros/problem2_bnct_uniform.mac
./build/tumor_therapy macros/problem2_bnct_shell.mac
```

Each run writes a ROOT file such as `output_problem1_gamma.root`.

Interactive proton-beam visualization:

```bash
./build/tumor_therapy --interactive macros/vis_proton.mac
```

The interactive form keeps the Geant4 UI session alive after the macro runs, so the OpenGL window remains available for rotation, zooming, and trajectory inspection.

## Main Outputs

The ROOT files contain:

- `RunTree`: run configuration.
- `EventTree`: event-level energy deposition, region doses, and secondary counts.
- `CellTree`: accumulated cell-level dose, nucleus dose, boron-region dose, and hit counts.
- Optional `StepTree`: detailed step information when `/therapy/saveStepTree true`.
- Histograms for tumor/normal dose, cell dose, nucleus dose, LET, depth-dose, secondary particle yield, and 3D voxel energy deposition.

## Important Metrics

- `D_tumor / D_normal`
- `D_tumor_cells / D_normal_cells`
- LET spectrum in tumor and normal cells
- Proton `PeakToEntranceDoseRatio`
- BNCT alpha and Li7 yields
- Tumor kill fraction over normal damage fraction, using a configurable first-version dose threshold
