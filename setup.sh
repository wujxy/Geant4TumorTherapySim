#!/usr/bin/env bash

# Usage:
#   source ./setup.sh

source /home/NagaiYoru/packages/setup-geant4-root.sh

export ROOTSYS=/home/NagaiYoru/packages/root
export Geant4_DIR=/home/NagaiYoru/packages/geant4-11.4.0/lib/cmake/Geant4

export PATH="$ROOTSYS/bin:/home/NagaiYoru/packages/geant4-11.4.0/bin:$PATH"
export LD_LIBRARY_PATH="$ROOTSYS/lib:/home/NagaiYoru/packages/geant4-11.4.0/lib:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="$ROOTSYS/lib:${PYTHONPATH:-}"
export CMAKE_PREFIX_PATH="/home/NagaiYoru/packages/geant4-11.4.0:$ROOTSYS:${CMAKE_PREFIX_PATH:-}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig-g4sim}"
