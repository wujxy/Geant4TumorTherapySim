#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
PLOT_PYTHON="${PLOT_PYTHON:-/home/yoru/miniconda3/envs/iris/bin/python}"
Q2_JOBS="${Q2_JOBS:-4}"
B10_SCAN_EVENTS="${B10_SCAN_EVENTS:-200000}"
THERAPY_COMPARISON_EVENTS="${THERAPY_COMPARISON_EVENTS:-20000}"

cd "$PROJECT_DIR"

if [[ -f "$GEANT4_ENV" ]]; then
  source "$GEANT4_ENV"
fi

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig-g4sim}"
mkdir -p build figures results/logs results/generated_macros

cmake -S . -B build
cmake --build build -j2

write_q2_macro() {
  local macro="$1"
  local output="$2"
  local boron_mode="$3"
  local boron_ppm="$4"
  local particle="$5"
  local energy="$6"
  local events="$7"

  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/boronMode ${boron_mode}
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
/therapy/boronPPM ${boron_ppm}
/therapy/killDoseThreshold 2 Gy

/run/initialize
/gun/particle ${particle}
/gun/energy ${energy}
/run/beamOn ${events}
EOF
}

tasks=(
  "macros/problem2_bnct_uniform.mac"
  "macros/problem2_bnct_shell.mac"
  "macros/problem2_gamma.mac"
  "macros/problem2_proton.mac"
)

b10_scan_ppm=(1000 3000 10000 30000 100000 300000 500000)
b10_modes=(uniform shell)
fluence_events=(2000 5000 10000 20000 50000 100000 200000)

for mode in "${b10_modes[@]}"; do
  for ppm in "${b10_scan_ppm[@]}"; do
    macro="results/generated_macros/problem2_bnct_${mode}_${ppm}ppm.mac"
    write_q2_macro "$macro" "output_problem2_bnct_${mode}_${ppm}ppm.root" \
      "$mode" "$ppm" neutron "0.5 eV" "$B10_SCAN_EVENTS"
    tasks+=("$macro")
  done

  for events in "${fluence_events[@]}"; do
    macro="results/generated_macros/problem2_bnct_${mode}_fluence_${events}events.mac"
    write_q2_macro "$macro" "output_problem2_bnct_${mode}_fluence_${events}events.root" \
      "$mode" 500000 neutron "0.5 eV" "$events"
    tasks+=("$macro")
  done
done

write_q2_macro "results/generated_macros/problem2_gamma.mac" "output_problem2_gamma.root" \
  none 0 gamma "1 MeV" "$THERAPY_COMPARISON_EVENTS"
write_q2_macro "results/generated_macros/problem2_proton.mac" "output_problem2_proton.root" \
  none 0 proton "80 MeV" "$THERAPY_COMPARISON_EVENTS"

printf '%s\0' "${tasks[@]}" | xargs -0 -n1 -P "$Q2_JOBS" bash -c '
  macro="$1"
  name="$(basename "$macro" .mac)"
  echo "Running $macro"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
' _

if [[ -d "$ROOT_DIR" ]]; then
  export ROOTSYS="$ROOT_DIR"
  export PATH="$ROOTSYS/bin:$PATH"
  export PYTHONPATH="$ROOTSYS/lib:${PYTHONPATH:-}"
  export LD_LIBRARY_PATH="$ROOTSYS/lib:${LD_LIBRARY_PATH:-}"
fi

"$PLOT_PYTHON" scripts/plot_assignment_results.py --section q2

echo "Generated Q2 figures:"
find figures -maxdepth 1 -type f -name 'Q2_*.png' -print | sort
