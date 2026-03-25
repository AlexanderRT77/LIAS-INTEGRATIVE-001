import psycopg2
import os
from dotenv import load_dotenv
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
load_dotenv()

def get_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=5
        )
    except Exception as e:
        logging.error(f"Erro de conexão com o Postgres no updater: {e}")
        return None

def criar_tabela(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS benchmarks_mercado (
                    id SERIAL PRIMARY KEY,
                    modelo_ia TEXT UNIQUE NOT NULL,
                    elo_intelligence INTEGER,
                    tokens_por_segundo REAL,
                    preco_1m_input REAL,
                    preco_1m_output REAL,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
    except Exception as e:
        logging.error(f"Erro na criação da tabela: {e}")

def atualizar_banco():
    # Dados mock baseados no mercado atual de Inteligência Artificial
    mock_data = [
        ("Claude 3.5 Sonnet", 1280, 75.5, 3.00, 15.00),
        ("DeepSeek R1", 1250, 95.0, 0.14, 0.28),
        ("Manus", 1150, 40.0, 5.00, 15.00),
        ("Grok 2", 1220, 85.0, 2.00, 10.00),
        ("Perplexity", 1180, 110.0, 1.00, 1.00),
        ("Chat.Z.Ai", 1090, 150.0, 0.50, 0.50)
    ]
    
    conn = get_connection()
    if not conn: return
    try:
        criar_tabela(conn)
        with conn.cursor() as cur:
            for d in mock_data:
                # Simulação natural para o updater ao longo do tempo
                variacao_elo = d[1] + random.randint(-5, 5)
                variacao_tps = d[2] + random.uniform(-2, 5)
                
                sql = """
                    INSERT INTO benchmarks_mercado 
                    (modelo_ia, elo_intelligence, tokens_por_segundo, preco_1m_input, preco_1m_output, data_atualizacao)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (modelo_ia) DO UPDATE SET 
                        elo_intelligence = EXCLUDED.elo_intelligence,
                        tokens_por_segundo = EXCLUDED.tokens_por_segundo,
                        preco_1m_input = EXCLUDED.preco_1m_input,
                        preco_1m_output = EXCLUDED.preco_1m_output,
                        data_atualizacao = EXCLUDED.data_atualizacao;
                """
                cur.execute(sql, (d[0], variacao_elo, round(variacao_tps, 2), d[3], d[4]))
        conn.commit()
        logging.info("Tabela de benchmarks populada com dados Artificiais de Mercado (Supabase)!")
    except Exception as e:
        logging.error(f"Erro ao inserir dados no banco: {e}")
    finally: conn.close()

if __name__ == "__main__":
    logging.info("Iniciando rotina de extracao ArtificialAnalysis (Mock Updater)...")
    atualizar_banco()
