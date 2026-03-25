import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import logging

load_dotenv()

def get_connection():
    try:
        # Tenta conexão com Postgres/Supabase
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            connect_timeout=3
        )
        return conn
    except Exception as e:
        logging.error(f"Erro de conexão Supabase: {e}")
        return None

def obter_logs_clinicos():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            query = """
                SELECT 
                    m.nome as modelo_ia, 
                    l.pontuacao as acuracia, 
                    l.latencia as tempo,
                    l.data_teste
                FROM logs_ia l
                JOIN modelos_ia m ON l.modelo_id = m.id
                ORDER BY l.data_teste DESC
                LIMIT 100
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            logging.error(f"Erro query logs: {e}")
        finally:
            conn.close()
    return []