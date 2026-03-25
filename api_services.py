import os
import io
import json
import logging
import requests
import pandas as pd
import pypdf as PyPDF2
import psycopg2
import psycopg2.extras
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import analise_clinica

def fetch_pubmed(termo, max_results=5):
    """ Busca na API do PubMed com Cache no Supabase (PostgreSQL) """
    conn = analise_clinica.get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT resultados FROM cache_artigos WHERE termo_busca = %s", (termo,))
            row = cursor.fetchone()
            if row:
                res = row['resultados']
                return json.loads(res) if isinstance(res, str) else res
        except Exception as e:
            logging.error(f"Erro cache PubMed: {e}")
        finally:
            conn.close()

    # Fallback NCBI Real Fetch
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": termo, "retmode": "json", "retmax": max_results}
    resultados = []
    
    try:
        r = requests.get(base_url, params=params, timeout=10)
        id_list = r.json().get("esearchresult", {}).get("idlist", [])
        
        if id_list:
            summ_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            summ_params = {"db": "pubmed", "id": ",".join(id_list), "retmode": "json"}
            r_summ = requests.get(summ_url, params=summ_params, timeout=10)
            summ_data = r_summ.json()
            
            for uid in id_list:
                info = summ_data.get("result", {}).get(uid, {})
                resultados.append({
                    "id": uid,
                    "title": info.get("title", f"Artigo {uid}"),
                    "source": info.get("source", "PubMed Central"),
                    "pubdate": info.get("pubdate", "Recente")
                })
        
        # Gravar Cache no Supabase
        if resultados:
            conn = analise_clinica.get_connection()
            if conn:
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO cache_artigos (termo_busca, resultados) VALUES (%s, %s) ON CONFLICT (termo_busca) DO UPDATE SET resultados = EXCLUDED.resultados", (termo, json.dumps(resultados)))
                    conn.commit()
                except Exception as e: logging.error(f"Cache save erro: {e}")
                finally: conn.close()
                    
    except Exception as e:
        logging.error(f"Erro Fetch NCBI: {e}")

    return resultados

def extract_pdf_text(file_obj):
    try:
        reader = PyPDF2.PdfReader(file_obj)
        text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text[:1000] + "..." if len(text) > 1000 else text
    except Exception as e:
        return f"Erro extração: {e}"

def generate_pdf_report(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Relatório Premium LIAS - Performance de IA")
    
    c.setFont("Helvetica", 10)
    y = height - 80
    
    if df is not None and not df.empty:
        for i, row in df.iterrows():
            if y < 50:
                c.showPage()
                y = height - 50
            texto = f"Modelo: {row.get('modelo_ia', 'N/A')} | Acurácia: {row.get('acuracia', '0.0')} | Tempo: {row.get('tempo', '0')}s"
            c.drawString(50, y, texto)
            y -= 20
    else:
        c.drawString(50, y, "Sem dados para o relatório.")

    c.save()
    buffer.seek(0)
    return buffer
