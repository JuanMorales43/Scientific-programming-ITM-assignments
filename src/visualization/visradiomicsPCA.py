import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_score, silhouette_samples
import os
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
csv_dir = os.path.join (REPO_ROOT, "results", "csv")

ruta_csv = os.path.join (csv_dir, "radiomics_merged.csv")
ruta_salida = os.path.join (REPO_ROOT, "results", "vis", "PCA")

# Crear carpeta de salida si no existe
os.makedirs(ruta_salida, exist_ok=True)

# Cargar datos
df = pd.read_csv(ruta_csv)

# Filtrar grupos
grupo1 = df[df['subtype'] == 'triple negative'].copy()
grupo2 = df[df['classification_cmmd'] == 'Benign'].copy()

# Seleccionar columnas que empiezan con original_shape2D_
cols_shape2D = [col for col in df.columns if col.startswith('original_shape2D_')]

# Concatenar ambos grupos y crear columna de grupo
grupo1['grupo'] = 'triple negative'
grupo2['grupo'] = 'Benign'
df_sel = pd.concat([grupo1, grupo2], ignore_index=True)

# Seleccionar solo las columnas shape2D y el grupo
X = df_sel[cols_shape2D]
y = df_sel['grupo']

print(f"Datos cargados: {len(X)} muestras, {len(cols_shape2D)} características")

# Manejar NaN/Inf de forma robusta
X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(X.mean())

# Verificar que no queden NaN
if X.isnull().any().any():
    print("⚠️ Advertencia: Aún hay valores NaN. Rellenando con 0...")
    X = X.fillna(0)

# Convertir a numpy array explícitamente
X_array = X.values.astype(np.float64)

print(f"Shape de X: {X_array.shape}")
print(f"Tipo de datos: {X_array.dtype}")

print("\n" + "="*60)
print("Ejecutando PCA...")
print("="*60)

# PCA
pca = PCA(n_components=2, random_state=42)
embedding = pca.fit_transform(X_array)

# Mostrar varianza explicada
print(f"\n✓ PCA completado!")
print(f"Varianza explicada por PC1: {pca.explained_variance_ratio_[0]*100:.2f}%")
print(f"Varianza explicada por PC2: {pca.explained_variance_ratio_[1]*100:.2f}%")
print(f"Varianza total explicada: {pca.explained_variance_ratio_.sum()*100:.2f}%")

# Graficar PCA original
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
print(f"✓ Gráfico guardado: {ruta_salida}/pca_shape2D.png")

# ============================================================
# ANÁLISIS DE SILHOUETTE
# ============================================================

print("\n" + "="*60)
print("ANÁLISIS DE SUPERPOSICIÓN CON SILHOUETTE")
print("="*60)

# Calcular Silhouette Score global
silhouette_avg = silhouette_score(embedding, y)
print(f"\nSILHOUETTE SCORE GLOBAL: {silhouette_avg:.3f}")
if silhouette_avg > 0.5:
    print("→ Buena separación entre grupos ✓")
elif silhouette_avg > 0.25:
    print("→ Separación moderada")
else:
    print("→ Alta superposición entre grupos ✗")

# Calcular Silhouette por paciente
silhouette_vals = silhouette_samples(embedding, y)

# Añadir al DataFrame
df_sel['silhouette'] = silhouette_vals
df_sel['caso_id'] = range(len(df_sel))

# Estadísticas por grupo
print(f"\n{'='*60}")
print("SILHOUETTE POR GRUPO")
print("="*60)

for grupo in ['triple negative', 'Benign']:
    vals = silhouette_vals[y == grupo]
    print(f"\n🔵 {grupo.upper()}:")
    print(f"   Media:    {vals.mean():.3f}")
    print(f"   Mediana:  {np.median(vals):.3f}")
    print(f"   Std:      {vals.std():.3f}")
    print(f"   Min:      {vals.min():.3f}")
    print(f"   Max:      {vals.max():.3f}")
    
    # Contar casos problemáticos
    negativos = (vals < 0).sum()
    frontera = ((vals >= 0) & (vals < 0.2)).sum()
    bien_agrupados = (vals >= 0.5).sum()
    moderados = len(vals) - bien_agrupados - frontera - negativos
    
    print(f"\n   Distribución:")
    print(f"   - Bien agrupados (≥0.5):     {bien_agrupados:3d} ({bien_agrupados/len(vals)*100:5.1f}%)")
    print(f"   - Moderados (0.2-0.5):       {moderados:3d} ({moderados/len(vals)*100:5.1f}%)")
    print(f"   - En frontera (0-0.2):       {frontera:3d} ({frontera/len(vals)*100:5.1f}%)")
    print(f"   - Mal agrupados (<0):        {negativos:3d} ({negativos/len(vals)*100:5.1f}%)")

# Identificar casos más superpuestos
casos_superpuestos = df_sel[df_sel['silhouette'] < 0.2].sort_values('silhouette')

print(f"\n{'='*60}")
print(f"⚠️  CASOS MÁS SUPERPUESTOS (silhouette < 0.2): {len(casos_superpuestos)} casos")
print("="*60)
if len(casos_superpuestos) > 0:
    print("\nTop 10 casos más superpuestos:")
    print(casos_superpuestos[['caso_id', 'grupo', 'silhouette']].head(10).to_string(index=False))
else:
    print("\n¡No hay casos superpuestos! Todos tienen silhouette ≥ 0.2")

# Guardar resultados
casos_superpuestos[['caso_id', 'grupo', 'silhouette']].to_csv(
    f'{ruta_salida}/casos_superpuestos.csv', index=False
)
print(f"\n✓ Casos superpuestos guardados en: {ruta_salida}/casos_superpuestos.csv")

# Guardar todos los scores de silhouette
df_sel[['caso_id', 'grupo', 'silhouette']].to_csv(
    f'{ruta_salida}/silhouette_scores.csv', index=False
)
print(f"✓ Todos los scores guardados en: {ruta_salida}/silhouette_scores.csv")

# ============================================================
# VISUALIZACIONES
# ============================================================

print("\nGenerando visualizaciones...")

# Figura 1: PCA coloreado por Silhouette
plt.figure(figsize=(14, 6))

# Subplot 1: Por grupo (original)
plt.subplot(1, 2, 1)
for grupo in ['triple negative', 'Benign']:
    idx = y == grupo
    plt.scatter(embedding[idx, 0], embedding[idx, 1], label=grupo, alpha=0.7, s=60)
plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)', fontsize=11)
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)', fontsize=11)
plt.title('PCA por grupo', fontsize=12, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)

# Subplot 2: Por Silhouette
plt.subplot(1, 2, 2)
scatter = plt.scatter(embedding[:, 0], embedding[:, 1], 
                     c=silhouette_vals, 
                     cmap='RdYlGn',  # Rojo=mal agrupado, Verde=bien agrupado
                     vmin=-0.5, vmax=1.0,
                     alpha=0.8, s=60, edgecolors='black', linewidth=0.5)
cbar = plt.colorbar(scatter, label='Silhouette Score')
cbar.ax.axhline(y=0, color='black', linewidth=2, linestyle='--')
cbar.ax.axhline(y=0.2, color='orange', linewidth=1.5, linestyle='--')
cbar.ax.axhline(y=0.5, color='green', linewidth=1.5, linestyle='--')

plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)', fontsize=11)
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)', fontsize=11)
plt.title('PCA coloreado por Silhouette\n(Verde=bien agrupado, Rojo=superpuesto)', 
          fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3)

# Marcar los 5 casos más problemáticos
if len(casos_superpuestos) >= 5:
    peores_idx = casos_superpuestos.head(5)['caso_id'].values
    plt.scatter(embedding[peores_idx, 0], embedding[peores_idx, 1], 
               s=200, facecolors='none', edgecolors='red', linewidth=2.5, 
               label='5 casos más superpuestos', zorder=5)
    plt.legend(loc='best')

plt.tight_layout()
plt.savefig(f'{ruta_salida}/pca_silhouette_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Gráfico guardado: {ruta_salida}/pca_silhouette_analysis.png")

# Figura 2: Distribución de Silhouette por grupo
plt.figure(figsize=(12, 5))

# Histograma
plt.subplot(1, 2, 1)
for grupo, color in zip(['triple negative', 'Benign'], ['blue', 'orange']):
    vals = silhouette_vals[y == grupo]
    plt.hist(vals, bins=30, alpha=0.6, label=grupo, color=color, edgecolor='black')
plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Silhouette = 0')
plt.axvline(x=0.2, color='orange', linestyle='--', linewidth=1.5, label='Silhouette = 0.2')
plt.axvline(x=0.5, color='green', linestyle='--', linewidth=1.5, label='Silhouette = 0.5')
plt.xlabel('Silhouette Score', fontsize=11)
plt.ylabel('Frecuencia', fontsize=11)
plt.title('Distribución de Silhouette Score', fontsize=12, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3, axis='y')

# Boxplot
plt.subplot(1, 2, 2)
data_boxplot = [silhouette_vals[y == 'triple negative'], 
                silhouette_vals[y == 'Benign']]
bp = plt.boxplot(data_boxplot, labels=['Triple Negative', 'Benign'],
                 patch_artist=True, widths=0.6)
bp['boxes'][0].set_facecolor('lightblue')
bp['boxes'][1].set_facecolor('lightsalmon')

# Añadir líneas de referencia
plt.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Frontera')
plt.axhline(y=0.5, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Bien agrupado')
plt.ylabel('Silhouette Score', fontsize=11)
plt.title('Boxplot de Silhouette Score', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3, axis='y')
plt.legend()

plt.tight_layout()
plt.savefig(f'{ruta_salida}/silhouette_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Gráfico guardado: {ruta_salida}/silhouette_distribution.png")

# Figura 3: Scree plot (varianza explicada)
plt.figure(figsize=(10, 5))

# Calcular PCA con todos los componentes para scree plot
pca_full = PCA()
pca_full.fit(X_array)

plt.subplot(1, 2, 1)
plt.plot(range(1, len(pca_full.explained_variance_ratio_) + 1), 
         pca_full.explained_variance_ratio_ * 100, 'bo-', linewidth=2)
plt.xlabel('Componente Principal', fontsize=11)
plt.ylabel('Varianza Explicada (%)', fontsize=11)
plt.title('Scree Plot', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.xlim(0.5, min(10, len(pca_full.explained_variance_ratio_)) + 0.5)

plt.subplot(1, 2, 2)
cumsum = np.cumsum(pca_full.explained_variance_ratio_ * 100)
plt.plot(range(1, len(cumsum) + 1), cumsum, 'ro-', linewidth=2)
plt.axhline(y=80, color='green', linestyle='--', linewidth=1.5, label='80% varianza')
plt.axhline(y=90, color='orange', linestyle='--', linewidth=1.5, label='90% varianza')
plt.xlabel('Número de Componentes', fontsize=11)
plt.ylabel('Varianza Acumulada (%)', fontsize=11)
plt.title('Varianza Acumulada', fontsize=12, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(0.5, min(10, len(cumsum)) + 0.5)

plt.tight_layout()
plt.savefig(f'{ruta_salida}/pca_scree_plot.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Gráfico guardado: {ruta_salida}/pca_scree_plot.png")

print(f"\n{'='*60}")
print("✓ ANÁLISIS COMPLETADO!")
print("="*60)
print("\nArchivos generados:")
print(f"  1. {ruta_salida}/pca_shape2D.png")
print(f"  2. {ruta_salida}/pca_silhouette_analysis.png")
print(f"  3. {ruta_salida}/silhouette_distribution.png")
print(f"  4. {ruta_salida}/pca_scree_plot.png")
print(f"  5. {ruta_salida}/casos_superpuestos.csv")
print(f"  6. {ruta_salida}/silhouette_scores.csv")
print("="*60)