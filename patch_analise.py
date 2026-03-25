import codecs
import re

with codecs.open("analise_clinica.py", "r", encoding="utf-8") as f:
    text = f.read()

# Make the modifications for normalized tables
text = text.replace(
    'FROM logs_ia\n        GROUP BY modelo',
    'FROM logs_ia l JOIN modelos_ia m ON l.modelo_id = m.id\n        GROUP BY m.nome'
)
text = text.replace(
    'SELECT \n            modelo,',
    'SELECT \n            m.nome as modelo,'
)
text = text.replace(
    'SELECT \n            categoria,\n            subcategoria,',
    'SELECT \n            c.nome_categoria as categoria,\n            c.subcategoria,'
)
text = text.replace(
    'FROM logs_ia\n        GROUP BY categoria, subcategoria',
    'FROM logs_ia l JOIN categorias_clinicas c ON l.categoria_id = c.id\n        GROUP BY c.nome_categoria, c.subcategoria'
)
text = text.replace(
    'SELECT * FROM logs_ia \n            WHERE categoria LIKE %s OR subcategoria LIKE %s',
    'SELECT l.*, m.nome as modelo, c.nome_categoria as categoria, c.subcategoria FROM logs_ia l JOIN modelos_ia m ON l.modelo_id=m.id JOIN categorias_clinicas c ON l.categoria_id=c.id \n            WHERE c.nome_categoria LIKE %s OR c.subcategoria LIKE %s'
)
text = text.replace(
    'SELECT categoria, subcategoria, COUNT(*) as total\n            FROM logs_ia \n            GROUP BY categoria, subcategoria',
    'SELECT c.nome_categoria as categoria, c.subcategoria, COUNT(*) as total\n            FROM logs_ia l JOIN categorias_clinicas c ON l.categoria_id = c.id \n            GROUP BY c.nome_categoria, c.subcategoria'
)
text = text.replace(
    'FROM logs_ia\n        WHERE data_teste IS NOT NULL\n        GROUP BY periodo',
    'FROM logs_ia l\n        WHERE l.data_teste IS NOT NULL\n        GROUP BY periodo'
)
text = text.replace(
    'SELECT \n            DATE(data_teste) as data,\n            modelo,',
    'SELECT \n            DATE(l.data_teste) as data,\n            m.nome as modelo,'
)
text = text.replace(
    'FROM logs_ia\n        WHERE data_teste >=',
    'FROM logs_ia l JOIN modelos_ia m ON l.modelo_id = m.id\n        WHERE l.data_teste >='
)
text = text.replace(
    'GROUP BY DATE(data_teste), modelo',
    'GROUP BY DATE(l.data_teste), m.nome'
)
text = text.replace(
    'SELECT \n            id, data_teste, modelo, categoria, subcategoria,',
    'SELECT \n            l.id, l.data_teste, m.nome as modelo, c.nome_categoria as categoria, c.subcategoria,'
)
text = text.replace(
    'FROM logs_ia\n        WHERE {where}',
    'FROM logs_ia l JOIN modelos_ia m ON l.modelo_id = m.id JOIN categorias_clinicas c ON l.categoria_id = c.id\n        WHERE {where}'
)
text = text.replace('COUNT(DISTINCT categoria)', 'COUNT(DISTINCT c.nome_categoria)')
text = text.replace('GROUP_CONCAT(DISTINCT modelo)', 'GROUP_CONCAT(DISTINCT m.nome)')

text = text.replace('condicoes.append("modelo = %s")', 'condicoes.append("m.nome = %s")')
text = text.replace('condicoes.append("categoria = %s")', 'condicoes.append("c.nome_categoria = %s")')
text = text.replace('condicoes.append("subcategoria = %s")', 'condicoes.append("c.subcategoria = %s")')
text = text.replace('(prompt LIKE %s OR resposta LIKE %s)', '(l.prompt LIKE %s OR l.resposta LIKE %s)')

text = text.replace('SELECT COUNT(*) FROM logs_ia', 'SELECT COUNT(*) FROM logs_ia l')
text = text.replace('COUNT(DISTINCT modelo) FROM logs_ia', 'COUNT(DISTINCT modelo_id) FROM logs_ia')
text = text.replace('COUNT(DISTINCT categoria) FROM logs_ia', 'COUNT(DISTINCT categoria_id) FROM logs_ia')
text = text.replace('SELECT AVG(pontuacao) FROM logs_ia', 'SELECT AVG(pontuacao) FROM logs_ia l')
text = text.replace('SELECT SUM(custo) FROM logs_ia', 'SELECT SUM(custo) FROM logs_ia l')
text = text.replace('SELECT modelo, AVG(pontuacao) as media', 'SELECT m.nome as modelo, AVG(l.pontuacao) as media')
text = text.replace('FROM logs_ia \n            GROUP BY modelo', 'FROM logs_ia l JOIN modelos_ia m ON l.modelo_id = m.id \n            GROUP BY m.nome')
text = text.replace('SELECT categoria, COUNT(*) as total', 'SELECT c.nome_categoria as categoria, COUNT(*) as total')
text = text.replace('FROM logs_ia \n            GROUP BY categoria', 'FROM logs_ia l JOIN categorias_clinicas c ON l.categoria_id = c.id \n            GROUP BY c.nome_categoria')

# Adicionar import streamlit
if "import streamlit as st" not in text:
    text = text.replace("import pandas as pd", "import pandas as pd\nimport streamlit as st")

with codecs.open("analise_clinica_patched.py", "w", encoding="utf-8") as f:
    f.write(text)
print("analise_clinica_patched.py created!")
