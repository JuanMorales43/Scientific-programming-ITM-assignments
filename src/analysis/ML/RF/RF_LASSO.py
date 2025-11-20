import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score
)
from sklearn.preprocessing import StandardScaler

# ==========================
# 0. Carpeta de salida
# ==========================
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
output_dir = os.path.join (REPO_ROOT,"results", "ML", "RF_LASSO")
csv_dir = os.path.join (REPO_ROOT, "results", "csv")
os.makedirs(output_dir, exist_ok=True)

# ==========================
# 1. Cargar datos
# ==========================
ruta_csv_radiomics = os.path.join (csv_dir,"radiomics_lasso_subset.csv")
ruta_csv_BN = os.path.join (csv_dir, "BN_cercanos.csv")
ruta_csv_TN = os.path.join (csv_dir, "TN_cercanos.csv")

# ⚠️ Ajusta esta ruta si tu splits.csv está en otro sitio
ruta_splits = os.path.join (csv_dir, "splits.csv")


df_radiomics = pd.read_csv(ruta_csv_radiomics)
df_bn = pd.read_csv(ruta_csv_BN)
df_tn = pd.read_csv(ruta_csv_TN)
df_splits = pd.read_csv(ruta_splits)

# IDs de pacientes
bn_ids = set(df_bn['Pacientes BN'])
tn_ids = set(df_tn['Paciente TN'])

# Filtrar pacientes BN y TN en radiomics
df_bn_radiomics = df_radiomics[df_radiomics['ID'].isin(bn_ids)].copy()
df_tn_radiomics = df_radiomics[df_radiomics['ID'].isin(tn_ids)].copy()

# Etiquetas: 0 = BN, 1 = TN
df_bn_radiomics['label'] = 0
df_tn_radiomics['label'] = 1

# Unir ambos grupos
df_all = pd.concat([df_bn_radiomics, df_tn_radiomics], ignore_index=True)

# ==========================
# 2. Unir con splits.csv para asignar train/val/test
# ==========================
df_merged = df_all.merge(df_splits[['ID', 'split']], on='ID', how='inner')

# Features radiómicas
feature_cols = [col for col in df_merged.columns if col.startswith('original_')]

# Separar por split
df_train = df_merged[df_merged['split'] == 'train']
df_val   = df_merged[df_merged['split'] == 'val']
df_test  = df_merged[df_merged['split'] == 'test']

X_train = df_train[feature_cols]
y_train = df_train['label']

X_val   = df_val[feature_cols]
y_val   = df_val['label']

X_test  = df_test[feature_cols]
y_test  = df_test['label']

print("Tamaños:", X_train.shape, X_val.shape, X_test.shape)

# ==========================
# 3. Normalizar con Z-score (fit SOLO en train)
# ==========================
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val   = scaler.transform(X_val)
X_test  = scaler.transform(X_test)

# ==========================
# 4. Entrenar Random Forest en TRAIN
# ==========================
clf = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)
clf.fit(X_train, y_train)

# ==========================
# 5. Evaluar en VALIDACIÓN
# ==========================
y_pred = clf.predict(X_val)
y_pred_proba = clf.predict_proba(X_val)[:, 1]  # prob de TN = 1

print("\n=== Resultados en VALIDACIÓN ===")
accuracy = accuracy_score(y_val, y_pred)
print("Accuracy:", accuracy)
print(classification_report(y_val, y_pred, target_names=['BN', 'TN']))

# Métricas puntuales
vpp_tn  = precision_score(y_val, y_pred, pos_label=1)
aucroc  = roc_auc_score(y_val, y_pred_proba)
sens_tn = recall_score(y_val, y_pred, pos_label=1)
esp_bn  = recall_score(y_val, y_pred, pos_label=0)
f1_tn   = f1_score(y_val, y_pred, pos_label=1)

print(f"AUC-ROC (TN = 1): {aucroc:.4f}")
print(f"VPP TN: {vpp_tn:.4f}")
print(f"Sensibilidad TN: {sens_tn:.4f}")
print(f"Especificidad BN: {esp_bn:.4f}")
print(f"F1 TN: {f1_tn:.4f}")

# ==========================
# # 6. Matriz de confusión (guardar)
# ==========================
cm = confusion_matrix(y_val, y_pred)
fig_cm, ax_cm = plt.subplots()
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['BN', 'TN'])
disp.plot(ax=ax_cm)
ax_cm.set_title('Matriz de Confusión Random Forest (Validación)')
fig_cm.tight_layout()
cm_path = os.path.join(output_dir, "matriz_confusion.png")
fig_cm.savefig(cm_path, dpi=300, bbox_inches='tight')
plt.close(fig_cm)

# ==========================
# 7. Curva ROC (guardar)
# ==========================
fig_roc, ax_roc = plt.subplots()
RocCurveDisplay.from_predictions(y_val, y_pred_proba, name='RF', pos_label=1, ax=ax_roc)
ax_roc.plot([0, 1], [0, 1], '--', label='Azar')
ax_roc.set_title('Curva ROC Random Forest (Validación)')
ax_roc.legend(loc='lower right')
fig_roc.tight_layout()
roc_path = os.path.join(output_dir, "aucroc.png")
fig_roc.savefig(roc_path, dpi=300, bbox_inches='tight')
plt.close(fig_roc)

# ==========================
# 8. Bootstrap: intervalos de confianza
# ==========================
def bootstrap_ci_metric(y_true, y_pred, metric_func,
                        n_bootstraps=1000, alpha=0.95, random_state=42):
    rng = np.random.RandomState(random_state)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)
    stats = []

    for _ in range(n_bootstraps):
        idx = rng.randint(0, n, n)  # con reemplazo
        y_bs = y_true[idx]
        p_bs = y_pred[idx]
        stats.append(metric_func(y_bs, p_bs))

    stats = np.array(stats)
    lower = np.percentile(stats, (1 - alpha) / 2 * 100)
    upper = np.percentile(stats, (1 + alpha) / 2 * 100)
    return stats.mean(), lower, upper

def ci_auc_bootstrap(y_true, y_score,
                     n_bootstraps=1000, alpha=0.95, random_state=42):
    rng = np.random.RandomState(random_state)
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    n = len(y_true)
    aucs = []

    for _ in range(n_bootstraps):
        idx = rng.randint(0, n, n)
        y_bs = y_true[idx]
        s_bs = y_score[idx]

        # necesitamos ambas clases
        if len(np.unique(y_bs)) < 2:
            continue

        aucs.append(roc_auc_score(y_bs, s_bs))

    aucs = np.array(aucs)
    lower = np.percentile(aucs, (1 - alpha) / 2 * 100)
    upper = np.percentile(aucs, (1 + alpha) / 2 * 100)
    return aucs.mean(), lower, upper

# Accuracy
_, acc_low, acc_up = bootstrap_ci_metric(y_val, y_pred, accuracy_score)

# AUC-ROC
_, auc_low, auc_up = ci_auc_bootstrap(y_val, y_pred_proba)

# VPP TN
_, vpp_low, vpp_up = bootstrap_ci_metric(
    y_val, y_pred,
    lambda yt, yp: precision_score(yt, yp, pos_label=1)
)

# Sensibilidad TN
_, sens_low, sens_up = bootstrap_ci_metric(
    y_val, y_pred,
    lambda yt, yp: recall_score(yt, yp, pos_label=1)
)

# Especificidad BN
_, esp_low, esp_up = bootstrap_ci_metric(
    y_val, y_pred,
    lambda yt, yp: recall_score(yt, yp, pos_label=0)
)

# F1 TN
_, f1_low, f1_up = bootstrap_ci_metric(
    y_val, y_pred,
    lambda yt, yp: f1_score(yt, yp, pos_label=1)
)

print(f"IC95% AUC-ROC: [{auc_low:.4f}, {auc_up:.4f}]")
print(f"IC95% Accuracy: [{acc_low:.4f}, {acc_up:.4f}]")
print(f"IC95% VPP_TN: [{vpp_low:.4f}, {vpp_up:.4f}]")
print(f"IC95% Sensibilidad_TN: [{sens_low:.4f}, {sens_up:.4f}]")
print(f"IC95% Especificidad_BN: [{esp_low:.4f}, {esp_up:.4f}]")
print(f"IC95% F1_TN: [{f1_low:.4f}, {f1_up:.4f}]")

# ==========================
# 9. Guardar métricas en CSV (agrupadas)
# ==========================
metrics_df = pd.DataFrame({
    'Metric': [
        'Accuracy_CI_lower_bound',
        'Accuracy',
        'Accuracy_CI_upper_bound',

        'AUC-ROC_CI_lower_bound',
        'AUC-ROC',
        'AUC-ROC_CI_upper_bound',

        'VPP_TN_CI_lower_bound',
        'VPP_TN',
        'VPP_TN_CI_upper_bound',

        'Sensibilidad_TN_CI_lower_bound',
        'Sensibilidad_TN',
        'Sensibilidad_TN_CI_upper_bound',

        'Especificidad_BN_CI_lower_bound',
        'Especificidad_BN',
        'Especificidad_BN_CI_upper_bound',

        'F1_TN_CI_lower_bound',
        'F1_TN',
        'F1_TN_CI_upper_bound'
    ],
    'Value': [
        acc_low,
        accuracy,
        acc_up,

        auc_low,
        aucroc,
        auc_up,

        vpp_low,
        vpp_tn,
        vpp_up,

        sens_low,
        sens_tn,
        sens_up,

        esp_low,
        esp_bn,
        esp_up,

        f1_low,
        f1_tn,
        f1_up
    ]
})

metrics_path = os.path.join(output_dir, "metrics.csv")
metrics_df.to_csv(metrics_path, index=False)

print(f"\nMétricas guardadas en: {metrics_path}")
print(f"Matriz de confusión guardada en: {cm_path}")
print(f"Curva ROC guardada en: {roc_path}")