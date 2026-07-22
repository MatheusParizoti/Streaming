"""
create_database.py
Cria o banco streaming.db e aplica as tabelas definidas em schema.sql.

Diferença em relação a uma versão "ingênua": não basta abrir uma conexão
com sqlite3.connect() — isso só cria/abre o ARQUIVO do banco. As tabelas
só existem depois que a gente LÊ o conteúdo do schema.sql e manda o
SQLite EXECUTAR esses comandos (conn.executescript).
"""

import sqlite3
from pathlib import Path

# Path(__file__) = caminho deste próprio script. Usamos a pasta ONDE ELE
# ESTÁ como referência, e não a pasta de onde o comando foi rodado no
# terminal — assim o banco sempre é o mesmo, não importa de onde você chame.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "streaming.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def main():
    # 1. Conecta (isso cria o arquivo .db se ele não existir, mas ainda vazio)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 2. Lê o texto do schema.sql
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # 3. Manda o SQLite executar todos os comandos CREATE TABLE de uma vez
    #    (executescript roda múltiplos comandos separados por ";")
    conn.executescript(schema_sql)

    # 4. Confirma as mudanças no arquivo do banco
    conn.commit()

    # 5. Conferência: lista as tabelas que realmente existem agora no banco
    tabelas = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    conn.close()

    print(f"Banco '{DB_PATH}' criado/atualizado com sucesso.")
    print("Tabelas encontradas no banco:")
    for (nome_tabela,) in tabelas:
        print(f"  - {nome_tabela}")


if __name__ == "__main__":
    main()