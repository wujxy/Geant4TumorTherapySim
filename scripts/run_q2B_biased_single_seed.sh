#!/usr/bin/env bash
# Run one statistically weighted, capture-biased real-neutron seed for F4.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
JOBS="${JOBS:-4}"
EVENTS="${EVENTS:-200000}"
events="$EVENTS"
B10_CAPTURE_BIAS="${B10_CAPTURE_BIAS:-100}"
bias="$B10_CAPTURE_BIAS"
UNIFORM_PPM="${UNIFORM_PPM:-300000}"
SEED1="${SEED1:-24681357}"
SEED2="${SEED2:-97531864}"

if [[ -f "$GEANT4_ENV" ]]; then source "$GEANT4_ENV"; fi
mkdir -p build results/generated_macros results/logs
cmake -S . -B build >/dev/null
cmake --build build -j"$JOBS"

SHELL_FACTOR=$(echo "scale=8; 1/(1 - (4/5)^3)" | bc -l)
SHELL_PPM=$(echo "scale=2; $UNIFORM_PPM * $SHELL_FACTOR / 1" | bc -l)

for spec in "uniform|${UNIFORM_PPM}" "shell|${SHELL_PPM}"; do
  IFS='|' read -r mode ppm <<< "$spec"
  output="output_q2B_neutron_${mode}_biased_seed1.root"
  macro="results/generated_macros/q2B_neutron_${mode}_biased_seed1.mac"
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/boronMode ${mode}
/therapy/sourceMode beam
/therapy/b10CaptureBias ${bias}
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

/random/setSeeds ${SEED1} ${SEED2}
/run/initialize
/gun/particle neutron
/gun/energy 0.5 eV
/run/beamOn ${events}
EOF
  echo "[q2B biased] ${mode}: ${EVENTS} histories, bias=${B10_CAPTURE_BIAS}x"
  ./build/tumor_therapy "$macro" > "results/logs/q2B_neutron_${mode}_biased_seed1.log" 2>&1
done

echo "[q2B biased] complete"
