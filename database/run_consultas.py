"""
run_consultas.py
Lê o arquivo consultas.sql, executa cada consulta contra o streaming.db
e imprime os resultados formatados no terminal.

Por que isso existe: um arquivo .sql sozinho é só texto (mesma lógica do
schema.sql lá no começo do projeto). Esse script é quem de fato LÊ o
consultas.sql e manda o SQLite EXECUTAR cada consulta, uma por vez.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "streaming.db"
CONSULTAS_PATH = BASE_DIR / "consultas.sql"

# Título descritivo de cada consulta, na mesma ordem em que aparecem
# no consultas.sql — só para deixar a saída do terminal legível
TITULOS_CONSULTAS = [
    "1) Top 5 títulos mais assistidos",
    "2) Ranking de usuários por minutos assistidos (RANK)",
    "3) Taxa de conclusão por dispositivo",
    "4) Evolução mensal de minutos assistidos",
    "5) Gênero mais assistido por plano",
    "6) Usuário mais ativo dentro de cada plano (ROW_NUMBER)",
    "7) Títulos mais bem avaliados (mín. 10 avaliações)",
    "8) Fim de semana vs dia de semana",
    "9) Usuários que assistem acima da média geral",
    "10) Distribuição por classificação etária e tipo",
]


def carregar_consultas():
    """Lê o arquivo .sql e separa em uma lista de comandos SELECT individuais."""
    with open(CONSULTAS_PATH, "r", encoding="utf-8") as f:
        conteudo = f.read()

    comandos = []
    for bloco in conteudo.split(";"):
        bloco = bloco.strip()
        if "SELECT" in bloco.upper():
            comandos.append(bloco)
    return comandos


def main():
    conn = sqlite3.connect(DB_PATH)
    consultas = carregar_consultas()

    for titulo, sql in zip(TITULOS_CONSULTAS, consultas):
        print("\n" + "=" * 60)
        print(titulo)
        print("=" * 60)

        cursor = conn.execute(sql)
        colunas = [desc[0] for desc in cursor.description]
        linhas = cursor.fetchall()

        print(" | ".join(colunas))
        print("-" * 60)
        for linha in linhas:
            print(" | ".join(str(v) for v in linha))

    conn.close()


if __name__ == "__main__":
    main()