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

declare -A particles=(["gamma"]="gamma" ["proton"]="proton")
declare -A energies=(["gamma"]="1 MeV" ["proton"]="45 MeV")
THERAPY_COMPARISON_EVENTS="${THERAPY_COMPARISON_EVENTS:-20000}"

for case_name in gamma proton; do
  macro="results/generated_macros/problem2_${case_name}.mac"
  output="output_problem2_${case_name}.root"
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/boronMode none
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
/therapy/killDoseThreshold 2 Gy

/run/initialize
/gun/particle ${particles[$case_name]}
/gun/energy ${energies[$case_name]}
/run/beamOn ${THERAPY_COMPARISON_EVENTS}
EOF
  echo "Running Q2 therapy comparison ${case_name}"
  ./build/tumor_therapy "$macro" > "results/logs/problem2_${case_name}.log" 2>&1
done

/usr/bin/python3 scripts/plot_assignment_results.py

echo "Generated figures/Q2_therapy_comparison_projected_maps.png"
