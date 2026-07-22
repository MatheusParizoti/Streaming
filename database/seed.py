"""
seed_data.py
Gera e popula o banco streaming.db a partir do schema.sql,
com dados fake porém realistas para permitir consultas analíticas.
"""

import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

# Mesma lógica do create_database.py: referência é a pasta ONDE ESTE
# SCRIPT ESTÁ, não a pasta de onde o comando é rodado no terminal.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "streaming.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

random.seed(42)  # reprodutibilidade

# -------------------------------------------------------------
# 1. Criar o banco a partir do schema
# -------------------------------------------------------------
def criar_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


# -------------------------------------------------------------
# 2. Dados de referência
# -------------------------------------------------------------
NOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Hugo",
    "Isabela", "João", "Karina", "Lucas", "Mariana", "Nicolas", "Otávio",
    "Patrícia", "Rafael", "Sofia", "Thiago", "Vanessa",
]
PAISES = ["Brasil", "Portugal", "Argentina", "México", "Estados Unidos", "Espanha"]
PLANOS = ["free", "basico", "premium"]

TITULOS = [
    ("Fronteira Escarlate", "filme", "Ação", 2021, 118, "14"),
    ("Noites de Verão", "filme", "Romance", 2019, 102, "12"),
    ("O Último Algoritmo", "filme", "Ficção Científica", 2023, 131, "12"),
    ("Sombras da Cidade", "serie", "Suspense", 2020, 45, "16"),
    ("Cozinha Aberta", "serie", "Documentário", 2022, 38, "L"),
    ("Reinos Perdidos", "serie", "Fantasia", 2018, 55, "14"),
    ("Risadas de Sábado", "serie", "Comédia", 2021, 25, "10"),
    ("Corrida Final", "filme", "Ação", 2020, 109, "12"),
    ("Vidas Cruzadas", "filme", "Drama", 2022, 124, "14"),
    ("Mundo Invertido", "serie", "Ficção Científica", 2023, 48, "16"),
    ("Amor em Lisboa", "filme", "Romance", 2017, 96, "L"),
    ("Investigação Nº7", "serie", "Suspense", 2019, 42, "16"),
    ("Herança de Sangue", "filme", "Terror", 2022, 105, "18"),
    ("Piadas do Bairro", "serie", "Comédia", 2020, 22, "10"),
    ("Trilhas Selvagens", "serie", "Documentário", 2021, 40, "L"),
    ("Guerreiros do Norte", "filme", "Fantasia", 2019, 140, "14"),
    ("Segredos de Família", "serie", "Drama", 2023, 50, "14"),
    ("Velocidade Máxima", "filme", "Ação", 2018, 112, "12"),
    ("Coração Partido", "filme", "Romance", 2021, 99, "12"),
    ("A Última Fronteira", "filme", "Ficção Científica", 2020, 128, "14"),
    ("Ruas Perigosas", "serie", "Suspense", 2022, 47, "16"),
    ("Sabores do Mundo", "serie", "Documentário", 2019, 35, "L"),
    ("Coroa de Ferro", "serie", "Fantasia", 2017, 58, "16"),
    ("Zoeira Geral", "serie", "Comédia", 2023, 24, "10"),
    ("Marca da Morte", "filme", "Terror", 2021, 101, "18"),
    ("Além do Horizonte", "filme", "Drama", 2019, 115, "12"),
    ("Circuito Fechado", "serie", "Suspense", 2021, 44, "14"),
    ("Paixão em Roma", "filme", "Romance", 2020, 108, "12"),
    ("Planeta X", "filme", "Ficção Científica", 2022, 122, "14"),
    ("Legado Ancestral", "serie", "Fantasia", 2020, 52, "14"),
]

DISPOSITIVOS = [
    ("Smart TV", "Tizen OS"),
    ("Celular", "Android"),
    ("Celular", "iOS"),
    ("Notebook", "Windows"),
    ("Console", "PlayStation OS"),
]

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


# -------------------------------------------------------------
# 3. Popular dimensões
# -------------------------------------------------------------
def popular_usuarios(conn):
    hoje = date(2026, 7, 16)
    for nome in NOMES:
        idade = random.randint(16, 65)
        pais = random.choice(PAISES)
        plano = random.choices(PLANOS, weights=[0.3, 0.35, 0.35])[0]
        dias_atras = random.randint(30, 900)
        data_cadastro = (hoje - timedelta(days=dias_atras)).isoformat()
        conn.execute(
            "INSERT INTO dim_usuarios (nome, idade, pais, plano, data_cadastro) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, idade, pais, plano, data_cadastro),
        )


def popular_titulos(conn):
    for t in TITULOS:
        conn.execute(
            "INSERT INTO dim_titulos "
            "(titulo, tipo, genero, ano_lancamento, duracao_min, classificacao) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            t,
        )


def popular_dispositivos(conn):
    for d in DISPOSITIVOS:
        conn.execute(
            "INSERT INTO dim_dispositivos (tipo_dispositivo, sistema_operacional) "
            "VALUES (?, ?)",
            d,
        )


def popular_tempo(conn):
    inicio = date(2026, 1, 1)
    dias = 197  # cobre até 16/07/2026
    for i in range(dias):
        d = inicio + timedelta(days=i)
        dia_semana = DIAS_SEMANA_PT[d.weekday()]
        fim_de_semana = 1 if d.weekday() >= 5 else 0
        trimestre = (d.month - 1) // 3 + 1
        conn.execute(
            "INSERT INTO dim_tempo (data, dia_semana, mes, ano, trimestre, fim_de_semana) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (d.isoformat(), dia_semana, d.month, d.year, trimestre, fim_de_semana),
        )


# -------------------------------------------------------------
# 4. Popular a tabela fato (COM DESEQUILÍBRIOS PROPOSITAIS)
# -------------------------------------------------------------
# A ideia aqui: dado real de streaming NUNCA é equilibrado. Um punhado de
# títulos vira "hit" e concentra a maioria das visualizações, enquanto a
# cauda longa de títulos mal é assistida. Usuário premium assiste mais que
# free. Celular domina os dispositivos. E fim de semana tem mais audiência
# que dia de semana. Simulamos tudo isso com PESOS (random.choices), ao
# invés de sorteio uniforme (random.choice) — é essa a diferença técnica
# que gera dado "desequilibrado de propósito" em vez de "tudo parecido".
def popular_visualizacoes(conn, n=650):
    usuarios_rows = conn.execute("SELECT id, plano FROM dim_usuarios ORDER BY id").fetchall()
    titulos_rows = conn.execute("SELECT id, duracao_min FROM dim_titulos ORDER BY id").fetchall()
    dispositivos_rows = conn.execute("SELECT id FROM dim_dispositivos ORDER BY id").fetchall()
    tempo_rows = conn.execute("SELECT id, fim_de_semana FROM dim_tempo ORDER BY id").fetchall()

    # --- pesos de usuários: poucos concentram muita audiência (cauda longa) ---
    # peso ~ 1/rank é uma distribuição tipo Zipf: o rank 0 pesa muito mais
    # que o rank 19. Multiplicamos ainda pelo plano: premium assiste mais.
    plano_multiplicador = {"free": 0.6, "basico": 1.0, "premium": 1.5}
    usuarios_ids = [uid for uid, _ in usuarios_rows]
    pesos_usuarios = [
        (1 / (rank + 1)) * plano_multiplicador[plano]
        for rank, (uid, plano) in enumerate(usuarios_rows)
    ]

    # --- pesos de títulos: alguns viram "hit", maioria fica esquecida ---
    # embaralhamos antes de aplicar o peso Zipf, pra o "hit" não ser sempre
    # o primeiro título cadastrado (senão o desequilíbrio ficaria óbvio/artificial)
    titulos_ids = [t[0] for t in titulos_rows]
    duracao_por_id = {tid: dur for tid, dur in titulos_rows}
    ordem_embaralhada = titulos_ids[:]
    random.shuffle(ordem_embaralhada)
    peso_por_titulo = {tid: 1 / (rank + 1) for rank, tid in enumerate(ordem_embaralhada)}
    pesos_titulos = [peso_por_titulo[tid] for tid in titulos_ids]

    # --- pesos de dispositivos: celular domina, console é raro ---
    # ordem segue DISPOSITIVOS: Smart TV, Celular/Android, Celular/iOS, Notebook, Console
    dispositivos_ids = [d[0] for d in dispositivos_rows]
    pesos_dispositivos = [0.30, 0.32, 0.16, 0.14, 0.08][: len(dispositivos_ids)]

    # --- pesos de tempo: fim de semana assiste mais + tendência de crescimento ---
    # peso cresce ao longo dos ~197 dias (0.6x no início até 1.8x no fim),
    # simulando a plataforma "crescendo" — ótimo pra uma query de evolução mensal
    tempo_ids = [t[0] for t in tempo_rows]
    total_dias = len(tempo_rows)
    pesos_tempo = []
    for idx, (tid, fim_semana) in enumerate(tempo_rows):
        peso = 1.8 if fim_semana else 1.0
        peso *= 0.6 + 1.2 * (idx / total_dias)
        pesos_tempo.append(peso)

    for _ in range(n):
        usuario_id = random.choices(usuarios_ids, weights=pesos_usuarios, k=1)[0]
        titulo_id = random.choices(titulos_ids, weights=pesos_titulos, k=1)[0]
        dispositivo_id = random.choices(dispositivos_ids, weights=pesos_dispositivos, k=1)[0]
        tempo_id = random.choices(tempo_ids, weights=pesos_tempo, k=1)[0]

        duracao = duracao_por_id[titulo_id]

        # simula quanto da duração o usuário assistiu
        pct_assistido = random.betavariate(2, 1.3)  # tende a assistir bastante
        minutos_assistidos = max(1, int(duracao * pct_assistido))
        completou = 1 if pct_assistido > 0.9 else 0

        # nem todo mundo avalia (30% de chance de ficar NULL)
        avaliacao = random.choices(
            [None, 1, 2, 3, 4, 5],
            weights=[30, 3, 5, 12, 25, 25],
        )[0]

        conn.execute(
            "INSERT INTO fato_visualizacoes "
            "(usuario_id, titulo_id, dispositivo_id, tempo_id, minutos_assistidos, completou, avaliacao) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (usuario_id, titulo_id, dispositivo_id, tempo_id, minutos_assistidos, completou, avaliacao),
        )


# -------------------------------------------------------------
# 5. Main
# -------------------------------------------------------------
def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("Criando schema...")
    criar_schema(conn)

    print("Populando dim_usuarios...")
    popular_usuarios(conn)

    print("Populando dim_titulos...")
    popular_titulos(conn)

    print("Populando dim_dispositivos...")
    popular_dispositivos(conn)

    print("Populando dim_tempo...")
    popular_tempo(conn)

    print("Populando fato_visualizacoes...")
    popular_visualizacoes(conn, n=650)

    conn.commit()

    # Conferência rápida
    for tabela in ["dim_usuarios", "dim_titulos", "dim_dispositivos", "dim_tempo", "fato_visualizacoes"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        print(f"  {tabela}: {count} registros")

    conn.close()
    print(f"\nBanco '{DB_PATH}' criado e populado com sucesso!")


if __name__ == "__main__":
    main()