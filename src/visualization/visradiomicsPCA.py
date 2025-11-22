import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_score, silhouette_samples
import os

"""
Exploratory visualization of radiomic features using PCA and distance analysis.

This script:
- Loads the `radiomics_merged.csv` file from `results/csv`.
- Selects the radiomic feature columns (`original_*`) and
  the variables of interest (class, subtype, etc.).
- Standardizes the features and applies Principal Component Analysis
  (PCA) to reduce the dimensionality to 2 components.
- Generates scatter plots (PC1 vs PC2) colored by class or molecular subtype
  to explore the separability between groups (e.g., benign
  vs triple negative).
- Calculates distances (e.g., Mahalanobis or Euclidean) between cases and
  constructs distance matrices to analyze the similarity between lesions.
- Evaluates clustering indices such as the silhouette coefficient and produces
  additional visualizations (heat maps, silhouette coloring, etc.).
- Save the resulting figures in the `results/vis/PCA` folder.

Its purpose is to provide a global visualization of the radiomic feature space
and support the interpretation of separability
between classes and molecular subtypes.
"""
# Files paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
csv_dir = os.path.join (REPO_ROOT, "results", "csv")

ruta_csv = os.path.join (csv_dir, "radiomics_merged.csv")
ruta_salida = os.path.join (REPO_ROOT, "results", "vis", "PCA")
os.makedirs(ruta_salida, exist_ok=True)

# Load data
df = pd.read_csv(ruta_csv)

# Filter groups
grupo1 = df[df['subtype'] == 'triple negative'].copy()
grupo2 = df[df['classification_cmmd'] == 'Benign'].copy()

# Select shape2D features
cols_shape2D = [col for col in df.columns if col.startswith('original_shape2D_')]

# Combine groups
grupo1['grupo'] = 'triple negative'
grupo2['grupo'] = 'Benign'
df_sel = pd.concat([grupo1, grupo2], ignore_index=True)

# Select features and labels
X = df_sel[cols_shape2D]
y = df_sel['grupo']

print(f"Data loaded: {len(X)} samples, {len(cols_shape2D)} features")

X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(X.mean())

# Check for remaining NaN values
if X.isnull().any().any():
    print("⚠️ Warning: Still NaN values present after imputation. Filling with 0.")
    X = X.fillna(0)

# Convert to numpy array of type float64
X_array = X.values.astype(np.float64)

print(f"Shape de X: {X_array.shape}")
print(f"Tipo de datos: {X_array.dtype}")

print("\n" + "="*60)
print("Ejecutando PCA...")
print("="*60)

# PCA
pca = PCA(n_components=2, random_state=42)
embedding = pca.fit_transform(X_array)

# Show explained variance
print(f"\n✓ PCA completed!")
print(f"Variance PC1: {pca.explained_variance_ratio_[0]*100:.2f}%")
print(f"Variance PC2: {pca.explained_variance_ratio_[1]*100:.2f}%")
print(f"Total variance: {pca.explained_variance_ratio_.sum()*100:.2f}%")

# Plot PCA
plt.figure(figsize=(8,6))
for grupo in ['triple negative', 'Benign']:
    idx = y == grupo
    plt.scatter(embedding[idx,0], embedding[idx,1], label=grupo, alpha=0.7)
plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
plt.title('PCA de original_shape2D_ features')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{ruta_salida}/pca_shape2D.png', dpi=300)
plt.close()
print(f"✓ Saved plot: {ruta_salida}/pca_shape2D.png")