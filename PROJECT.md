# PROJECT.md

## Project Goal

Build a first-version Geant4 simulation for tumor radiotherapy comparison. The program supports two assignment problems through one executable and multiple macro files.

## Problem 1

Compare gamma and proton radiotherapy for tumor and normal spherical cells:

- cell diameter: `10 um`;
- tumor region: `2 cm x 1 cm x 3 cm`;
- tumor and normal materials: water;
- comparison quantities: dose spectrum, LET spectrum, depth-dose curve, tumor-to-normal dose ratio;
- proton-specific quantity: Bragg peak placement and peak-to-entrance dose ratio.

Because a full tumor volume filled with `10 um` cells would require billions of placements, the macroscopic tumor is modeled as a water box and cell-level scoring is performed in representative tumor and normal patches.

## Problem 2

Compare BNCT boron-distribution strategies:

- thermal neutron energy: `0.5 eV`;
- cell radius: `5 um`;
- nucleus radius: `2.5 um`;
- boron modes:
  - uniform `10B` in tumor cell material;
  - `10B` concentrated in the outer `1 um` shell;
- normal cells contain no boron in the default setup.

Main comparison quantities are alpha/Li7 yield, tumor/normal nucleus dose, boron-region dose, and LET spectra.

## Implementation Strategy

The project uses a single main branch and one executable:

```text
build/tumor_therapy
```

Different tasks are selected by macro commands:

```text
/therapy/mode problem1
/therapy/mode problem2
/therapy/boronMode none
/therapy/boronMode uniform
/therapy/boronMode shell
```

This avoids duplicate code across branches and keeps geometry, physics, particle source, and analysis output consistent.

## Current Version

This is a first working version focused on:

- modular Geant4 project structure;
- simplified human phantom;
- tumor and normal scoring regions;
- representative `10 um` cell patches;
- gamma, proton, and thermal-neutron source macros;
- interactive OpenGL proton-beam visualization macro;
- ROOT output for event-level and cell-level analysis.

Future improvements can add automated parameter scans, more realistic tissue materials, multiple tumor-depth patches, and biological survival models.
