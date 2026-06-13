#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SCRIPT="/home/NagaiYoru/packages/setup-geant4-root.sh"

cd "$PROJECT_DIR"

if [[ -f "$ENV_SCRIPT" ]]; then
  source "$ENV_SCRIPT" || true
fi

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

declare -a b10_scan_ppm=(1000 3000 10000 30000 100000 300000 500000)
declare -a b10_modes=(uniform shell)
B10_SCAN_EVENTS="${B10_SCAN_EVENTS:-200000}"

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
/therapy/tumorPosition 0 -80 0 mm
/therapy/normalPosition 0 80 0 mm
/therapy/sourcePosition 0 -600 0 mm
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

echo "Generated figures/Q2_b10_concentration_scan.png"
