-- =========================================================
-- STREAMING SQL PORTFOLIO — Consultas analíticas
-- Cada consulta explora um dos desequilíbrios propositais
-- que existem nos dados (ver seed_data.py)
-- =========================================================


-- ---------------------------------------------------------
-- 1) TOP 5 títulos mais assistidos
--    Mostra JOIN simples + GROUP BY + ORDER BY + LIMIT
-- ---------------------------------------------------------
SELECT
    t.titulo,
    t.genero,
    COUNT(*) AS total_visualizacoes
FROM fato_visualizacoes f
JOIN dim_titulos t ON f.titulo_id = t.id
GROUP BY t.id
ORDER BY total_visualizacoes DESC
LIMIT 5;


-- ---------------------------------------------------------
-- 2) Ranking de usuários por minutos assistidos, usando
--    window function RANK() — mostra os "power users"
-- ---------------------------------------------------------
SELECT
    u.nome,
    u.plano,
    SUM(f.minutos_assistidos) AS total_minutos,
    RANK() OVER (ORDER BY SUM(f.minutos_assistidos) DESC) AS posicao_ranking
FROM fato_visualizacoes f
JOIN dim_usuarios u ON f.usuario_id = u.id
GROUP BY u.id
ORDER BY posicao_ranking
LIMIT 10;


-- ---------------------------------------------------------
-- 3) Taxa de conclusão (%) por tipo de dispositivo
--    Mostra AVG com CAST/ROUND e agregação por dimensão
-- ---------------------------------------------------------
SELECT
    d.tipo_dispositivo,
    COUNT(*) AS total_visualizacoes,
    ROUND(100.0 * SUM(f.completou) / COUNT(*), 1) AS taxa_conclusao_pct
FROM fato_visualizacoes f
JOIN dim_dispositivos d ON f.dispositivo_id = d.id
GROUP BY d.tipo_dispositivo
ORDER BY taxa_conclusao_pct DESC;


-- ---------------------------------------------------------
-- 4) Evolução mensal de minutos assistidos
--    Mostra agregação por dimensão de tempo (mês/ano)
--    Confirma a tendência de crescimento simulada no seed
-- ---------------------------------------------------------
SELECT
    dt.ano,
    dt.mes,
    COUNT(*) AS visualizacoes,
    SUM(f.minutos_assistidos) AS total_minutos
FROM fato_visualizacoes f
JOIN dim_tempo dt ON f.tempo_id = dt.id
GROUP BY dt.ano, dt.mes
ORDER BY dt.ano, dt.mes;


-- ---------------------------------------------------------
-- 5) Gênero mais assistido, quebrado por plano de assinatura
--    Mostra GROUP BY composto (duas dimensões ao mesmo tempo)
-- ---------------------------------------------------------
SELECT
    u.plano,
    t.genero,
    COUNT(*) AS visualizacoes
FROM fato_visualizacoes f
JOIN dim_usuarios u ON f.usuario_id = u.id
JOIN dim_titulos t ON f.titulo_id = t.id
GROUP BY u.plano, t.genero
ORDER BY u.plano, visualizacoes DESC;


-- ---------------------------------------------------------
-- 6) Usuário mais ativo DENTRO de cada plano
--    Mostra window function PARTITION BY + ROW_NUMBER
-- ---------------------------------------------------------
SELECT plano, nome, total_minutos
FROM (
    SELECT
        u.plano,
        u.nome,
        SUM(f.minutos_assistidos) AS total_minutos,
        ROW_NUMBER() OVER (
            PARTITION BY u.plano
            ORDER BY SUM(f.minutos_assistidos) DESC
        ) AS posicao_no_plano
    FROM fato_visualizacoes f
    JOIN dim_usuarios u ON f.usuario_id = u.id
    GROUP BY u.id
)
WHERE posicao_no_plano = 1;


-- ---------------------------------------------------------
-- 7) Títulos mais bem avaliados (mínimo de 10 avaliações)
--    Mostra HAVING para filtrar depois do agrupamento
--    e como lidar com NULL (nem toda visualização tem nota)
-- ---------------------------------------------------------
SELECT
    t.titulo,
    COUNT(f.avaliacao) AS qtd_avaliacoes,
    ROUND(AVG(f.avaliacao), 2) AS nota_media
FROM fato_visualizacoes f
JOIN dim_titulos t ON f.titulo_id = t.id
WHERE f.avaliacao IS NOT NULL
GROUP BY t.id
HAVING COUNT(f.avaliacao) >= 10
ORDER BY nota_media DESC
LIMIT 5;


-- ---------------------------------------------------------
-- 8) Fim de semana vs dia de semana
--    Mostra CASE WHEN para recategorizar dados na consulta
-- ---------------------------------------------------------
SELECT
    CASE WHEN dt.fim_de_semana = 1 THEN 'Fim de semana' ELSE 'Dia de semana' END AS periodo,
    COUNT(*) AS visualizacoes,
    ROUND(AVG(f.minutos_assistidos), 1) AS media_minutos_por_sessao
FROM fato_visualizacoes f
JOIN dim_tempo dt ON f.tempo_id = dt.id
GROUP BY periodo;


-- ---------------------------------------------------------
-- 9) Usuários que assistem ACIMA da média geral
--    Mostra subquery (subconsulta) no WHERE
-- ---------------------------------------------------------
SELECT
    u.nome,
    SUM(f.minutos_assistidos) AS total_minutos
FROM fato_visualizacoes f
JOIN dim_usuarios u ON f.usuario_id = u.id
GROUP BY u.id
HAVING SUM(f.minutos_assistidos) > (
    SELECT AVG(soma_por_usuario)
    FROM (
        SELECT SUM(minutos_assistidos) AS soma_por_usuario
        FROM fato_visualizacoes
        GROUP BY usuario_id
    )
)
ORDER BY total_minutos DESC;


-- ---------------------------------------------------------
-- 10) Distribuição de visualizações por classificação etária
--     e tipo de conteúdo (filme vs série)
--     Mostra GROUP BY composto simples pra fechar com uma
--     visão geral do catálogo mais consumido
-- ---------------------------------------------------------
SELECT
    t.tipo,
    t.classificacao,
    COUNT(*) AS visualizacoes
FROM fato_visualizacoes f
JOIN dim_titulos t ON f.titulo_id = t.id
GROUP BY t.tipo, t.classificacao
ORDER BY t.tipo, visualizacoes DESC;