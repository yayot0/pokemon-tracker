-- ============================================================
-- schema.sql
-- Esquema de la base de datos para el Pokémon Card Tracker
-- SQLite
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- cards
-- Caché local de cartas que ya se consultaron en la API de
-- pokemontcg.io. Evita pegarle a la API cada vez que se necesita
-- info básica de una carta ya vista.
-- id = el mismo id que usa pokemontcg.io (ej. 'base1-4'),
-- así no hay que inventar uno propio ni mapear IDs.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cards (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    set_id      TEXT,
    set_name    TEXT,
    number      TEXT,          -- número de la carta dentro del set, ej. '4/102'
    rarity      TEXT,
    image_url   TEXT,
    cached_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- price_snapshots
-- Una fila = "esta carta, en esta fecha, valía esto".
-- Guardamos tanto TCGPlayer (mercado US) como Cardmarket (EU)
-- porque pueden variar bastante entre sí.
-- UNIQUE(card_id, date): si consultas la misma carta el mismo
-- día más de una vez, se actualiza el snapshot, no se duplica.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS price_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id             TEXT NOT NULL,
    date                TEXT NOT NULL,      -- 'YYYY-MM-DD'
    tcgplayer_market    REAL,               -- precio de mercado en USD
    cardmarket_avg      REAL,               -- precio promedio en EUR
    fetched_at          TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
    UNIQUE (card_id, date)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_card ON price_snapshots(card_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON price_snapshots(date);

-- ------------------------------------------------------------
-- collection
-- Las cartas que de verdad tienes tú. Separada de 'cards' porque
-- una carta puede existir en tu caché (la buscaste) sin que sea
-- tuya, y puedes tener varias copias con distinta condición.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS collection (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id         TEXT NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 1,
    condition       TEXT NOT NULL DEFAULT 'Near Mint'
                    CHECK (condition IN ('Mint', 'Near Mint', 'Lightly Played',
                                          'Moderately Played', 'Heavily Played', 'Damaged')),
    acquired_date   TEXT,               -- cuándo la conseguiste
    acquired_price  REAL,               -- cuánto pagaste (para comparar vs. valor actual)
    notes           TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_collection_card ON collection(card_id);

-- ------------------------------------------------------------
-- sets_cache
-- Caché local de sets (expansiones), mismo patrón que 'cards'.
-- Sirve para la pantalla de inicio ("sets para explorar").
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sets_cache (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    series          TEXT,
    release_date    TEXT,
    logo_url        TEXT,
    symbol_url      TEXT,
    cached_at       TEXT DEFAULT CURRENT_TIMESTAMP
);