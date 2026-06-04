#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SCRIPT="/home/NagaiYoru/packages/setup-geant4-root.sh"

cd "$PROJECT_DIR"

if [[ ! -f "$ENV_SCRIPT" ]]; then
  echo "Missing Geant4/ROOT environment script: $ENV_SCRIPT" >&2
  exit 1
fi

source "$ENV_SCRIPT"
ROOT_DIR="/home/NagaiYoru/packages/root"
if [[ -d "$ROOT_DIR" ]]; then
  export ROOTSYS="$ROOT_DIR"
  export PATH="$ROOTSYS/bin:$PATH"
  export PYTHONPATH="$ROOTSYS/lib:${PYTHONPATH:-}"
  export LD_LIBRARY_PATH="$ROOTSYS/lib:${LD_LIBRARY_PATH:-}"
fi
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig-g4sim}"

mkdir -p build figures results/logs results/generated_macros

cmake -S . -B build
cmake --build build -j2

declare -a macros=(
  "macros/problem1_gamma.mac"
  "macros/problem1_proton.mac"
  "macros/problem2_bnct_uniform.mac"
  "macros/problem2_bnct_shell.mac"
)

for macro in "${macros[@]}"; do
  name="$(basename "$macro" .mac)"
  echo "Running $macro"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
done

declare -a gamma_scan_energies=(0.2 0.5 1 2 4 6 8 10 15)
declare -a scan_energies=(30 35 40 45 50 55 60 70 80)
declare -a b10_scan_ppm=(1000 3000 10000 30000 100000 300000 500000)
declare -a b10_modes=(uniform shell)
B10_SCAN_EVENTS="${B10_SCAN_EVENTS:-20000}"

for energy in "${gamma_scan_energies[@]}"; do
  tag="${energy//./p}MeV"
  macro="results/generated_macros/problem1_gamma_${tag}.mac"
  output="output_problem1_gamma_${tag}.root"
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem1
/therapy/boronMode none
/therapy/outputFile ${output}
/therapy/saveStepTree false
/therapy/tumorPosition -45 -45 30 mm
/therapy/normalPosition -45 -15 30 mm
/therapy/sourcePosition -45 -600 30 mm
/therapy/sourceDirection 0 1 0
/therapy/beamRadius 8 mm
/therapy/cellPatchSize 200 200 200 um
/therapy/cellPitch 12 um
/therapy/cellDiameter 10 um
/therapy/killDoseThreshold 2 Gy

/run/initialize
/gun/particle gamma
/gun/energy ${energy} MeV
/run/beamOn 1000
EOF
  echo "Running gamma scan ${energy} MeV"
  ./build/tumor_therapy "$macro" > "results/logs/problem1_gamma_${tag}.log" 2>&1
done

for energy in "${scan_energies[@]}"; do
  macro="results/generated_macros/problem1_proton_${energy}MeV.mac"
  output="output_problem1_proton_${energy}MeV.root"
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem1
/therapy/boronMode none
/therapy/outputFile ${output}
/therapy/saveStepTree false
/therapy/tumorPosition -45 -45 30 mm
/therapy/normalPosition -45 -15 30 mm
/therapy/sourcePosition -45 -600 30 mm
/therapy/sourceDirection 0 1 0
/therapy/beamRadius 8 mm
/therapy/cellPatchSize 200 200 200 um
/therapy/cellPitch 12 um
/therapy/cellDiameter 10 um
/therapy/killDoseThreshold 2 Gy

/run/initialize
/gun/particle proton
/gun/energy ${energy} MeV
/run/beamOn 500
EOF
  echo "Running proton scan ${energy} MeV"
  ./build/tumor_therapy "$macro" > "results/logs/problem1_proton_${energy}MeV.log" 2>&1
done

for mode in "${b10_modes[@]}"; do
  for ppm in "${b10_scan_ppm[@]}"; do
    macro="results/generated_macros/problem2_bnct_${mode}_${ppm}ppm.mac"
    output="output_problem2_bnct_${mode}_${ppm}ppm.root"
    cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/boronMode ${mode}
/therapy/outputFile ${output}
/therapy/saveStepTree false
/therapy/tumorPosition -45 -45 30 mm
/therapy/normalPosition -45 -15 30 mm
/therapy/sourcePosition -45 -600 30 mm
/therapy/sourceDirection 0 1 0
/therapy/beamRadius 150 um
/therapy/cellPatchSize 200 200 200 um
/therapy/cellPitch 12 um
/therapy/cellDiameter 10 um
/therapy/nucleusRadius 2.5 um
/therapy/boronPPM ${ppm}
/therapy/killDoseThreshold 2 Gy

/run/initialize
/gun/particle neutron
/gun/energy 0.5 eV
/run/beamOn ${B10_SCAN_EVENTS}
EOF
    echo "Running B10 scan ${mode} ${ppm} ppm"
    ./build/tumor_therapy "$macro" > "results/logs/problem2_bnct_${mode}_${ppm}ppm.log" 2>&1
  done
done

/usr/bin/python3 scripts/plot_assignment_results.py

echo "Generated figures:"
find figures -maxdepth 1 -type f -name '*.png' -print | sort
