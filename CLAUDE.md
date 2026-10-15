# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Pokémon TCG card tracker: search cards via the pokemontcg.io API, track price
history, and manage a personal collection with cost-vs-current-value. Spanish
is used throughout code comments, docstrings, and README files — match that
convention when editing existing files.

## Commands

### Backend (run from `backend/`)
```bash
pip install -r requirements.txt --break-system-packages

# create/reset the SQLite database (reads schema.sql, must be run before first use)
python3 -c "import sqlite3; c = sqlite3.connect('data/pokemon.db'); c.executescript(open('app/db/schema.sql').read()); c.close()"

# run the API (must be run from backend/, not app/ or data/ — the
# `app.main:app` import string needs `app/` importable from cwd)
python3 -m uvicorn app.main:app --reload
```
API at `http://127.0.0.1:8000`, interactive docs at `/docs`. No test suite exists in this repo.

### Frontend (run from `frontend/`)
```bash
npm install
npm run dev       # http://localhost:5173, requires backend running concurrently
npm run build
```

### Optional API key
pokemontcg.io is deprecated and no longer issues new keys; the app works
unauthenticated with lower rate limits. An existing key goes in `backend/.env`
as `POKEMONTCG_API_KEY=...` (loaded via `python-dotenv` in `pokemon_api.py`).

## Architecture

**Backend** — FastAPI + raw `sqlite3` (no ORM, no SQLAlchemy). All SQL lives
in one place: `backend/app/db/queries.py`. Routers call into `queries.py` and
`services/pokemon_api.py`; they never run SQL or HTTP calls inline.

- `app/main.py` — app setup, CORS, router registration.
- `app/db/schema.sql` — table definitions, applied manually via the command above (no migration tool).
- `app/db/queries.py` — every query in the project, grouped by table. Each endpoint opens a connection via `get_connection()` and closes it itself in a `try/finally` so it's released even on exceptions (no shared session/dependency injection).
- `app/services/pokemon_api.py` — the only module that talks to the external pokemontcg.io API. Retries each request up to 3x with a 1.5s backoff before raising `PokemonAPIError`, since the free/unauthenticated tier is intermittently flaky rather than reliably down. Also owns `_simplify_card`/`_simplify_set` (external JSON → internal dict shape) and `extract_prices` (pulls a representative TCGPlayer `market` price and the Cardmarket average out of the API's nested price-by-finish structure).
- `app/routers/` — `cards.py` (search/detail/history), `collection.py`, `browse.py` (home screen: recently viewed + sets).
- `app/models/schemas.py` — Pydantic response models.

**Data model** (`schema.sql`), key relationships and why they're shaped this way:
- `cards` is a local cache of anything ever fetched from the external API, keyed by the external API's own card id (e.g. `base1-4`) — no separate internal id is minted.
- `price_snapshots` has `UNIQUE(card_id, date)`; every `GET /cards/{id}` fetch does `INSERT OR REPLACE`, so re-querying the same card on the same day updates that day's snapshot instead of duplicating it. The external API only ever returns the *current* price — this table is how price history is built, one snapshot at a time, purely from app usage over multiple days.
- `collection` (the cards the user actually owns) is intentionally separate from `cards` (the search cache) — a card can be cached from a search without being owned, and a card can be owned in multiple quantities/conditions.
- `sets_cache` mirrors the `cards` caching pattern for set/expansion data.

**Cache-first request flow**: endpoints that hit the external API (search,
sets) check the local SQLite cache first and only call `pokemon_api.py` on a
miss, then upsert results back into the cache. This is both a speed
optimization and a way to conserve the external API's low unauthenticated
rate limit — preserve this pattern when adding new endpoints that wrap
external data.

**Frontend** — React + Vite, Tailwind, Recharts for price-history charts.
- `src/api/client.js` — the only place `fetch` is called; every backend call goes through here, with a shared `handle()` that unwraps FastAPI's `{"detail": ...}` error shape into a thrown `Error`.
- `src/pages/Tracker.jsx` — main page/state container.
- `src/components/` — `Home.jsx` (landing view), `SearchBar.jsx`, `CardGrid.jsx`/`CardGridSkeleton.jsx`, `CardDetailPanel.jsx`, `CollectionList.jsx`.
- Visual identity is a dark "card binder" theme — custom Tailwind tokens (`ink`, `surface`, `gold`, `gain`/`loss`, etc.) are defined in `tailwind.config.js`; reuse those tokens rather than introducing new colors.
- Backend base URL is hardcoded in `client.js` as `http://127.0.0.1:8000` (no env-based config).

## Subagentes

- Cuando pida revisar mis cambios o revisar antes de commit, delega siempre al
  subagente `architecture-guard` (`.claude/agents/architecture-guard.md`). Si
  además usas la skill `code-review`, úsala como complemento, no como reemplazo.
