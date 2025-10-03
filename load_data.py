import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente de um arquivo .env
load_dotenv()

# --- Configuração do Banco de Dados ---
DB_NAME = os.getenv("DB_NAME", "preventai_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def setup_database():
    """Cria tabelas e carrega dados iniciais."""
    conn = None
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()

        print("Limpando tabelas existentes...")
        cur.execute(
            "TRUNCATE TABLE LEITURA_SENSOR, SENSOR, TIPO_SENSOR RESTART IDENTITY CASCADE;")

        # --- Inserir Tipos de Sensores ---
        print("Inserindo tipos de sensores...")
        tipos_sensores = [
            (1, 'Air temperature', 'K'),
            (2, 'Process temperature', 'K'),
            (3, 'Rotational speed', 'rpm'),
            (4, 'Torque', 'Nm'),
            (5, 'Tool wear', 'min')
        ]
        execute_values(
            cur, "INSERT INTO TIPO_SENSOR (cd_tipo_sensor, ds_tipo, unidade) VALUES %s", tipos_sensores)

        # --- Inserir Sensores (um para cada tipo) ---
        print("Inserindo sensores...")
        sensores = [(i, f'Sensor_{tipos[1]}', tipos[2], tipos[0], 1)
                    for i, tipos in enumerate(tipos_sensores, 1)]
        execute_values(
            cur, "INSERT INTO SENSOR (cd_sensor, tp_sensor, unidade, cd_tipo_sensor, cd_maquina) VALUES %s", sensores)

        # --- Carregar e Inserir Leituras ---
        print("Carregando dados do CSV para o banco...")
        df = pd.read_csv("ml/predictive_maintenance.csv")

        # Mapear nomes de colunas para IDs de sensor
        col_to_sensor_id = {
            "Air temperature [K]": 1, "Process temperature [K]": 2,
            "Rotational speed [rpm]": 3, "Torque [Nm]": 4, "Tool wear [min]": 5
        }

        leituras = []
        for _, row in df.iterrows():
            for col, sensor_id in col_to_sensor_id.items():
                leituras.append((sensor_id, datetime.now(), row[col]))

        execute_values(
            cur, "INSERT INTO LEITURA_SENSOR (cd_sensor, ts_leitura, vl_medido) VALUES %s", leituras)

        conn.commit()
        print(f"{len(leituras)} leituras inseridas com sucesso!")

    except Exception as e:
        print(f"Erro durante o setup do banco de dados: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    setup_database()
