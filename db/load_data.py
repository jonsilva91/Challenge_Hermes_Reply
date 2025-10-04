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
        conn_string = (
            f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASS}' "
            f"host='{DB_HOST}' port='{DB_PORT}' sslmode='require'"
        )
        conn = psycopg2.connect(conn_string)

        cur = conn.cursor()

        print("Limpando tabelas existentes...")
        cur.execute(
            "TRUNCATE TABLE LEITURA_SENSOR, SENSOR, TIPO_SENSOR, MAQUINA, LINHA_PRODUCAO, SITE RESTART IDENTITY CASCADE;")

        # --- Inserir Dados Estruturais (Site, Linha, Máquina) ---
        print("Inserindo dados estruturais (Site, Linha, Máquina)...")
        # 1. Site
        cur.execute(
            "INSERT INTO SITE (cd_site, nm_site, sg_pais, nm_cidade) VALUES (%s, %s, %s, %s)",
            (1, 'Planta Sorocaba', 'BR', 'Sorocaba'))
        # 2. Linha de Produção
        cur.execute(
            "INSERT INTO LINHA_PRODUCAO (cd_linha, nm_linha, cd_site) VALUES (%s, %s, %s)",
            (1, 'Linha de Montagem A', 1))
        # 3. Máquina
        cur.execute("INSERT INTO MAQUINA (cd_maquina, nm_maquina, tp_maquina, cd_linha) VALUES (%s, %s, %s, %s)",
                    (1, 'Prensa Hidráulica 01', 'Prensa', 1))

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
        # Ajuste de caminho relativo para funcionar a partir da pasta /db
        csv_path = os.path.join(os.path.dirname(
            __file__), '..', 'ml', 'predictive_maintenance.csv')
        df = pd.read_csv(csv_path)

        # Mapear nomes de colunas para IDs de sensor
        col_to_sensor_id = {
            "Air temperature [K]": 1, "Process temperature [K]": 2,
            "Rotational speed [rpm]": 3, "Torque [Nm]": 4, "Tool wear [min]": 5
        }

        # Otimização: Usar pd.melt para transformar os dados de wide para long format
        # É ordens de magnitude mais rápido que iterar com df.iterrows()
        print("Transformando dados para formato de inserção (long format)...")
        df_long = df[list(col_to_sensor_id.keys())].melt(
            var_name='coluna', value_name='vl_medido')
        df_long['cd_sensor'] = df_long['coluna'].map(col_to_sensor_id)
        df_long['ts_leitura'] = datetime.now()  # Timestamp único para o batch

        # Converte o DataFrame para uma lista de tuplas para o execute_values
        leituras = list(df_long[['cd_sensor', 'ts_leitura', 'vl_medido']].itertuples(
            index=False, name=None))

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
