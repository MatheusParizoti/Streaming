-- =========================================================
-- STREAMING SQL PORTFOLIO
-- Esquema em formato ESTRELA (star schema)
-- 1 tabela FATO (fato_visualizacoes) + 4 tabelas DIMENSÃO
-- =========================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------
-- DIMENSÃO: usuários
-- ---------------------------------------------------------
DROP TABLE IF EXISTS dim_usuarios;
CREATE TABLE dim_usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    idade           INTEGER NOT NULL CHECK (idade >= 0),
    pais            TEXT NOT NULL,
    plano           TEXT NOT NULL CHECK (plano IN ('free', 'basico', 'premium')),
    data_cadastro   TEXT NOT NULL  -- formato YYYY-MM-DD
);

-- ---------------------------------------------------------
-- DIMENSÃO: títulos (filmes e séries)
-- ---------------------------------------------------------
DROP TABLE IF EXISTS dim_titulos;
CREATE TABLE dim_titulos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo              TEXT NOT NULL,
    tipo                TEXT NOT NULL CHECK (tipo IN ('filme', 'serie')),
    genero              TEXT NOT NULL,
    ano_lancamento      INTEGER NOT NULL,
    duracao_min         INTEGER NOT NULL CHECK (duracao_min > 0),
    classificacao       TEXT NOT NULL CHECK (classificacao IN ('L', '10', '12', '14', '16', '18'))
);

-- ---------------------------------------------------------
-- DIMENSÃO: dispositivos
-- ---------------------------------------------------------
DROP TABLE IF EXISTS dim_dispositivos;
CREATE TABLE dim_dispositivos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_dispositivo    TEXT NOT NULL,   -- Smart TV, Celular, Notebook, Tablet, Console
    sistema_operacional TEXT NOT NULL
);

-- ---------------------------------------------------------
-- DIMENSÃO: tempo
-- ---------------------------------------------------------
DROP TABLE IF EXISTS dim_tempo;
CREATE TABLE dim_tempo (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    data            TEXT NOT NULL UNIQUE,  -- YYYY-MM-DD
    dia_semana      TEXT NOT NULL,
    mes             INTEGER NOT NULL,
    ano             INTEGER NOT NULL,
    trimestre       INTEGER NOT NULL,
    fim_de_semana   INTEGER NOT NULL CHECK (fim_de_semana IN (0, 1))
);

-- ---------------------------------------------------------
-- FATO: visualizações
-- Cada linha = um evento de "usuário assistiu um título"
-- ---------------------------------------------------------
DROP TABLE IF EXISTS fato_visualizacoes;
CREATE TABLE fato_visualizacoes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id          INTEGER NOT NULL,
    titulo_id           INTEGER NOT NULL,
    dispositivo_id      INTEGER NOT NULL,
    tempo_id            INTEGER NOT NULL,
    minutos_assistidos  INTEGER NOT NULL CHECK (minutos_assistidos >= 0),
    completou           INTEGER NOT NULL CHECK (completou IN (0, 1)),
    avaliacao           INTEGER CHECK (avaliacao BETWEEN 1 AND 5),  -- pode ser NULL (usuário nem sempre avalia)

    FOREIGN KEY (usuario_id)     REFERENCES dim_usuarios(id),
    FOREIGN KEY (titulo_id)      REFERENCES dim_titulos(id),
    FOREIGN KEY (dispositivo_id) REFERENCES dim_dispositivos(id),
    FOREIGN KEY (tempo_id)       REFERENCES dim_tempo(id)
);

-- Índices para acelerar joins/consultas analíticas na tabela fato
CREATE INDEX idx_fato_usuario     ON fato_visualizacoes(usuario_id);
CREATE INDEX idx_fato_titulo      ON fato_visualizacoes(titulo_id);
CREATE INDEX idx_fato_dispositivo ON fato_visualizacoes(dispositivo_id);
CREATE INDEX idx_fato_tempo       ON fato_visualizacoes(tempo_id);