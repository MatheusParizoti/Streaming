"""
gerar_dashboard.py
Lê o streaming.db e gera dashboard.html: um painel visual único (KPIs +
gráficos, via Chart.js) com os principais indicadores do banco. Não
depende de servidor — abre direto no navegador.
"""

import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "streaming.db"
SAIDA_PATH = BASE_DIR / "dashboard.html"


def buscar_dados(conn):
    dados = {}

    # KPIs gerais
    total_views, total_minutos, taxa_conclusao = conn.execute("""
        SELECT COUNT(*), SUM(minutos_assistidos), ROUND(100.0*SUM(completou)/COUNT(*), 1)
        FROM fato_visualizacoes
    """).fetchone()
    dados["kpi_total_views"] = total_views
    dados["kpi_total_horas"] = round(total_minutos / 60)
    dados["kpi_taxa_conclusao"] = taxa_conclusao

    titulo_top, views_top = conn.execute("""
        SELECT t.titulo, COUNT(*) FROM fato_visualizacoes f
        JOIN dim_titulos t ON f.titulo_id = t.id
        GROUP BY t.id ORDER BY 2 DESC LIMIT 1
    """).fetchone()
    dados["kpi_titulo_top"] = titulo_top
    dados["kpi_titulo_top_views"] = views_top

    usuario_top, minutos_top = conn.execute("""
        SELECT u.nome, SUM(f.minutos_assistidos) FROM fato_visualizacoes f
        JOIN dim_usuarios u ON f.usuario_id = u.id
        GROUP BY u.id ORDER BY 2 DESC LIMIT 1
    """).fetchone()
    dados["kpi_usuario_top"] = usuario_top
    dados["kpi_usuario_top_horas"] = round(minutos_top / 60, 1)

    # Top 8 titulos mais assistidos
    rows = conn.execute("""
        SELECT t.titulo, COUNT(*) as views FROM fato_visualizacoes f
        JOIN dim_titulos t ON f.titulo_id = t.id
        GROUP BY t.id ORDER BY views DESC LIMIT 8
    """).fetchall()
    dados["top_titulos_labels"] = [r[0] for r in rows]
    dados["top_titulos_valores"] = [r[1] for r in rows]

    # Evolucao mensal
    rows = conn.execute("""
        SELECT dt.ano || '-' || printf('%02d', dt.mes) as periodo, SUM(f.minutos_assistidos)
        FROM fato_visualizacoes f JOIN dim_tempo dt ON f.tempo_id = dt.id
        GROUP BY periodo ORDER BY periodo
    """).fetchall()
    dados["evolucao_labels"] = [r[0] for r in rows]
    dados["evolucao_valores"] = [r[1] for r in rows]

    # Dispositivos
    rows = conn.execute("""
        SELECT d.tipo_dispositivo, COUNT(*) FROM fato_visualizacoes f
        JOIN dim_dispositivos d ON f.dispositivo_id = d.id
        GROUP BY d.tipo_dispositivo ORDER BY 2 DESC
    """).fetchall()
    dados["dispositivos_labels"] = [r[0] for r in rows]
    dados["dispositivos_valores"] = [r[1] for r in rows]

    # Taxa de conclusao por dispositivo
    rows = conn.execute("""
        SELECT d.tipo_dispositivo, ROUND(100.0*SUM(f.completou)/COUNT(*), 1)
        FROM fato_visualizacoes f JOIN dim_dispositivos d ON f.dispositivo_id = d.id
        GROUP BY d.tipo_dispositivo ORDER BY 2 DESC
    """).fetchall()
    dados["conclusao_disp_labels"] = [r[0] for r in rows]
    dados["conclusao_disp_valores"] = [r[1] for r in rows]

    # Visualizacoes por genero
    rows = conn.execute("""
        SELECT t.genero, COUNT(*) FROM fato_visualizacoes f
        JOIN dim_titulos t ON f.titulo_id = t.id
        GROUP BY t.genero ORDER BY 2 DESC
    """).fetchall()
    dados["genero_labels"] = [r[0] for r in rows]
    dados["genero_valores"] = [r[1] for r in rows]

    # Fim de semana vs dia de semana
    rows = conn.execute("""
        SELECT CASE WHEN dt.fim_de_semana=1 THEN 'Fim de semana' ELSE 'Dia de semana' END, COUNT(*)
        FROM fato_visualizacoes f JOIN dim_tempo dt ON f.tempo_id = dt.id
        GROUP BY 1
    """).fetchall()
    dados["semana_labels"] = [r[0] for r in rows]
    dados["semana_valores"] = [r[1] for r in rows]

    # Top 5 titulos mais bem avaliados (min 10 avaliacoes)
    rows = conn.execute("""
        SELECT t.titulo, t.genero, COUNT(f.avaliacao), ROUND(AVG(f.avaliacao), 2)
        FROM fato_visualizacoes f JOIN dim_titulos t ON f.titulo_id = t.id
        WHERE f.avaliacao IS NOT NULL
        GROUP BY t.id HAVING COUNT(f.avaliacao) >= 10
        ORDER BY 4 DESC LIMIT 5
    """).fetchall()
    dados["top_avaliados"] = rows

    return dados


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Painel — Streaming SQL Portfolio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root {{
    --bg: #0b0c12;
    --panel: #14161f;
    --panel-border: #23263340;
    --violet: #8b7cff;
    --amber: #ffb648;
    --teal: #35d6b8;
    --text: #eceef4;
    --muted: #8890a4;
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    background: var(--bg);
    background-image: radial-gradient(circle at 15% 0%, #1c1740 0%, transparent 45%),
                       radial-gradient(circle at 85% 100%, #142621 0%, transparent 40%);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    padding: 48px 24px 80px;
}}
.wrap {{ max-width: 1180px; margin: 0 auto; }}

header {{ margin-bottom: 40px; }}
.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--teal);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 10px;
}}
h1 {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0 0 6px;
}}
.subtitulo {{ color: var(--muted); font-size: 0.95rem; }}

/* --- KPI "ticket stubs" --- */
.kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-bottom: 44px;
}}
.ticket {{
    position: relative;
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 14px;
    padding: 22px 20px 20px;
    overflow: hidden;
}}
.ticket::after {{
    content: "";
    position: absolute;
    left: 0; right: 0; bottom: 46px;
    border-bottom: 1.5px dashed #33374a;
}}
.ticket::before {{
    content: "";
    position: absolute;
    left: -8px; bottom: 40px;
    width: 16px; height: 16px;
    background: var(--bg);
    border-radius: 50%;
    box-shadow: 1180px 0 0 -1164px var(--bg);
}}
.ticket .valor {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--violet);
    line-height: 1.1;
}}
.ticket .rotulo {{
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 4px;
}}
.ticket .footer {{
    margin-top: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #6b7284;
}}
.ticket.amber .valor {{ color: var(--amber); }}
.ticket.teal .valor {{ color: var(--teal); }}

/* --- Grid de graficos --- */
.grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
}}
.card {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 14px;
    padding: 18px 16px;
}}
.card h2 {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 2px;
}}
.card .desc {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted);
    margin-bottom: 16px;
}}
.card.full {{ grid-column: 1 / -1; }}
.chart-box {{ position: relative; height: 280px; }}
.chart-box.alto {{ height: 340px; }}
canvas {{ max-width: 100%; }}

table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
th {{
    text-align: left;
    color: var(--muted);
    font-weight: 500;
    font-size: 0.78rem;
    padding: 8px 10px;
    border-bottom: 1px solid var(--panel-border);
}}
td {{ padding: 9px 10px; border-bottom: 1px solid #1c1f2b; }}
td.num {{ text-align: right; font-family: 'JetBrains Mono', monospace; color: var(--amber); }}

footer.rodape {{
    text-align: center;
    color: #4a5063;
    font-size: 0.78rem;
    margin-top: 48px;
    font-family: 'JetBrains Mono', monospace;
}}

@media (max-width: 860px) {{
    .kpis {{ grid-template-columns: repeat(2, 1fr); }}
    .grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="wrap">
    <header>
        <div class="eyebrow">Now analyzing</div>
        <h1>Painel de audiência — Streaming SQL Portfolio</h1>
        <div class="subtitulo">650 sessões de visualização · 20 usuários · 30 títulos · gerado a partir de streaming.db</div>
    </header>

    <section class="kpis">
        <div class="ticket">
            <div class="valor">{kpi_total_views}</div>
            <div class="rotulo">Visualizações registradas</div>
            <div class="footer">ADM · 001</div>
        </div>
        <div class="ticket amber">
            <div class="valor">{kpi_titulo_top_views}×</div>
            <div class="rotulo">"{kpi_titulo_top}" — título mais assistido</div>
            <div class="footer">HIT · 002</div>
        </div>
        <div class="ticket teal">
            <div class="valor">{kpi_taxa_conclusao}%</div>
            <div class="rotulo">Taxa média de conclusão</div>
            <div class="footer">ENG · 003</div>
        </div>
        <div class="ticket">
            <div class="valor">{kpi_usuario_top_horas}h</div>
            <div class="rotulo">{kpi_usuario_top} — usuário mais ativo</div>
            <div class="footer">TOP · 004</div>
        </div>
    </section>

    <section class="grid">
        <div class="card full">
            <h2>Top títulos mais assistidos</h2>
            <div class="desc">GROUP BY + ORDER BY + LIMIT</div>
            <div class="chart-box alto"><canvas id="chartTitulos"></canvas></div>
        </div>

        <div class="card full">
            <h2>Evolução mensal de audiência</h2>
            <div class="desc">SUM(minutos_assistidos) por mês</div>
            <div class="chart-box"><canvas id="chartEvolucao"></canvas></div>
        </div>

        <div class="card">
            <h2>Visualizações por dispositivo</h2>
            <div class="desc">Celular concentra a maior fatia</div>
            <div class="chart-box"><canvas id="chartDispositivos"></canvas></div>
        </div>

        <div class="card">
            <h2>Taxa de conclusão por dispositivo</h2>
            <div class="desc">% de sessões assistidas até o fim</div>
            <div class="chart-box"><canvas id="chartConclusao"></canvas></div>
        </div>

        <div class="card">
            <h2>Visualizações por gênero</h2>
            <div class="desc">Catálogo mais consumido</div>
            <div class="chart-box alto"><canvas id="chartGenero"></canvas></div>
        </div>

        <div class="card">
            <h2>Fim de semana vs dia de semana</h2>
            <div class="desc">Distribuição de sessões</div>
            <div class="chart-box"><canvas id="chartSemana"></canvas></div>
        </div>

        <div class="card full">
            <h2>Títulos mais bem avaliados</h2>
            <div class="desc">Mínimo de 10 avaliações · média de 1 a 5</div>
            <table>
                <thead><tr><th>Título</th><th>Gênero</th><th>Avaliações</th><th>Nota média</th></tr></thead>
                <tbody>
                    {linhas_avaliados}
                </tbody>
            </table>
        </div>
    </section>

    <footer class="rodape">Gerado automaticamente por gerar_dashboard.py a partir de streaming.db</footer>
</div>

<script>
Chart.defaults.color = "#8890a4";
Chart.defaults.font.family = "Inter";
Chart.defaults.borderColor = "#23263340";

const paletaViolet = "#8b7cff";
const paletaAmber = "#ffb648";
const paletaTeal = "#35d6b8";
const paletaMix = ["#8b7cff", "#35d6b8", "#ffb648", "#ff7c9c", "#5ea0ff", "#c98bff", "#6de3c0", "#ffcf7c"];

new Chart(document.getElementById('chartTitulos'), {{
    type: 'bar',
    data: {{
        labels: {top_titulos_labels},
        datasets: [{{ data: {top_titulos_valores}, backgroundColor: paletaViolet, borderRadius: 6 }}]
    }},
    options: {{
        indexAxis: 'y',
        maintainAspectRatio: false,
        layout: {{ padding: {{ right: 12 }} }},
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            x: {{ grid: {{ color: '#1c1f2b' }} }},
            y: {{
                grid: {{ display: false }},
                ticks: {{
                    callback: function(val) {{
                        const label = this.getLabelForValue(val);
                        return label.length > 22 ? label.slice(0, 21) + '…' : label;
                    }}
                }}
            }}
        }}
    }}
}});

new Chart(document.getElementById('chartEvolucao'), {{
    type: 'line',
    data: {{
        labels: {evolucao_labels},
        datasets: [{{
            data: {evolucao_valores},
            borderColor: paletaTeal,
            backgroundColor: "#35d6b833",
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointBackgroundColor: paletaTeal
        }}]
    }},
    options: {{
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: '#1c1f2b' }} }} }}
    }}
}});

new Chart(document.getElementById('chartDispositivos'), {{
    type: 'doughnut',
    data: {{
        labels: {dispositivos_labels},
        datasets: [{{ data: {dispositivos_valores}, backgroundColor: paletaMix, borderColor: "#14161f", borderWidth: 3 }}]
    }},
    options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, padding: 14 }} }} }} }}
}});

new Chart(document.getElementById('chartConclusao'), {{
    type: 'bar',
    data: {{
        labels: {conclusao_disp_labels},
        datasets: [{{ data: {conclusao_disp_valores}, backgroundColor: paletaAmber, borderRadius: 6 }}]
    }},
    options: {{
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: '#1c1f2b' }} }} }}
    }}
}});

new Chart(document.getElementById('chartGenero'), {{
    type: 'bar',
    data: {{
        labels: {genero_labels},
        datasets: [{{ data: {genero_valores}, backgroundColor: paletaViolet, borderRadius: 6 }}]
    }},
    options: {{
        maintainAspectRatio: false,
        layout: {{ padding: {{ bottom: 8 }} }},
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 40, minRotation: 40, autoSkip: false }} }}, y: {{ grid: {{ color: '#1c1f2b' }} }} }}
    }}
}});

new Chart(document.getElementById('chartSemana'), {{
    type: 'doughnut',
    data: {{
        labels: {semana_labels},
        datasets: [{{ data: {semana_valores}, backgroundColor: [paletaTeal, paletaViolet], borderColor: "#14161f", borderWidth: 3 }}]
    }},
    options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, padding: 14 }} }} }} }}
}});
</script>
</body>
</html>"""


def main():
    conn = sqlite3.connect(DB_PATH)
    d = buscar_dados(conn)
    conn.close()

    linhas_avaliados = ""
    for titulo, genero, qtd, nota in d["top_avaliados"]:
        linhas_avaliados += f"<tr><td>{titulo}</td><td>{genero}</td><td class='num'>{qtd}</td><td class='num'>{nota}</td></tr>"

    html = HTML_TEMPLATE.format(
        kpi_total_views=d["kpi_total_views"],
        kpi_titulo_top=d["kpi_titulo_top"],
        kpi_titulo_top_views=d["kpi_titulo_top_views"],
        kpi_taxa_conclusao=d["kpi_taxa_conclusao"],
        kpi_usuario_top=d["kpi_usuario_top"],
        kpi_usuario_top_horas=d["kpi_usuario_top_horas"],
        top_titulos_labels=json.dumps(d["top_titulos_labels"], ensure_ascii=False),
        top_titulos_valores=json.dumps(d["top_titulos_valores"]),
        evolucao_labels=json.dumps(d["evolucao_labels"]),
        evolucao_valores=json.dumps(d["evolucao_valores"]),
        dispositivos_labels=json.dumps(d["dispositivos_labels"], ensure_ascii=False),
        dispositivos_valores=json.dumps(d["dispositivos_valores"]),
        conclusao_disp_labels=json.dumps(d["conclusao_disp_labels"], ensure_ascii=False),
        conclusao_disp_valores=json.dumps(d["conclusao_disp_valores"]),
        genero_labels=json.dumps(d["genero_labels"], ensure_ascii=False),
        genero_valores=json.dumps(d["genero_valores"]),
        semana_labels=json.dumps(d["semana_labels"], ensure_ascii=False),
        semana_valores=json.dumps(d["semana_valores"]),
        linhas_avaliados=linhas_avaliados,
    )

    SAIDA_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard gerado em: {SAIDA_PATH}")


if __name__ == "__main__":
    main()