"""
conftest.py
Fixtures compartidas para los tests del backend.

Regla clave: nunca se usa backend/data/pokemon.db. Cada test obtiene una
base de datos sqlite temporal (dentro de tmp_path) con el esquema de
schema.sql ya aplicado, y queries.DB_PATH apunta ahí vía monkeypatch.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import queries
from app.main import app

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "app" / "db" / "schema.sql"


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Crea una base de datos sqlite temporal con el esquema aplicado y
    hace que queries.DB_PATH apunte a ella en vez de a la real."""
    db_path = tmp_path / "test_pokemon.db"
    monkeypatch.setattr(queries, "DB_PATH", db_path)

    conn = queries.get_connection()
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
    finally:
        conn.close()

    return db_path


@pytest.fixture
def client(db):
    """TestClient de FastAPI que usa la base de datos temporal de `db`."""
    return TestClient(app)
