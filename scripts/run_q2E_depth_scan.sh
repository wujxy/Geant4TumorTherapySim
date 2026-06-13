#!/usr/bin/env bash
# Q2 replacement experiment E: effect of tumor depth on analog neutron delivery.
# Only tumor depth changes; source and incident histories remain fixed.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
JOBS="${JOBS:-12}"
EVENTS="${EVENTS:-200000}"
B10_CAPTURE_BIAS="${B10_CAPTURE_BIAS:-1}"
UNIFORM_PPM="${UNIFORM_PPM:-300000}"
DEPTH_Y_MM=(-110 -95 -80 -65 -50)
SEED1=24681357
SEED2=97531864

if [[ -f "$GEANT4_ENV" ]]; then source "$GEANT4_ENV"; fi
if [[ -d "$ROOT_DIR" ]]; then
  export ROOTSYS="$ROOT_DIR"
  export PATH="$ROOTSYS/bin:$PATH"
  export LD_LIBRARY_PATH="$ROOTSYS/lib:${LD_LIBRARY_PATH:-}"
fi

mkdir -p build figures_final results/logs results/generated_macros
cmake -S . -B build >/dev/null
cmake --build build -j"$JOBS"

tasks=()
for tumor_y in "${DEPTH_Y_MM[@]}"; do
  tag="${tumor_y/-/m}"
  macro="results/generated_macros/q2E_depth_y${tag}_analog.mac"
  output="output_q2E_depth_y${tag}_analog.root"
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/sourceMode beam
/therapy/b10CaptureBias ${B10_CAPTURE_BIAS}
/therapy/boronMode uniform
/therapy/boronPPM ${UNIFORM_PPM}
/therapy/outputFile ${output}
/therapy/saveStepTree false
/therapy/tumorPosition 0 ${tumor_y} 0 mm
/therapy/normalPosition 0 80 0 mm
/therapy/sourcePosition 0 -600 0 mm
/therapy/sourceDirection 0 1 0
/therapy/beamRadius 150 um
/therapy/cellPatchSize 200 200 200 um
/therapy/cellPitch 12 um
/therapy/cellDiameter 10 um
/therapy/nucleusRadius 2.5 um
/therapy/killDoseThreshold 2 Gy

/random/setSeeds ${SEED1} ${SEED2}
/run/initialize
/gun/particle neutron
/gun/energy 0.5 eV
/run/beamOn ${EVENTS}
EOF
  tasks+=("$macro")
done

echo "[experiment E-depth] running ${#tasks[@]} jobs with ${JOBS}-way parallelism..."
printf '%s\0' "${tasks[@]}" | xargs -0 -n1 -P "$JOBS" bash -c '
  macro="$1"
  name="$(basename "$macro" .mac)"
  echo "  -> $name"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
' _

echo "[experiment E-depth] done. ROOT outputs: output_q2E_depth_y*_analog.root"
