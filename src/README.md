# Source code (`src/`)

This folder contains the Python source code for Lab 3.

A typical organisation is:

- `src/preprocessing/`  
  Scripts and utilities to:
  - Load DICOM mammograms.
  - Convert them to standard image formats.
  - Parse TOMPEI-CMMD annotations.
  - Generate and save binary lesion masks.
  - Build metadata tables.

- `src/radiomics/`  
  Wrappers around **PyRadiomics** and helper functions to:
  - Configure feature extraction parameters.
  - Loop over all lesions.
  - Export radiomic features to CSV files.

- `src/analysis/`  
  Statistical and machine-learning routines to:
  - Perform descriptive statistics and hypothesis testing.
  - Reduce dimensionality (e.g. PCA).
  - Train and evaluate baseline classifiers (Naive Bayes, Random Forest, SVM, etc.).
  - Save metrics, confusion matrices and plots to the `results/` folder.

- `src/utils/` (if present)  
  Shared utility functions (e.g. configuration management, logging, plotting helpers).

## How to use

From the project root (after activating the conda environment):

```bash
# Example: run preprocessing
python -m src.preprocessing.run_preprocessing

# Example: extract radiomic features
python -m src.radiomics.extract_features

# Example: train baseline classifiers
python -m src.analysis.train_baseline_models
