#!/usr/bin/env bash
# Q2 experiment C: equal-total-B10 concentration scan with occurrence bias.
# Statistical weights reconstruct the corresponding unbiased beam result.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
JOBS="${JOBS:-12}"
EVENTS_SCAN="${EVENTS_SCAN:-200000}"
B10_CAPTURE_BIAS="${B10_CAPTURE_BIAS:-1000}"
PPM_LIST=(30000 100000 200000 300000)
SEED1=11111111
SEED2=98765431

if [[ -f "$GEANT4_ENV" ]]; then source "$GEANT4_ENV"; fi
if [[ -d "$ROOT_DIR" ]]; then
  export ROOTSYS="$ROOT_DIR"
  export PATH="$ROOTSYS/bin:$PATH"
  export LD_LIBRARY_PATH="$ROOTSYS/lib:${LD_LIBRARY_PATH:-}"
fi

mkdir -p build figures results/logs results/generated_macros
cmake -S . -B build >/dev/null
cmake --build build -j"$JOBS"

SHELL_FACTOR=$(echo "scale=6; 1/(1 - (4/5)^3)" | bc -l)
echo "[experiment C] shell-actual = uniform_equiv x ${SHELL_FACTOR}"

write_macro() {
  local macro="$1" output="$2" mode="$3" ppm="$4" events="$5" seed1="$6" seed2="$7" bias="$8"
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/sourceMode beam
/therapy/b10CaptureBias ${bias}
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

/random/setSeeds ${seed1} ${seed2}
/run/initialize
/gun/particle neutron
/gun/energy 0.5 eV
/run/beamOn ${events}
EOF
}

tasks=()
for uppm in "${PPM_LIST[@]}"; do
  sppm=$(echo "scale=2; $uppm * $SHELL_FACTOR / 1" | bc -l)
  for mode in uniform shell; do
    ppm="$uppm"
    if [[ "$mode" == shell ]]; then ppm="$sppm"; fi
    m="results/generated_macros/q2C_biased_${mode}_${uppm}ppm.mac"
    o="output_q2C_biased_${mode}_${uppm}ppm.root"
    write_macro "$m" "$o" "$mode" "$ppm" "$EVENTS_SCAN" "$SEED1" "$SEED2" "$B10_CAPTURE_BIAS"
    tasks+=("$m")
  done
done

echo "[experiment C] running ${#tasks[@]} jobs with ${JOBS}-way parallelism..."
printf '%s\0' "${tasks[@]}" | xargs -0 -n1 -P "$JOBS" bash -c '
  macro="$1"
  name="$(basename "$macro" .mac)"
  echo "  -> $name"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
' _

echo "[experiment C] done. ROOT outputs: output_q2C_biased_*.root"
