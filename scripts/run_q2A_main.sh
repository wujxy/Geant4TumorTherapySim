#!/usr/bin/env bash
# Q2 重设计 — 实验 A：等总 B10 原子数下的 Shell vs Uniform 主图
# 输出：output_q2A_<mode>_<ppm>ppm_seed<i>.root
#   uniform 跑次：实际 ppm = uniform_equiv_ppm
#   shell 跑次：实际 ppm = uniform_equiv_ppm × 2.049 (V_cell / V_shell)
# 同时跑 none 模式作为中子背景控制
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
JOBS="${JOBS:-12}"
EVENTS_MAIN="${EVENTS_MAIN:-1000000}"
UNIFORM_PPM="${UNIFORM_PPM:-300000}"
# Big well-spaced seed pairs — small seeds (1,2,3) produce zero BNCT reactions
# with the default Geant4 RNG, so we use 8-digit primes.
SEEDS=(11111111 22222223 33333335)
SEEDS2=(98765431 87654319 76543207)

if [[ -f "$GEANT4_ENV" ]]; then source "$GEANT4_ENV"; fi
if [[ -d "$ROOT_DIR" ]]; then
  export ROOTSYS="$ROOT_DIR"
  export PATH="$ROOTSYS/bin:$PATH"
  export LD_LIBRARY_PATH="$ROOTSYS/lib:${LD_LIBRARY_PATH:-}"
fi

mkdir -p build figures results/logs results/generated_macros
cmake -S . -B build >/dev/null
cmake --build build -j"$JOBS"

# shell 等总硼系数 = V_cell / V_shell, cellRadius=5um, shellThickness=1um
# V_shell/V_cell = 1 - (4/5)^3 = 0.488 -> ppm_shell = ppm_uniform / 0.488 = 2.0492
SHELL_FACTOR_BC="scale=6; 1/(1 - (4/5)^3)"
SHELL_FACTOR=$(echo "$SHELL_FACTOR_BC" | bc -l)
SHELL_PPM=$(echo "scale=2; $UNIFORM_PPM * $SHELL_FACTOR / 1" | bc -l)
echo "[experiment A] uniform_equiv=${UNIFORM_PPM} ppm; shell actual=${SHELL_PPM} ppm (factor=${SHELL_FACTOR})"

write_macro() {
  local macro="$1" output="$2" mode="$3" ppm="$4" events="$5" seed1="$6" seed2="$7"
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

/random/setSeeds ${seed1} ${seed2}
/run/initialize
/gun/particle neutron
/gun/energy 0.5 eV
/run/beamOn ${events}
EOF
}

tasks=()
for idx in 0 1 2; do
  seed1="${SEEDS[$idx]}"
  seed2="${SEEDS2[$idx]}"
  s="$((idx+1))"
  # uniform 等效 ppm（实际 ppm = UNIFORM_PPM）
  m="results/generated_macros/q2A_uniform_${UNIFORM_PPM}ppm_seed${s}.mac"
  o="output_q2A_uniform_${UNIFORM_PPM}ppm_seed${s}.root"
  write_macro "$m" "$o" uniform "$UNIFORM_PPM" "$EVENTS_MAIN" "$seed1" "$seed2"
  tasks+=("$m")

  # shell 等 B10 总量（实际 ppm = SHELL_PPM）
  m="results/generated_macros/q2A_shell_${UNIFORM_PPM}ppm_seed${s}.mac"
  o="output_q2A_shell_${UNIFORM_PPM}ppm_seed${s}.root"
  write_macro "$m" "$o" shell "$SHELL_PPM" "$EVENTS_MAIN" "$seed1" "$seed2"
  tasks+=("$m")

  # none 中子背景
  m="results/generated_macros/q2A_none_${UNIFORM_PPM}ppm_seed${s}.mac"
  o="output_q2A_none_${UNIFORM_PPM}ppm_seed${s}.root"
  write_macro "$m" "$o" none 0 "$EVENTS_MAIN" "$seed1" "$seed2"
  tasks+=("$m")
done

echo "[experiment A] running ${#tasks[@]} jobs with ${JOBS}-way parallelism..."
printf '%s\0' "${tasks[@]}" | xargs -0 -n1 -P "$JOBS" bash -c '
  macro="$1"
  name="$(basename "$macro" .mac)"
  echo "  -> $name"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
' _

echo "[experiment A] done. ROOT outputs: output_q2A_*.root"
ls output_q2A_*.root 2>/dev/null | head
