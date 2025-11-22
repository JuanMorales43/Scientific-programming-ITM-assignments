#!/usr/bin/env bash
#
# run.sh – Launcher for Scientific-programming-ITM-assignments
#
# This script runs the main pipeline steps WITHOUT radiomic feature extraction.
# It:
#   - calls Python scripts under src/
#   - checks that required input files/folders exist BEFORE running each step
#   - skips steps that cannot be run (instead of crashing)
#
# Usage examples:
#   ./run.sh            # run full pipeline (except feature extraction)
#   ./run.sh all        # same as above
#   ./run.sh img        # only image preprocessing
#   ./run.sh csv        # only CSV preprocessing
#   ./run.sh lasso      # only LASSO feature selection
#   ./run.sh ml         # only ML experiments (NB, RF, SVM)
#   ./run.sh vis        # only visualization
#
# You can override the Python interpreter with:
#   PYTHON=python3 ./run.sh
#

# Do NOT exit on first error; we want to skip broken steps gracefully
set -u  # but not -e

PYTHON="${PYTHON:-python}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"
CSV_DIR="${SCRIPT_DIR}/results/csv"

# Common folders used by preprocessing scripts
DATA_RAW="${SCRIPT_DIR}/data/raw"
DATA_PROCESSED="${SCRIPT_DIR}/data/processed"
DATA_RAW_CSV="${SCRIPT_DIR}/data/raw csv"   # note the space in the folder name
SEG_RAW="${SCRIPT_DIR}/data/raw/TOMPEI-CMMD-Segmentations"


echo "==================================================================="
echo " Scientific-programming-ITM-assignments – run.sh"
echo " (Radiomic feature extraction is NOT executed here)"
echo " Repository root: ${SCRIPT_DIR}"
echo " Using Python: ${PYTHON}"
echo "==================================================================="
echo

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

check_requirements() {
  # Usage: check_requirements "Label" path1 path2 ...
  local label="$1"; shift
  local missing=()
  local path
  for path in "$@"; do
    # Ignore empty arguments
    if [[ -z "${path}" ]]; then
      continue
    fi
    if [[ ! -e "${path}" ]]; then
      missing+=("${path}")
    fi
  done

  if ((${#missing[@]} > 0)); then
    echo "[SKIP] ${label} – missing required inputs:"
    for m in "${missing[@]}"; do
      echo "       - ${m}"
    done
    echo
    return 1
  fi
  return 0
}

run_step() {
  # Usage: run_step "Label" "relative/python/script.py" [req1 req2 ...]
  local label="$1"
  local rel_script="$2"
  shift 2
  local script="${SRC_DIR}/${rel_script}"

  echo "-------------------------------------------------------------------"
  echo "[STEP] ${label}"
  echo "       Script: ${script}"

  if [[ ! -f "${script}" ]]; then
    echo "[SKIP] Script not found: ${script}"
    echo
    return 0
  fi

  # Check requirements if any were passed
  if ((${#@} > 0)); then
    if ! check_requirements "${label}" "$@"; then
      return 0
    fi
  fi

  # Run the script
  "${PYTHON}" "${script}"
  local status=$?

  if [[ ${status} -ne 0 ]]; then
    echo "[WARN] ${label} finished with a non-zero exit code (${status})."
    echo "       Check the script output/logs if this is unexpected."
  else
    echo "[OK] ${label} finished successfully."
  fi
  echo
}

# ---------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------

run_preprocessing_img() {
  echo "=== Image preprocessing pipeline (preprocessing/img) ==="

  # 1) data/raw → data/processed/<ID>/dcm
  run_step "DICOM → patient folders" \
           "preprocessing/img/dcm2folder.py" \
           "${DATA_RAW}"

  # 2) data/processed DICOM → PNG
  run_step "DICOM → PNG" \
           "preprocessing/img/dcm2png.py" \
           "${DATA_PROCESSED}"

  # 3) data/processed DICOM → TIFF
  run_step "DICOM → TIFF" \
           "preprocessing/img/dmctotiff.py" \
           "${DATA_PROCESSED}"

  # 4) Copy segmentation JSONs into processed structure
  run_step "Copy segmentation JSON" \
           "preprocessing/img/segjson.py" \
           "${SEG_RAW}" "${DATA_PROCESSED}"

  # 5) Generate binary masks from JSON
  run_step "Generate segmentation masks" \
           "preprocessing/img/segmask.py" \
           "${DATA_PROCESSED}"

  # 6) Overlay segmentations on original images
  run_step "Visualize segmentations" \
           "preprocessing/img/segvis.py" \
           "${DATA_PROCESSED}"
}

run_preprocessing_csv() {
  echo "=== CSV preprocessing pipeline (preprocessing/csv) ==="

  local clinical_excel="${DATA_RAW_CSV}/TOMPEI-CMMD_clinical_data_v01_20250121.xlsx"
  local cmmd_excel="${DATA_RAW_CSV}/CMMD_clinicaldata_revision.xlsx"

  # 1) Filter TOMPEI clinical sheets
  run_step "Filter TOMPEI clinical sheets" \
           "preprocessing/csv/csvClinicaldata.py" \
           "${DATA_RAW}" "${DATA_RAW_CSV}" "${clinical_excel}"

  # 2) Filter CMMD clinical data
  run_step "Filter CMMD clinical data" \
           "preprocessing/csv/csvMSG.py" \
           "${DATA_RAW}" "${DATA_RAW_CSV}" "${cmmd_excel}"

  # 3) Clean molecular subtype & copy folders
  run_step "Clean molecular subtype & copy folders" \
           "preprocessing/csv/Molecularsubtypeclean.py" \
           "${DATA_RAW}" "${DATA_RAW_CSV}" "${cmmd_excel}"

  # 4) Merge radiomics + subtype + BI-RADS
  #    This REQUIRES radiomics_features.csv to already exist.
  local csv_radiomics="${CSV_DIR}/radiomics_features.csv"
  local csv_cmmd_clean="${CSV_DIR}/CMMD_clinicaldata_revision_clean.csv"
  local csv_tompei_diag="${CSV_DIR}/TOMPEI-CMMD_imaging_diagnosis_details.csv"

  run_step "Merge radiomics + subtype + BI-RADS" \
           "preprocessing/csv/csv_radiomics_MS_Birads.py" \
           "${csv_radiomics}" "${csv_cmmd_clean}" "${csv_tompei_diag}"
}

run_lasso() {
  echo "=== LASSO feature selection (analysis/LASSO.py) ==="

  local radiomics_merged="${CSV_DIR}/radiomics_merged.csv"

  run_step "LASSO feature selection (no feature extraction)" \
           "analysis/LASSO.py" \
           "${radiomics_merged}"
}

run_ml_all() {
  echo "=== ML experiments (NB, RF, SVM; with and without LASSO) ==="

  local radiomics_merged="${CSV_DIR}/radiomics_merged.csv"
  local radiomics_lasso="${CSV_DIR}/radiomics_lasso_subset.csv"
  local bn_cercanos="${CSV_DIR}/BN_cercanos.csv"
  local tn_cercanos="${CSV_DIR}/TN_cercanos.csv"
  local splits="${CSV_DIR}/splits.csv"

  # Naive Bayes
  run_step "Gaussian Naive Bayes (all features)" \
           "analysis/ML/NB/NB.py" \
           "${radiomics_merged}" "${bn_cercanos}" "${tn_cercanos}" "${splits}"

  run_step "Gaussian Naive Bayes (LASSO subset)" \
           "analysis/ML/NB/NB_LASSO.py" \
           "${radiomics_lasso}" "${bn_cercanos}" "${tn_cercanos}" "${splits}"

  # Random Forest
  run_step "Random Forest (all features)" \
           "analysis/ML/RF/RF.py" \
           "${radiomics_merged}" "${bn_cercanos}" "${tn_cercanos}" "${splits}"

  run_step "Random Forest (LASSO subset)" \
           "analysis/ML/RF/RF_LASSO.py" \
           "${radiomics_lasso}" "${bn_cercanos}" "${tn_cercanos}" "${splits}"

  # SVM
  run_step "SVM (all features)" \
           "analysis/ML/SVM/SVM.py" \
           "${radiomics_merged}" "${bn_cercanos}" "${tn_cercanos}" "${splits}"

  run_step "SVM (LASSO subset)" \
           "analysis/ML/SVM/SVM_LASSO.py" \
           "${radiomics_lasso}" "${bn_cercanos}" "${tn_cercanos}" "${splits}"
}

run_visualization() {
  echo "=== Visualization (PCA / distances / silhouette) ==="

  local radiomics_merged="${CSV_DIR}/radiomics_merged.csv"

  run_step "PCA / distance / silhouette visualization" \
           "visualization/visradiomicsPCA.py" \
           "${radiomics_merged}"
}

run_all() {
  run_preprocessing_img
  run_preprocessing_csv
  run_lasso
  run_ml_all
  run_visualization
}

print_usage() {
  cat <<EOF
Usage: $(basename "$0") [all|img|csv|lasso|ml|vis]

  all    – run full pipeline (EXCEPT radiomic feature extraction)
  img    – run only image preprocessing (preprocessing/img)
  csv    – run only CSV preprocessing (preprocessing/csv)
  lasso  – run only LASSO feature selection (analysis/LASSO.py)
  ml     – run only ML experiments (NB, RF, SVM)
  vis    – run only visualization (PCA / distances / silhouette)

You can set the Python interpreter via:
  PYTHON=python3 $(basename "$0") all
EOF
}

# ---------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------

CMD="${1:-all}"

case "${CMD}" in
  all)
    run_all
    ;;
  img)
    run_preprocessing_img
    ;;
  csv)
    run_preprocessing_csv
    ;;
  lasso)
    run_lasso
    ;;
  ml)
    run_ml_all
    ;;
  vis)
    run_visualization
    ;;
  -h|--help|help)
    print_usage
    ;;
  *)
    echo "Unknown command: ${CMD}"
    echo
    print_usage
    exit 1
    ;;
esac
