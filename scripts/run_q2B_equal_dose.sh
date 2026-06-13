#!/usr/bin/env bash
# Q2 重设计 — 实验 B：跨疗法等剂量对照（H2）
# 策略：
#   (1) 探针：四组（gamma/proton/uniform/shell）各跑 PROBE_EVENTS=200k
#   (2) 用 ROOT 读出每组 tumor 细胞平均剂量 D_tumor
#   (3) 按 D_target / D_tumor 线性外推所需 events，cap 在 FINAL_EVENTS_MAX
#   (4) 跑正式跑次
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

GEANT4_ENV="${GEANT4_ENV:-/home/yoru/packages/geant4-11.4.0/bin/geant4.sh}"
ROOT_DIR="${ROOT_DIR:-/home/yoru/packages/root}"
JOBS="${JOBS:-12}"
PROBE_EVENTS="${PROBE_EVENTS:-200000}"
D_TARGET_GY="${D_TARGET_GY:-2.0}"
FINAL_EVENTS_MAX="${FINAL_EVENTS_MAX:-2000000}"
FINAL_EVENTS_MIN="${FINAL_EVENTS_MIN:-200000}"
UNIFORM_PPM="${UNIFORM_PPM:-300000}"

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
SHELL_PPM=$(echo "scale=2; $UNIFORM_PPM * $SHELL_FACTOR / 1" | bc -l)

# group: name|boronMode|ppm|particle|energy
# (use Q2B_GROUPS to avoid conflict with bash built-in $GROUPS array)
Q2B_GROUPS=(
  "gamma|none|0|gamma|1 MeV"
  "proton|none|0|proton|80 MeV"
  "neutron_uniform|uniform|${UNIFORM_PPM}|neutron|0.5 eV"
  "neutron_shell|shell|${SHELL_PPM}|neutron|0.5 eV"
)

write_macro() {
  local macro="$1" output="$2" mode="$3" ppm="$4" particle="$5" energy="$6" events="$7" seed1="$8" seed2="$9"
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
/gun/particle ${particle}
/gun/energy ${energy}
/run/beamOn ${events}
EOF
}

PROBE_SEED1=11111111
PROBE_SEED2=98765431
FINAL_SEED1=22222223
FINAL_SEED2=87654319

# Step 1: probe runs
probe_tasks=()
for spec in "${Q2B_GROUPS[@]}"; do
  IFS='|' read -r name mode ppm particle energy <<< "$spec"
  m="results/generated_macros/q2B_${name}_probe.mac"
  o="output_q2B_${name}_probe.root"
  write_macro "$m" "$o" "$mode" "$ppm" "$particle" "$energy" "$PROBE_EVENTS" "$PROBE_SEED1" "$PROBE_SEED2"
  probe_tasks+=("$m")
done

echo "[experiment B] probing ${#probe_tasks[@]} groups @ ${PROBE_EVENTS} events..."
printf '%s\0' "${probe_tasks[@]}" | xargs -0 -n1 -P "$JOBS" bash -c '
  macro="$1"; name="$(basename "$macro" .mac)"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
' _

# Step 2: read tumor-cell mean dose and compute scale factors
declare -A SCALE
set +e  # allow root's cling non-fatal exit 255 without killing the script
for spec in "${Q2B_GROUPS[@]}"; do
  IFS='|' read -r name mode ppm particle energy <<< "$spec"
  o="output_q2B_${name}_probe.root"
  d_tumor=$(root -l -b -q -e "
    TFile f(\"$o\");
    auto t=(TTree*)f.Get(\"CellTree\");
    if(!t){cout<<0<<endl; return;}
    t->Draw(\"doseCell_Gy>>htmp(1,0,1e9)\",\"cellType==1\",\"goff\");
    cout<<t->GetHistogram()->GetMean()<<endl;
  " 2>/dev/null | tail -1)
  if [[ -z "$d_tumor" || "$d_tumor" == "0" ]]; then
    scale=10
    echo "  [WARN] ${name} probe gave zero tumor dose; using max scaling"
  else
    scale=$(echo "scale=4; $D_TARGET_GY / $d_tumor" | bc -l)
  fi
  SCALE[$name]=$scale
  echo "  ${name}: D_tumor(probe)=${d_tumor} Gy -> scale=${scale}"
done
set -e

# Step 3: write final macros with scaled events
final_tasks=()
for spec in "${Q2B_GROUPS[@]}"; do
  IFS='|' read -r name mode ppm particle energy <<< "$spec"
  scale="${SCALE[$name]}"
  raw=$(echo "scale=0; $PROBE_EVENTS * $scale / 1" | bc -l)
  # clamp
  if (( raw > FINAL_EVENTS_MAX )); then raw=$FINAL_EVENTS_MAX; fi
  if (( raw < FINAL_EVENTS_MIN )); then raw=$FINAL_EVENTS_MIN; fi
  m="results/generated_macros/q2B_${name}_final.mac"
  o="output_q2B_${name}_final.root"
  write_macro "$m" "$o" "$mode" "$ppm" "$particle" "$energy" "$raw" "$FINAL_SEED1" "$FINAL_SEED2"
  final_tasks+=("$m")
  echo "  final ${name}: events=${raw}"
done

echo "[experiment B] running ${#final_tasks[@]} final jobs..."
printf '%s\0' "${final_tasks[@]}" | xargs -0 -n1 -P "$JOBS" bash -c '
  macro="$1"; name="$(basename "$macro" .mac)"
  echo "  -> $name"
  ./build/tumor_therapy "$macro" > "results/logs/${name}.log" 2>&1
' _

echo "[experiment B] done."
ls output_q2B_*_final.root 2>/dev/null
