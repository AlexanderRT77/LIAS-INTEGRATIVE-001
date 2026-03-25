-- Tabela de Benchmarks de Mercado (ArtificialAnalysis / L.I.A.S Admin)
CREATE TABLE IF NOT EXISTS benchmarks_mercado (
    id SERIAL PRIMARY KEY,
    modelo_ia TEXT UNIQUE NOT NULL,
    elo_intelligence INTEGER,
    tokens_por_segundo REAL,
    preco_1m_input REAL,
    preco_1m_output REAL,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Carga Inicial das 6 IAs Monitoradas
INSERT INTO benchmarks_mercado (modelo_ia, elo_intelligence, tokens_por_segundo, preco_1m_input, preco_1m_output)
VALUES 
('Claude 3.5 Sonnet', 1280, 75.5, 3.00, 15.00),
('DeepSeek R1', 1250, 95.0, 0.14, 0.28),
('Perplexity', 1180, 110.0, 1.00, 1.00),
('Chat.Z.Ai', 1090, 150.0, 0.50, 0.50),
('Grok 2', 1220, 85.0, 2.00, 10.00),
('Manus', 1150, 40.0, 5.00, 15.00)
ON CONFLICT (modelo_ia) DO NOTHING;
