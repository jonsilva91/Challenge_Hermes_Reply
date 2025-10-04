import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# --- Configuração do Banco de Dados ---
DB_NAME = os.getenv("DB_NAME", "preventai_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def fetch_data_from_db():
    """Busca os dados do CSV original para simular o dataset de treino."""
    print("Carregando dados do arquivo 'predictive_maintenance.csv' para o treino...")
    # Nota: Em um cenário real, os dados viriam de queries complexas no banco.
    # Para este MVP, usamos o CSV original que foi carregado no banco.
    file_path = os.path.join(os.path.dirname(
        __file__), "predictive_maintenance.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}. Certifique-se de que ele está na pasta /ml.")
    df = pd.read_csv(file_path)
    print("Dados carregados com sucesso.")
    return df


# Carregar dados do banco (simulado pelo CSV)
df = fetch_data_from_db()

# --- Engenharia de Atributos ---
print("Criando novas features (Engenharia de Atributos)...")
# 1. Potência (interação entre torque e velocidade)
df['Power [W]'] = df['Torque [Nm]'] * df['Rotational speed [rpm]']
# 2. Diferença de Temperatura
df['TempDiff [K]'] = df['Process temperature [K]'] - df['Air temperature [K]']

# Features e target
X = df[["Air temperature [K]", "Process temperature [K]",
        "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]",
        "Power [W]", "TempDiff [K]"]]
y = df["Target"]

# Divisão treino/teste
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# Escalonamento
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# --- Otimização de Hiperparâmetros com GridSearchCV ---
print("\nIniciando otimização de hiperparâmetros com GridSearchCV...")
param_grid = {
    'n_estimators': [100, 150],
    'max_depth': [10, 20, None],
    'min_samples_leaf': [1, 2]
}

rf = RandomForestClassifier(random_state=42, class_weight='balanced')
grid_search = GridSearchCV(
    estimator=rf, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2, scoring='recall')

grid_search.fit(X_train_scaled, y_train)

print(f"Melhores parâmetros encontrados: {grid_search.best_params_}")
model = grid_search.best_estimator_  # O melhor modelo já treinado


# Predições
y_pred = model.predict(X_test_scaled)

# Relatório e matriz de confusão
report = classification_report(y_test, y_pred, output_dict=True)
print("\nRelatório de Classificação:")
print(classification_report(y_test, y_pred))
cm = confusion_matrix(y_test, y_pred)

# Gráfico da matriz de confusão
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Normal (0)', 'Falha (1)'],
            yticklabels=['Normal (0)', 'Falha (1)'])
plt.title("Matriz de Confusão - Modelo Aperfeiçoado", fontsize=16)
plt.ylabel('Classe Real', fontsize=12)
plt.xlabel('Classe Predita', fontsize=12)
plt.tight_layout()

# Salvar dentro da mesma pasta onde o script está
img_path = os.path.join(os.path.dirname(__file__), "confusion_matrix.png")
plt.savefig(img_path)
plt.close()

print(f"Matriz de confusão atualizada e salva em: {img_path}")

# --- Análise de Importância das Features ---
print("Calculando e salvando a importância das features...")
importances = model.feature_importances_
feature_names = X.columns
feature_importance_df = pd.DataFrame(
    {'Feature': feature_names, 'Importance': importances})
feature_importance_df = feature_importance_df.sort_values(
    by='Importance', ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x='Importance', y='Feature',
            data=feature_importance_df, palette='viridis')
plt.title('Importância de Cada Feature para o Modelo', fontsize=16)
plt.xlabel('Importância', fontsize=12)
plt.ylabel('Feature (Sensor/Variável)', fontsize=12)
plt.tight_layout()
img_path_features = os.path.join(
    os.path.dirname(__file__), "feature_importance.png")
plt.savefig(img_path_features)
plt.close()

print(f"Gráfico de importância das features salvo em: {img_path_features}")

# --- Salvar o Modelo e o Scaler ---
print("Salvando o modelo otimizado e o scaler...")
artifacts_path = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(artifacts_path, exist_ok=True)  # Cria a pasta se não existir

joblib.dump(model, os.path.join(artifacts_path, "preventai_model.joblib"))
joblib.dump(scaler, os.path.join(artifacts_path, "preventai_scaler.joblib"))

print(f"Artefatos salvos na pasta: {artifacts_path}")
