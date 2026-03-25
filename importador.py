import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import logging
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def get_db_connection():
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
        logging.error(f"Erro ao conectar no banco PostgreSQL: {e}")
        return None

def setup_database():
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            logging.info("Criando tabelas relacionais no PostgreSQL...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS modelos_ia (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias_clinicas (
                    id SERIAL PRIMARY KEY,
                    nome_categoria VARCHAR(255) NOT NULL,
                    subcategoria VARCHAR(255) NOT NULL,
                    UNIQUE (nome_categoria, subcategoria)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs_ia (
                    id SERIAL PRIMARY KEY,
                    modelo_id INT NOT NULL REFERENCES modelos_ia(id) ON DELETE CASCADE,
                    categoria_id INT NOT NULL REFERENCES categorias_clinicas(id) ON DELETE CASCADE,
                    prompt TEXT,
                    resposta TEXT,
                    latencia FLOAT,
                    pontuacao FLOAT,
                    tokens INT,
                    custo FLOAT,
                    confianca FLOAT,
                    status VARCHAR(50),
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_teste TIMESTAMP,
                    UNIQUE (modelo_id, categoria_id, data_teste, prompt)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_artigos (
                    id SERIAL PRIMARY KEY,
                    termo_busca VARCHAR(255) UNIQUE NOT NULL,
                    resultados JSONB,
                    data_busca TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        logging.info("Tabelas provisionadas (Supabase/PostgreSQL).")
        return True
    except Exception as e:
        logging.error(f"Erro setup BD PostgreSQL: {e}")
        return False
    finally:
        conn.close()

def importar_dados():
    logging.info("Iniciando Pipeline ETL PostgreSQL...")
    try:
        df = pd.read_csv('Base_Dados_Saude_corrigido.csv', sep=';', encoding='utf-8-sig')
        df['Pontuação (0-10)'] = df['Pontuação (0-10)'].fillna(0.0)
        df['Resposta da IA'] = df['Resposta da IA'].fillna('Pendente')
        df['Tempo de Resposta (s)'] = df['Tempo de Resposta (s)'].fillna(0.0)
        
        conn = get_db_connection()
        if not conn: return
        
        custo_por_token = {
            'Claude 3.5': 3.0 / 1000000,
            'DeepSeek R1': 0.14 / 1000000,
            'Manus': 5.0 / 1000000,
            'Grok 2': 2.0 / 1000000,
            'Perplexity': 1.0 / 1000000,
            'Chat.Z.Ai': 0.5 / 1000000
        }
        
        inserted = 0
        with conn.cursor() as cursor:
            for _, row in df.iterrows():
                modelo_str = str(row['Nome da IA']).strip()
                if not modelo_str or pd.isna(row['Nome da IA']) or modelo_str == 'nan': continue
                
                cat_str = str(row['Categoria do Teste']).strip()
                subcat_str = str(row['Subcategoria']).strip()
                prompt_str = str(row['Prompt (Pergunta)'])
                res_str = str(row['Resposta da IA'])
                latencia = float(row['Tempo de Resposta (s)'])
                pontuacao = float(row['Pontuação (0-10)'])
                
                data_teste = None
                if pd.notna(row['Data do Teste']) and str(row['Data do Teste']).strip() not in ["", "nan"]:
                    try:
                        data_teste = pd.to_datetime(row['Data do Teste'], format='mixed').strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                
                cursor.execute(
                    "INSERT INTO modelos_ia (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING RETURNING id",
                    (modelo_str,)
                )
                res_m = cursor.fetchone()
                if not res_m:
                    cursor.execute("SELECT id FROM modelos_ia WHERE nome = %s", (modelo_str,))
                    res_m = cursor.fetchone()
                modelo_id = res_m[0]
                
                cursor.execute(
                    "INSERT INTO categorias_clinicas (nome_categoria, subcategoria) VALUES (%s, %s) ON CONFLICT (nome_categoria, subcategoria) DO NOTHING RETURNING id",
                    (cat_str, subcat_str)
                )
                res_c = cursor.fetchone()
                if not res_c:
                    cursor.execute("SELECT id FROM categorias_clinicas WHERE nome_categoria = %s AND subcategoria = %s", (cat_str, subcat_str))
                    res_c = cursor.fetchone()
                cat_id = res_c[0]
                
                tokens = math.ceil((len(prompt_str) + len(res_str)) / 4)
                custo_taxa = custo_por_token.get(modelo_str, 1.0 / 1000000)
                custo = tokens * custo_taxa
                confianca = pontuacao / 10.0
                status = 'sucesso' if latencia > 0 else 'pendente'
                
                sql = """
                    INSERT INTO logs_ia 
                    (modelo_id, categoria_id, prompt, resposta, latencia, pontuacao, tokens, custo, confianca, status, data_teste)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (modelo_id, categoria_id, data_teste, prompt) DO NOTHING
                """
                cursor.execute(sql, (modelo_id, cat_id, prompt_str, res_str, latencia, pontuacao, tokens, custo, confianca, status, data_teste))
                inserted += cursor.rowcount if cursor.rowcount > 0 else 0
                
        conn.commit()
        conn.close()
        logging.info(f"Importação concluída! Total de logs inseridos: {inserted}")
        
    except Exception as e:
        logging.error(f"Erro na importação: {e}")

if __name__ == "__main__":
    if setup_database():
        importar_dados()
