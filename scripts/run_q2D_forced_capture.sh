#!/usr/bin/env bash
# Q2 two-stage BNCT: conditional microdosimetry for one B10 capture per event.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
JOBS="${JOBS:-6}"
CAPTURE_EVENTS="${CAPTURE_EVENTS:-100000}"
SEEDS=(11111111 22222223 33333335)
SEEDS2=(98765431 87654319 76543207)

if [[ -f "$GEANT4_ENV" ]]; then source "$GEANT4_ENV"; fi
if [[ -f "$ROOT_DIR/bin/thisroot.sh" ]]; then source "$ROOT_DIR/bin/thisroot.sh"; fi

mkdir -p build results/logs results/generated_macros
cmake -S . -B build >/dev/null
cmake --build build -j"$JOBS"

write_macro() {
  local macro="$1" output="$2" mode="$3" ppm="$4" events="$5" seed1="$6" seed2="$7"
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/boronMode ${mode}
/therapy/sourceMode b10Capture
/therapy/outputFile ${output}
/therapy/saveStepTree false
/therapy/tumorPosition 0 -80 0 mm
/therapy/normalPosition 0 80 0 mm
/therapy/cellPatchSize 200 200 200 um
/therapy/cellPitch 12 um
/therapy/cellDiameter 10 um
/therapy/nucleusRadius 2.5 um
/therapy/boronPPM ${ppm}

/random/setSeeds ${seed1} ${seed2}
/run/initialize
/run/beamOn ${events}
EOF
}

tasks=()
for idx in 0 1 2; do
  s="$((idx + 1))"
  for mode in uniform cytoplasm shell; do
    ppm=300000
    if [[ "$mode" == cytoplasm ]]; then ppm=342857; fi
    if [[ "$mode" == shell ]]; then ppm=614754; fi
    macro="results/generated_macros/q2D_capture_${mode}_seed${s}.mac"
    output="output_q2D_capture_${mode}_seed${s}.root"
    write_macro "$macro" "$output" "$mode" "$ppm" "$CAPTURE_EVENTS" \
      "${SEEDS[$idx]}" "${SEEDS2[$idx]}"
    tasks+=("$macro")
  done
done

printf '%s\0' "${tasks[@]}" | xargs -0 -n1 -P "$JOBS" bash -c '
  macro="$1"; name="$(basename "$macro" .mac)"
  echo "  -> $name"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
' _

echo "[experiment D] conditional B10 capture runs complete."
