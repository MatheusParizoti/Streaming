"""
adicionar_visualizacao.py
Formulário interativo no terminal para adicionar UMA visualização
manualmente no fato_visualizacoes, sem precisar escrever SQL na mão.
"""

import sqlite3
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "streaming.db"

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
PLANOS_VALIDOS = ["free", "basico", "premium"]


def perguntar_numero(pergunta, minimo=None, maximo=None, permitir_vazio=False):
    while True:
        texto = input(pergunta).strip()
        if permitir_vazio and texto == "":
            return None
        if texto.isdigit():
            valor = int(texto)
            if (minimo is None or valor >= minimo) and (maximo is None or valor <= maximo):
                return valor
        print("Valor inválido, tenta de novo.")


def perguntar_sim_nao(pergunta):
    while True:
        texto = input(pergunta + " (s/n): ").strip().lower()
        if texto in ("s", "sim"):
            return 1
        if texto in ("n", "nao", "não"):
            return 0
        print("Responde só com 's' ou 'n'.")


def perguntar_plano():
    print("\nQual o plano?")
    for i, p in enumerate(PLANOS_VALIDOS, start=1):
        print(f"  {i}) {p}")
    escolha = perguntar_numero("Digite o número: ", minimo=1, maximo=len(PLANOS_VALIDOS))
    return PLANOS_VALIDOS[escolha - 1]


# -------------------------------------------------------------
# Usuário: escolher existente OU cadastrar um novo na hora
# -------------------------------------------------------------
def escolher_usuario(conn):
    print("\nQuem assistiu?")
    print("  1) Conta já existente")
    print("  2) Novo usuário")
    opcao = perguntar_numero("Digite o número: ", minimo=1, maximo=2)

    if opcao == 1:
        usuarios = conn.execute(
            "SELECT id, nome, plano FROM dim_usuarios ORDER BY id"
        ).fetchall()

        print("\nSelecione a conta:")
        for i, (uid, nome, plano) in enumerate(usuarios, start=1):
            print(f"  {i}) {nome} ({plano})")
        escolha = perguntar_numero("Digite o número: ", minimo=1, maximo=len(usuarios))
        return usuarios[escolha - 1][0]

    # Cadastro de usuário novo
    print("\n--- Cadastro de novo usuário ---")
    nome = input("Nome: ").strip()
    idade = perguntar_numero("Idade: ", minimo=0, maximo=120)
    pais = input("País: ").strip()
    plano = perguntar_plano()
    data_cadastro = date.today().isoformat()

    cursor = conn.execute(
        "INSERT INTO dim_usuarios (nome, idade, pais, plano, data_cadastro) "
        "VALUES (?, ?, ?, ?, ?)",
        (nome, idade, pais, plano, data_cadastro),
    )
    print(f"Usuário '{nome}' cadastrado com sucesso!")
    return cursor.lastrowid


# -------------------------------------------------------------
# Título: primeiro filtra por gênero, depois lista só dessa categoria
# -------------------------------------------------------------
def escolher_titulo(conn):
    generos = [r[0] for r in conn.execute("SELECT DISTINCT genero FROM dim_titulos ORDER BY genero")]

    print("\nQual o gênero?")
    for i, g in enumerate(generos, start=1):
        print(f"  {i}) {g}")
    escolha_genero = perguntar_numero("Digite o número: ", minimo=1, maximo=len(generos))
    genero_escolhido = generos[escolha_genero - 1]

    titulos = conn.execute(
        "SELECT id, titulo, duracao_min FROM dim_titulos WHERE genero = ? ORDER BY titulo",
        (genero_escolhido,),
    ).fetchall()

    print(f"\nQual título ({genero_escolhido})?")
    for i, (tid, titulo, _) in enumerate(titulos, start=1):
        print(f"  {i}) {titulo}")
    escolha_titulo = perguntar_numero("Digite o número: ", minimo=1, maximo=len(titulos))

    titulo_id, titulo_nome, duracao_min = titulos[escolha_titulo - 1]
    return titulo_id, duracao_min


# -------------------------------------------------------------
# Dispositivo (sem alteração)
# -------------------------------------------------------------
def escolher_dispositivo(conn):
    dispositivos = conn.execute(
        "SELECT id, tipo_dispositivo, sistema_operacional FROM dim_dispositivos ORDER BY id"
    ).fetchall()

    print("\nEm qual dispositivo?")
    for i, (did, tipo, so) in enumerate(dispositivos, start=1):
        print(f"  {i}) {tipo} / {so}")
    escolha = perguntar_numero("Digite o número: ", minimo=1, maximo=len(dispositivos))
    return dispositivos[escolha - 1][0]


# -------------------------------------------------------------
# Data: usa automaticamente a data de hoje, criando a linha na
# dim_tempo se ela ainda não existir
# -------------------------------------------------------------
def obter_tempo_id_hoje(conn):
    hoje = date.today()
    hoje_iso = hoje.isoformat()

    row = conn.execute("SELECT id FROM dim_tempo WHERE data = ?", (hoje_iso,)).fetchone()
    if row:
        return row[0], hoje_iso

    dia_semana = DIAS_SEMANA_PT[hoje.weekday()]
    fim_de_semana = 1 if hoje.weekday() >= 5 else 0
    trimestre = (hoje.month - 1) // 3 + 1

    cursor = conn.execute(
        "INSERT INTO dim_tempo (data, dia_semana, mes, ano, trimestre, fim_de_semana) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (hoje_iso, dia_semana, hoje.month, hoje.year, trimestre, fim_de_semana),
    )
    return cursor.lastrowid, hoje_iso


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("=" * 50)
    print(" Adicionar nova visualização — streaming.db")
    print("=" * 50)

    usuario_id = escolher_usuario(conn)
    titulo_id, duracao_titulo = escolher_titulo(conn)
    dispositivo_id = escolher_dispositivo(conn)
    tempo_id, data_usada = obter_tempo_id_hoje(conn)

    minutos_assistidos = perguntar_numero(
        f"\nQuantos minutos assistiu (a duração total é {duracao_titulo} min)? ",
        minimo=1,
    )
    completou = perguntar_sim_nao("Assistiu até o fim?")
    avaliacao = perguntar_numero(
        "Nota de 1 a 5 (deixe em branco se não avaliou): ",
        minimo=1, maximo=5, permitir_vazio=True,
    )

    conn.execute(
        "INSERT INTO fato_visualizacoes "
        "(usuario_id, titulo_id, dispositivo_id, tempo_id, minutos_assistidos, completou, avaliacao) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (usuario_id, titulo_id, dispositivo_id, tempo_id, minutos_assistidos, completou, avaliacao),
    )
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM fato_visualizacoes").fetchone()[0]
    conn.close()

    print(f"\nVisualização registrada em {data_usada}!")
    print(f"O banco agora tem {total} registros em fato_visualizacoes.")
    print("Rode 'python3 gerar_dashboard.py' de novo para atualizar o painel com esse novo dado.")


if __name__ == "__main__":
    main()