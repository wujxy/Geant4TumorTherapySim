#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
PLOT_PYTHON="${PLOT_PYTHON:-/home/yoru/miniconda3/envs/iris/bin/python}"
Q1_SCAN_EVENTS="${Q1_SCAN_EVENTS:-5000}"

cd "$PROJECT_DIR"

if [[ -f "$GEANT4_ENV" ]]; then
  source "$GEANT4_ENV"
fi

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig-g4sim}"
mkdir -p build figures results/logs results/generated_macros

cmake -S . -B build
cmake --build build -j2

run_macro() {
  local macro="$1"
  local name
  name="$(basename "$macro" .mac)"
  echo "Running $macro"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
}

run_scan() {
  local particle="$1"
  local energy="$2"
  local tag="$3"
  local macro="results/generated_macros/problem1_${particle}_${tag}.mac"
  local output="output_problem1_${particle}_${tag}.root"

  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem1
/therapy/boronMode none
/therapy/outputFile ${output}
/therapy/saveStepTree false
/therapy/tumorPosition 0 -80 0 mm
/therapy/normalPosition 0 80 0 mm
/therapy/sourcePosition 0 -600 0 mm
/therapy/sourceDirection 0 1 0
/therapy/beamRadius 8 mm
/therapy/cellPatchSize 200 200 200 um
/therapy/cellPitch 12 um
/therapy/cellDiameter 10 um
/therapy/killDoseThreshold 2 Gy

/run/initialize
/gun/particle ${particle}
/gun/energy ${energy} MeV
/run/beamOn ${Q1_SCAN_EVENTS}
EOF

  run_macro "$macro"
}

run_macro "macros/problem1_gamma.mac"
run_macro "macros/problem1_proton.mac"

gamma_scan_energies=(0.2 0.5 1 2 4 6 8 10 15)
proton_scan_energies=(60 65 70 75 80 85 90 95 100)

for energy in "${gamma_scan_energies[@]}"; do
  run_scan gamma "$energy" "${energy//./p}MeV"
done

for energy in "${proton_scan_energies[@]}"; do
  run_scan proton "$energy" "${energy}MeV"
done

if [[ -d "$ROOT_DIR" ]]; then
  export ROOTSYS="$ROOT_DIR"
  export PATH="$ROOTSYS/bin:$PATH"
  export PYTHONPATH="$ROOTSYS/lib:${PYTHONPATH:-}"
  export LD_LIBRARY_PATH="$ROOTSYS/lib:${LD_LIBRARY_PATH:-}"
fi

"$PLOT_PYTHON" scripts/plot_assignment_results.py --section q1

echo "Generated Q1 figures:"
find figures -maxdepth 1 -type f -name 'Q1_*.png' -print | sort
