import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import os
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

# Features e target
X = df[["Air temperature [K]", "Process temperature [K]",
        "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]]
y = df["Target"]

# Divisão treino/teste
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# Escalonamento
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Modelo simples - Random Forest
model = RandomForestClassifier(random_state=42, n_estimators=100)
model.fit(X_train_scaled, y_train)

# Predições
y_pred = model.predict(X_test_scaled)

# Relatório e matriz de confusão
report = classification_report(y_test, y_pred, output_dict=True)
cm = confusion_matrix(y_test, y_pred)

# Gráfico da matriz de confusão
plt.figure(figsize=(6, 5))
plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
plt.title("Matriz de Confusão - Classificação de Falha")
plt.colorbar()
classes = ["Normal (0)", "Falha (1)"]
tick_marks = range(len(classes))
plt.xticks(tick_marks, classes, rotation=45)
plt.yticks(tick_marks, classes)

# Anotação dos valores na matriz
thresh = cm.max() / 2.
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(j, i, format(cm[i, j], 'd'),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

plt.ylabel('Classe Real')
plt.xlabel('Classe Predita')
plt.tight_layout()

# Salvar dentro da mesma pasta onde o script está
img_path = os.path.join(os.path.dirname(__file__), "confusion_matrix.png")
plt.savefig(img_path)
plt.close()

report, cm, img_path
