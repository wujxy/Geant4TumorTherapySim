#!/usr/bin/env bash
# Add independent real-neutron BNCT seeds until both modes reach the Li7 target.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
PYTHON_BIN="${PYTHON_BIN:-/home/yoru/miniconda3/envs/iris/bin/python}"
JOBS="${JOBS:-6}"
EVENTS_PER_SEED="${EVENTS_PER_SEED:-2000000}"
INITIAL_SEEDS="${INITIAL_SEEDS:-10}"
TARGET_CAPTURES="${TARGET_CAPTURES:-100}"
UNIFORM_PPM="${UNIFORM_PPM:-300000}"

if [[ -f "$GEANT4_ENV" ]]; then source "$GEANT4_ENV"; fi
if [[ -d "$ROOT_DIR" ]]; then
  export ROOTSYS="$ROOT_DIR"
  export PATH="$ROOTSYS/bin:$PATH"
  export PYTHONPATH="$ROOTSYS/lib:${PYTHONPATH:-}"
  export LD_LIBRARY_PATH="$ROOTSYS/lib:${LD_LIBRARY_PATH:-}"
fi

mkdir -p build results/logs results/generated_macros
cmake -S . -B build >/dev/null
cmake --build build -j"$JOBS"

SHELL_PPM=$(echo "scale=2; $UNIFORM_PPM / (1 - (4/5)^3)" | bc -l)

write_macro() {
  local macro="$1" output="$2" mode="$3" ppm="$4" events="$5" seed="$6"
  local seed1=$((40000001 + seed * 101))
  local seed2=$((70000003 + seed * 211))
  cat > "$macro" <<EOF
/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0

/therapy/mode problem2
/therapy/boronMode ${mode}
/therapy/sourceMode beam
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

/random/setSeeds ${seed1} ${seed2}
/run/initialize
/gun/particle neutron
/gun/energy 0.5 eV
/run/beamOn ${events}
EOF
}

count_mode_captures() {
  local mode="$1"
  "$PYTHON_BIN" -c "
from pathlib import Path
import ROOT
paths = [Path('output_q2B_neutron_${mode}_final.root'), *sorted(Path('.').glob('output_q2B_neutron_${mode}_seed*.root'))]
print(sum(int(ROOT.RDataFrame('EventTree', str(path)).Sum('nLi7').GetValue()) for path in paths))
" 2>/dev/null
}

next_seed=1
while true; do
  uniform_captures=$(count_mode_captures uniform)
  shell_captures=$(count_mode_captures shell)
  echo "[BNCT stats] uniform=${uniform_captures}, shell=${shell_captures}, target=${TARGET_CAPTURES}"
  if (( uniform_captures >= TARGET_CAPTURES && shell_captures >= TARGET_CAPTURES )); then break; fi

  tasks=()
  batch_end=$((next_seed + INITIAL_SEEDS - 1))
  for seed in $(seq "$next_seed" "$batch_end"); do
    for mode in uniform shell; do
      captures=$uniform_captures
      ppm=$UNIFORM_PPM
      if [[ "$mode" == shell ]]; then captures=$shell_captures; ppm=$SHELL_PPM; fi
      while (( captures < TARGET_CAPTURES )); do
        output="output_q2B_neutron_${mode}_seed${seed}.root"
        if [[ ! -f "$output" ]]; then
          macro="results/generated_macros/q2B_neutron_${mode}_seed${seed}.mac"
          write_macro "$macro" "$output" "$mode" "$ppm" "$EVENTS_PER_SEED" "$seed"
          tasks+=("$macro")
        fi
        break
      done
    done
  done
  if (( ${#tasks[@]} == 0 )); then
    next_seed=$((batch_end + 1))
    continue
  fi
  printf '%s\0' "${tasks[@]}" | xargs -0 -n1 -P "$JOBS" bash -c '
    macro="$1"; name="$(basename "$macro" .mac)"
    echo "  -> $name"
    ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
  ' _
  next_seed=$((batch_end + 1))
done

echo "[BNCT stats] capture target reached."
