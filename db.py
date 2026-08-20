"""
Strat de acces la baza de date.

MOD LOCAL (implicit): folosește un fișier SQLite (tabara.db) — perfect pentru
testare pe un singur calculator, dar NU sincronizează între mai multe
calculatoare/telefoane.

MOD ONLINE (recomandat pentru folosire reală): setează variabilele de mediu
SUPABASE_URL și SUPABASE_DB_PASSWORD (vezi README.md) — aplicația se va
conecta atunci la baza de date Postgres din Supabase, iar toate
calculatoarele/telefoanele vor vedea aceleași date, în timp real.

Restul aplicației (paginile Streamlit) NU trebuie modificat quando schimbi
modul — toate funcțiile de mai jos rămân la fel.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).parent
SQLITE_PATH = BASE_DIR / "tabara.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

USE_SUPABASE = bool(os.environ.get("SUPABASE_URL"))


def get_raw_connection():
    """Returnează o conexiune brută (sqlite3 sau psycopg2, în funcție de mod)."""
    if USE_SUPABASE:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(
            host=os.environ["SUPABASE_DB_HOST"],
            port=os.environ.get("SUPABASE_DB_PORT", "5432"),
            dbname=os.environ.get("SUPABASE_DB_NAME", "postgres"),
            user=os.environ.get("SUPABASE_DB_USER", "postgres"),
            password=os.environ["SUPABASE_DB_PASSWORD"],
        )
        return conn
    else:
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


@contextmanager
def get_cursor(commit=False):
    conn = get_raw_connection()
    try:
        if USE_SUPABASE:
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db():
    """Creează tabelele dacă nu există — DOAR pentru modul local (SQLite).
    Pentru Supabase, rulează schema_postgres.sql manual în SQL Editor (vezi README.md)."""
    if USE_SUPABASE:
        raise RuntimeError(
            "Rulează schema_postgres.sql în Supabase SQL Editor (vezi README.md) — "
            "init_db() automat este disponibil doar în modul local."
        )
    schema_sql = SCHEMA_PATH.read_text()
    conn = get_raw_connection()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def _adapt(sql):
    """Traduce placeholderele stil SQLite (?) în stil psycopg2 (%s) când e nevoie."""
    return sql.replace("?", "%s") if USE_SUPABASE else sql


def query(sql, params=()):
    """SELECT — returnează listă de dict-uri."""
    with get_cursor() as cur:
        cur.execute(_adapt(sql), params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def execute(sql, params=()):
    """INSERT/UPDATE/DELETE — returnează id-ul rândului inserat (dacă e cazul)."""
    with get_cursor(commit=True) as cur:
        adapted = _adapt(sql)
        if USE_SUPABASE and adapted.strip().upper().startswith("INSERT") and "RETURNING" not in adapted.upper():
            adapted += " RETURNING id"
        cur.execute(adapted, params)
        if USE_SUPABASE:
            if adapted.strip().upper().startswith("INSERT"):
                row = cur.fetchone()
                return row["id"] if row else None
            return None
        return cur.lastrowid
