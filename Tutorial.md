# Tutorial

## 1. Load the Environment

```bash
cd /home/NagaiYoru/ucas_course/G4sim/Geant4TumorTherapySim
source setup.sh
```

The expected environment contains Geant4 11.4.0 and ROOT 6.36.06.

## 2. Build

```bash
cmake -S . -B build
cmake --build build -j
```

The executable is:

```bash
build/tumor_therapy
```

## 3. Visual Check

```bash
./build/tumor_therapy macros/vis.mac
```

The visualized geometry contains:

- simplified human body;
- red tumor region;
- blue normal control region;
- representative tumor and normal cell patches.

## 4. Problem 1: Gamma vs Proton

Run gamma:

```bash
./build/tumor_therapy macros/problem1_gamma.mac
```

Run proton:

```bash
./build/tumor_therapy macros/problem1_proton.mac
```

Compare:

- tumor region dose vs normal region dose;
- tumor cell dose spectrum vs normal cell dose spectrum;
- LET spectra;
- depth-dose curve.

For proton optimization, copy `macros/problem1_proton_scan_template.mac` and change:

```text
/gun/energy
/therapy/sourcePosition
/therapy/beamRadius
```

The first optimization quantity is:

```text
Score = (D_tumor / D_normal) * PeakToEntranceDoseRatio
```

## 5. Problem 2: BNCT Boron Distribution

Uniform boron case:

```bash
./build/tumor_therapy macros/problem2_bnct_uniform.mac
```

Outer-shell boron case:

```bash
./build/tumor_therapy macros/problem2_bnct_shell.mac
```

Compare:

- tumor cell dose;
- tumor nucleus dose;
- boron-region dose;
- alpha and Li7 yields;
- LET spectra.

## 6. Inspect ROOT Output

Example:

```bash
root -l output_problem1_proton.root
```

Inside ROOT:

```cpp
.ls
EventTree->Print()
CellTree->Print()
hDepthDose->Draw()
hLETTumor->Draw()
```

The most useful trees are `EventTree` for treatment-level comparison and `CellTree` for cell-level dose spectra.
