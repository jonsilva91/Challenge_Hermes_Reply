import psycopg2
import os
import time
import random
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# --- Configuração do Banco de Dados ---
DB_NAME = os.getenv("DB_NAME", "preventai_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def insert_simulated_reading():
    """Insere uma leitura simulada no banco de dados."""
    conn = None
    try:
        conn_string = (
            f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASS}' "
            f"host='{DB_HOST}' port='{DB_PORT}' sslmode='require'"
        )
        conn = psycopg2.connect(conn_string)

        cur = conn.cursor()

        # Simula leitura de um sensor de temperatura (ID 1)
        sensor_id = 1
        # Valor base com variação
        valor_medido = 300 + random.uniform(-5.0, 5.0)
        timestamp = datetime.now()

        query = "INSERT INTO LEITURA_SENSOR (cd_sensor, ts_leitura, vl_medido) VALUES (%s, %s, %s);"
        cur.execute(query, (sensor_id, timestamp, valor_medido))

        conn.commit()
        print(
            f"[{timestamp}] Leitura inserida: Sensor {sensor_id}, Valor {valor_medido:.2f}")

    except Exception as e:
        print(f"Erro ao inserir leitura: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Iniciando simulação de ingestão de dados... Pressione CTRL+C para parar.")
    while True:
        insert_simulated_reading()
        time.sleep(5)  # Insere uma nova leitura a cada 5 segundos
