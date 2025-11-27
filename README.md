# Lab 3 – Radiomics and Machine Learning for Breast Cancer (CMMD)

## Important

A practical warning is necessary regarding the execution of the scripts contained in the *preprocessing* folder. Due to the current impossibility of loading and processing the complete cohort of patients (i.e., all image folders and associated clinical data), running these scripts in a partial or incomplete dataset configuration may lead to missing files, empty tables, or misaligned identifiers, which can in turn propagate errors or inconsistencies to the subsequent stages of the pipeline (e.g., radiomics extraction, merging of clinical data, or machine learning analysis). These preprocessing routines were designed and validated under the assumption that the full set of patients is available and correctly structured; therefore, any attempt to execute them with a reduced or incomplete dataset should be done with caution and, ideally, after adapting the paths and filters to the specific subset being used.


## 1. Project overview

This repository contains the code and resources for **Lab 3** of the *Scientific Programming* course.  
The goal is to implement an end-to-end workflow that:

- Loads mammography data from the **CMMD** dataset and corresponding **TOMPEI-CMMD** segmentations.
- Extracts **radiomic features** (shape, intensity, texture) from breast lesions using **PyRadiomics**.
- Structures the resulting features into CSV files suitable for analysis.
- Performs **statistical analyses** and trains **baseline machine-learning models** to discriminate between **benign** lesions and **triple-negative breast cancers (TNBC)**.

The repository is organised to separate data, source code, notebooks, results and installation files, following reproducible research practices.

---

## 2. Theoretical background (short)

### 2.1 Breast cancer and molecular subtypes

Breast cancer is a group of diseases characterised by uncontrolled growth of abnormal cells in breast tissue. It is currently the most commonly diagnosed cancer in women worldwide and remains one of the leading causes of cancer-related death.

From an immunohistochemical point of view, breast cancer can be classified into four main **molecular subtypes**:

- **Luminal A**
- **Luminal B**
- **HER2-positive**
- **Triple-negative (TNBC)**

These subtypes span from best to worst prognosis. **TNBC** is defined by the absence of expression of estrogen receptors (ER), progesterone receptors (PR) and HER2, and is associated with more aggressive clinical behaviour, higher recurrence rates and fewer targeted treatment options.

### 2.2 Why focus on TNBC vs benign lesions?

Despite its biological aggressiveness, **TNBC can sometimes appear benign on imaging**. In mammography and ultrasound, a non-negligible fraction of TNBC lesions may present as oval or round masses with circumscribed margins, mimicking benign findings. This benign-like appearance increases the risk of misdiagnosis and may delay appropriate treatment.

Because of this, there is an interest in using **quantitative image analysis** to support the differentiation between **TNBC** and **benign** lesions, especially in cases where their visual appearance overlaps.

### 2.3 Radiomics and machine learning

**Radiomics** refers to the extraction of a large number of quantitative features from medical images. These features aim to capture:

- **Shape** (2D/3D geometry of the lesion).
- **First-order intensity statistics** (mean, variance, skewness, entropy, etc.).
- **Texture patterns** (spatial relationships of gray levels via GLCM, GLRLM, GLSZM, NGTDM, GLDM, etc.).

Radiomic features can be combined with **machine-learning algorithms** to develop imaging biomarkers for diagnosis, prognosis and treatment response. In this lab, radiomics is used to quantify the appearance of breast lesions on mammography and to explore whether these features contain enough information to **distinguish benign lesions from TNBC**.

---

## 3. Methodology (brief description)

### 3.1 Data

- **Imaging:** Digital mammograms from the **CMMD** public dataset.
- **Segmentations:** Lesion masks from the **TOMPEI-CMMD** resource (MLO view).
- **Labels:** Each lesion is labelled as *benign* or *triple negative*, based on the clinical and immunohistochemical information provided with CMMD.

Only cases with valid segmentations and complete labels are included in the analyses.

### 3.2 Preprocessing

Preprocessing scripts (in `src/preprocessing/`) perform:

1. **DICOM loading and conversion**
   - Read original mammograms in DICOM format.
   - Convert to standard image formats (e.g. TIFF or PNG), ensuring consistent orientation and resolution.

2. **Mask generation**
   - Parse TOMPEI-CMMD annotation files.
   - Generate binary masks aligned with the corresponding mammograms.

3. **Data organisation**
   - Build a folder hierarchy under `data/` for images and masks.
   - Create metadata tables linking each lesion ID to its image path, mask path and class label.

### 3.3 Radiomic feature extraction

Radiomic features are extracted using **PyRadiomics** (see `src/radiomics/` and corresponding notebooks):

- **Inputs:** mammogram + binary lesion mask.
- **Feature families:**
  - `shape2D` features (area, perimeter, major/minor axis length, compactness, roundness, elongation, etc.).
  - `firstorder` features (mean, variance, skewness, kurtosis, energy, entropy, etc.).
  - Texture features derived from GLCM, GLRLM, GLSZM, NGTDM and GLDM matrices.

The output is a consolidated CSV file (stored under `data/processed/`) where each row corresponds to a lesion and columns store radiomic features plus metadata (ID, class label, etc.).

### 3.4 Statistical analysis and baseline classifiers

Analyses implemented in `src/analysis/` and `notebooks/` include:

- **Descriptive statistics and group comparison**
  - Summary statistics per class.
  - Normality tests for each feature.
  - Parametric or non-parametric tests to compare benign vs TNBC for individual features.

- **Dimensionality reduction and visualisation**
  - Principal Component Analysis (PCA) (and optionally other methods) to visualise the distribution of lesions in a low-dimensional space.

- **Baseline machine-learning models**
  - Patient-level split into training, validation and test sets.
  - Training of baseline classifiers such as:
    - Gaussian Naive Bayes
    - Random Forest
    - Support Vector Machine (SVM)
  - Evaluation using metrics such as accuracy, recall/sensitivity, specificity, F1-score and ROC-AUC.

Results are saved as CSV files and plots under the `results/` folder.

---

## 4. Summary of obtained results

At feature level, most radiomic variables exhibit considerable overlap between benign and TNBC lesions, which is consistent with the fact that some TNBC can present benign-like imaging features.

When combining features in multivariate models:

- Baseline classifiers achieve **moderate discrimination** between benign and TNBC.
- Tree-based models (e.g. Random Forest) and margin-based models (SVM) tend to outperform simpler models such as Naive Bayes.
- Feature selection (e.g. LASSO) can reduce the dimensionality of the feature space while maintaining or slightly improving generalisation performance in some cases.

Detailed tables with metrics and confusion matrices, as well as visualisations of PCA and other analyses, are stored under `results/`.

---

## 5. Brief discussion

The main observations from this lab include:

- **Radiomics is informative but not perfect:** Radiomic features capture relevant aspects of lesion morphology and texture, allowing classifiers to perform better than random guessing. However, the separation between benign and TNBC is far from perfect.
- **Clinical difficulty is reflected in the data:** The moderate performance and overlap in feature space highlight the genuine difficulty of distinguishing some TNBC lesions from benign ones using mammography alone.
- **Need for rigorous evaluation:** Using patient-level splits, a held-out test set and multiple metrics helps to obtain realistic estimates of model performance and to avoid overly optimistic conclusions.

These points suggest that radiomics can support—but not replace—expert radiological assessment, and that combining imaging with additional clinical or molecular information may be necessary to further improve discrimination.

---

## 6. Conclusions

In this lab:

1. An **end-to-end radiomics and machine-learning pipeline** was implemented to study the problem of classifying benign vs TNBC lesions in mammography.
2. The pipeline includes **preprocessing**, **radiomic feature extraction**, **statistical analysis** and **baseline classification models**, all integrated in a single repository.
3. Results show that radiomics provides **useful but limited** discriminative power, reflecting the real-world complexity of TNBC diagnosis.
4. The code, notebooks and folder structure are organised to facilitate **reproducibility** and to serve as a basis for more advanced experiments (e.g. additional feature families, other classifiers, multi-class setups, external validation).

---

## 7. Repository structure (lab3 branch)

At the root of the `lab3` branch, the main folders are:

- `data/`  
  Raw, intermediate and processed data (images, masks, radiomic feature tables, metadata).

- `instalation files/`  
  Environment and dependency files (e.g. `environment.yml`, `requirements.txt`) and any scripts needed to recreate the software environment.

- `notebooks/`  
  Jupyter notebooks for interactive preprocessing, feature extraction, statistical analysis and model training.

- `results/`  
  Output files generated by the analyses: metrics tables, confusion matrices, ROC curves, PCA plots, etc.

- `src/`  
  Python source code, organised into modules for preprocessing, radiomics extraction, analysis and utilities.

---

## 8. Installation and setup

### 8.1 Clone the repository and switch to `lab3`

```bash
git clone https://github.com/JuanMorales43/Scientific-programming-ITM-assignments.git
cd Scientific-programming-ITM-assignments
git checkout lab3
