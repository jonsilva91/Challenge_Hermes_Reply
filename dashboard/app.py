import streamlit as st
import pandas as pd
import psycopg2
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


def get_db_connection():
    """Estabelece conexão com o banco de dados PostgreSQL."""
    # String de conexão completa, ideal para serviços em nuvem como o Neon
    conn_string = (
        f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASS}' "
        f"host='{DB_HOST}' port='{DB_PORT}' sslmode='require'"
    )
    conn = psycopg2.connect(conn_string)
    return conn


def fetch_data(query):
    """Executa uma query e retorna os dados como DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# --- Título e Visão Geral ---
st.set_page_config(page_title="PreventAI Dashboard", layout="wide")
st.title("📊 PreventAI - Dashboard de Manutenção Preditiva")
st.markdown("""
Este dashboard demonstra o fluxo integrado do projeto PreventAI: dados são coletados, armazenados no banco de dados,
processados por um modelo de Machine Learning e visualizados aqui para gerar insights e alertas.
""")

# --- KPIs Principais ---
st.header("📈 KPIs Operacionais em Tempo Real (Simulado)")

try:
    total_leituras = fetch_data(
        "SELECT COUNT(*) FROM LEITURA_SENSOR;").iloc[0, 0]
    num_sensores = fetch_data("SELECT COUNT(*) FROM SENSOR;").iloc[0, 0]
    avg_temp_query = """
    SELECT AVG(ls.vl_medido) 
    FROM LEITURA_SENSOR ls
    JOIN SENSOR s ON ls.cd_sensor = s.cd_sensor
    JOIN TIPO_SENSOR ts ON s.cd_tipo_sensor = ts.cd_tipo_sensor
    WHERE ts.ds_tipo = 'Air temperature';
    """
    avg_temp = fetch_data(avg_temp_query).iloc[0, 0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Nº de Sensores Ativos", f"{num_sensores}")
    col2.metric("Total de Leituras Coletadas", f"{total_leituras}")
    col3.metric("Temperatura Média do Ar (K)", f"{avg_temp:.2f}")

    # --- Alerta Mínimo ---
    st.header("🚨 Sistema de Alertas")
    TEMP_THRESHOLD = 305.0  # Limite em Kelvin
    if avg_temp > TEMP_THRESHOLD:
        st.error(
            f"**ALERTA DE TEMPERATURA!** A média ({avg_temp:.2f} K) ultrapassou o limite de {TEMP_THRESHOLD} K.", icon="🔥")
    else:
        st.success(
            f"Condições normais. A temperatura média ({avg_temp:.2f} K) está dentro do limite.", icon="✅")

    # --- Visualização de Dados ---
    st.header("🔍 Análise de Dados dos Sensores")
    leituras_df = fetch_data(
        "SELECT ts_leitura, vl_medido FROM LEITURA_SENSOR ORDER BY ts_leitura DESC LIMIT 100;")
    st.line_chart(leituras_df.rename(
        columns={'ts_leitura': 'index'}).set_index('index'))

    # --- Resultados do Modelo de ML ---
    st.header("🤖 Resultados do Machine Learning")
    st.markdown("""
    Um modelo de **Machine Learning** (`RandomForestClassifier`) foi treinado para analisar os dados dos sensores e prever possíveis falhas na máquina.
    A matriz abaixo mostra o desempenho do modelo em dados de teste:""")

    # Exibe a matriz de confusão gerada pelo script de ML
    col1_ml, col2_ml = st.columns(2)
    with col1_ml:
        if os.path.exists("ml/confusion_matrix.png"):
            st.image("ml/confusion_matrix.png",
                     caption="Matriz de Confusão do Modelo Otimizado")
        else:
            st.warning(
                "Matriz de confusão não encontrada. Execute o pipeline de ML.")

    with col2_ml:
        if os.path.exists("ml/feature_importance.png"):
            st.image("ml/feature_importance.png",
                     caption="Importância das Features")
        else:
            st.warning(
                "Gráfico de importância não encontrado. Execute o pipeline de ML.")

except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados ou buscar dados: {e}")
    st.info("Certifique-se de que o banco de dados está rodando e os dados foram carregados com 'python db/load_data.py'.")
