"""
queries.py
Todas las queries SQL del proyecto, centralizadas. SQL puro, sin ORM.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "pokemon.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ------------------------------------------------------------
# cards (caché de la API)
# ------------------------------------------------------------

def get_recently_viewed(conn, limit=8):
    """Últimas cartas consultadas, para la pantalla de inicio."""
    query = """
        SELECT id, name, set_id, set_name, number, rarity, image_url
        FROM cards
        ORDER BY cached_at DESC
        LIMIT ?
    """
    return conn.execute(query, (limit,)).fetchall()


def upsert_set(conn, set_data):
    query = """
        INSERT OR REPLACE INTO sets_cache (id, name, series, release_date, logo_url, symbol_url)
        VALUES (:id, :name, :series, :release_date, :logo_url, :symbol_url)
    """
    conn.execute(query, set_data)
    conn.commit()


def get_cached_sets(conn, limit=12):
    query = """
        SELECT id, name, series, release_date, logo_url, symbol_url
        FROM sets_cache
        ORDER BY release_date DESC
        LIMIT ?
    """
    return conn.execute(query, (limit,)).fetchall()


def search_cached_cards(conn, query, limit=40):
    """
    Busca cartas ya guardadas en el caché local antes de pegarle a la API
    externa. Usa LIKE, no es tan sofisticado como el buscador real de
    pokemontcg.io, pero es instantáneo para búsquedas repetidas.
    """
    like_pattern = f"%{query}%"
    rows = conn.execute(
        "SELECT id, name, set_id, set_name, number, rarity, image_url "
        "FROM cards WHERE name LIKE ? COLLATE NOCASE LIMIT ?",
        (like_pattern, limit),
    ).fetchall()
    return rows


def upsert_card(conn, card):
    """
    Guarda o actualiza una carta en el caché local.
    INSERT OR REPLACE porque la info de una carta (rareza, imagen, etc.)
    prácticamente no cambia, así que sobreescribir es seguro y simple.
    """
    query = """
        INSERT OR REPLACE INTO cards (id, name, set_id, set_name, number, rarity, image_url)
        VALUES (:id, :name, :set_id, :set_name, :number, :rarity, :image_url)
    """
    conn.execute(query, card)
    conn.commit()


def get_card(conn, card_id):
    row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    return row


# ------------------------------------------------------------
# price_snapshots
# ------------------------------------------------------------

def insert_price_snapshot(conn, card_id, date, tcgplayer_market, cardmarket_avg):
    """
    Guarda el precio del día. OR REPLACE respeta el UNIQUE(card_id, date):
    si ya consultaste esta carta hoy, actualiza el snapshot en vez de
    crear uno nuevo (así no se ensucia el historial con varias entradas
    del mismo día).
    """
    query = """
        INSERT OR REPLACE INTO price_snapshots (card_id, date, tcgplayer_market, cardmarket_avg)
        VALUES (?, ?, ?, ?)
    """
    conn.execute(query, (card_id, date, tcgplayer_market, cardmarket_avg))
    conn.commit()


def get_price_history(conn, card_id):
    """Todo el historial de precios de una carta, ordenado por fecha."""
    query = """
        SELECT date, tcgplayer_market, cardmarket_avg
        FROM price_snapshots
        WHERE card_id = ?
        ORDER BY date ASC
    """
    return conn.execute(query, (card_id,)).fetchall()


def get_latest_price(conn, card_id):
    """El snapshot más reciente de una carta (para mostrar 'valor actual')."""
    query = """
        SELECT date, tcgplayer_market, cardmarket_avg
        FROM price_snapshots
        WHERE card_id = ?
        ORDER BY date DESC
        LIMIT 1
    """
    return conn.execute(query, (card_id,)).fetchone()


# ------------------------------------------------------------
# collection
# ------------------------------------------------------------

def add_to_collection(conn, card_id, quantity, condition, acquired_date, acquired_price, notes):
    query = """
        INSERT INTO collection (card_id, quantity, condition, acquired_date, acquired_price, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor = conn.execute(query, (card_id, quantity, condition, acquired_date, acquired_price, notes))
    conn.commit()
    return cursor.lastrowid


def get_collection(conn):
    """
    Trae toda tu colección con el nombre/imagen de la carta (JOIN a cards)
    y el precio más reciente conocido (subquery correlacionada a
    price_snapshots), para poder calcular ganancia/pérdida en el frontend.
    """
    query = """
        SELECT
            col.id,
            col.card_id,
            c.name,
            c.set_name,
            c.image_url,
            col.quantity,
            col.condition,
            col.acquired_price,
            col.acquired_date,
            (
                SELECT tcgplayer_market
                FROM price_snapshots ps
                WHERE ps.card_id = col.card_id
                ORDER BY ps.date DESC
                LIMIT 1
            ) AS current_price
        FROM collection col
        JOIN cards c ON c.id = col.card_id
        ORDER BY col.created_at DESC
    """
    return conn.execute(query).fetchall()


def update_collection_item(conn, item_id, quantity, condition):
    query = """
        UPDATE collection
        SET quantity = ?, condition = ?
        WHERE id = ?
    """
    cursor = conn.execute(query, (quantity, condition, item_id))
    conn.commit()
    return cursor.rowcount == 1


def delete_collection_item(conn, item_id):
    cursor = conn.execute("DELETE FROM collection WHERE id = ?", (item_id,))
    conn.commit()
    return cursor.rowcount == 1