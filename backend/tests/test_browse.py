"""
test_browse.py
Tests del router app/routers/browse.py: pantalla de inicio (cartas vistas
recientemente), listado de sets (cache-first, igual que la búsqueda de
cartas) y cartas dentro de un set.
"""
import pytest

from app.db import queries
from app.services import pokemon_api
from app.services.pokemon_api import PokemonAPIError


def _carta_simplificada(card_id="base1-4", name="Charizard"):
    """Shape que devuelve `pokemon_api._simplify_card`."""
    return {
        "id": card_id,
        "name": name,
        "set_id": "base1",
        "set_name": "Base Set",
        "number": "4",
        "rarity": "Rare Holo",
        "image_url": "https://example.com/charizard.png",
    }


def _insertar_carta_en_cache(card_id="base1-4", name="Charizard"):
    """Inserta una carta directamente en la tabla `cards` (caché), como si
    ya se hubiera consultado/buscado antes."""
    conn = queries.get_connection()
    try:
        queries.upsert_card(conn, _carta_simplificada(card_id, name))
    finally:
        conn.close()


def _set_simplificado(set_id="base1", name="Base Set"):
    """Shape que devuelve `pokemon_api._simplify_set`."""
    return {
        "id": set_id,
        "name": name,
        "series": "Base",
        "release_date": "1999-01-09",
        "logo_url": "https://example.com/base1-logo.png",
        "symbol_url": "https://example.com/base1-symbol.png",
    }


def _insertar_set_en_cache(set_id="base1", name="Base Set"):
    conn = queries.get_connection()
    try:
        queries.upsert_set(conn, _set_simplificado(set_id, name))
    finally:
        conn.close()


# ------------------------------------------------------------
# GET /cards/recent
# ------------------------------------------------------------

def test_cartas_recientes_vacio_devuelve_lista_vacia(client):
    """Caso feliz: sin nada en el caché de `cards`, devuelve []."""
    response = client.get("/cards/recent")

    assert response.status_code == 200
    assert response.json() == []


def test_cartas_recientes_devuelve_las_cacheadas(client):
    """Caso feliz: cartas que ya están en el caché local (porque se
    buscaron o se consultó su detalle antes) aparecen como 'recientes'."""
    _insertar_carta_en_cache("base1-4", "Charizard")
    _insertar_carta_en_cache("base1-58", "Pikachu")

    response = client.get("/cards/recent")

    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body}
    assert ids == {"base1-4", "base1-58"}


# ------------------------------------------------------------
# GET /sets
# ------------------------------------------------------------

def test_listar_sets_con_cache_miss_llama_a_la_api_y_guarda_en_cache(client, monkeypatch):
    """Sin sets en el caché local, debe pegarle a `pokemon_api.get_sets` y
    guardar el resultado en `sets_cache` para la próxima vez."""
    llamadas = []

    def fake_get_sets(*args, **kwargs):
        llamadas.append(1)
        return [_set_simplificado()]

    monkeypatch.setattr(pokemon_api, "get_sets", fake_get_sets)

    response = client.get("/sets")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "base1"
    assert body[0]["name"] == "Base Set"
    assert len(llamadas) == 1


def test_listar_sets_con_cache_hit_no_llama_a_la_api(client, monkeypatch):
    """Regla cache-first: si ya hay sets en `sets_cache`, no debe llamar a
    `pokemon_api.get_sets`."""
    _insertar_set_en_cache()

    llamadas = []

    def fake_get_sets(*args, **kwargs):
        llamadas.append(1)
        return [_set_simplificado()]

    monkeypatch.setattr(pokemon_api, "get_sets", fake_get_sets)

    response = client.get("/sets")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "base1"
    assert llamadas == []


def test_listar_sets_guarda_en_cache_tras_un_miss(client, monkeypatch):
    """Tras un cache miss, el resultado se guarda en `sets_cache`: una
    segunda consulta ya no debe llamar a la API externa."""
    llamadas = []

    def fake_get_sets(*args, **kwargs):
        llamadas.append(1)
        return [_set_simplificado()]

    monkeypatch.setattr(pokemon_api, "get_sets", fake_get_sets)

    primera = client.get("/sets")
    segunda = client.get("/sets")

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert len(llamadas) == 1


def test_listar_sets_con_error_de_api_responde_503(client, monkeypatch):
    """Si `pokemon_api.get_sets` lanza PokemonAPIError (cache miss), el
    endpoint debe traducirlo a un 503."""

    def fake_get_sets(*args, **kwargs):
        raise PokemonAPIError("la API externa no respondió")

    monkeypatch.setattr(pokemon_api, "get_sets", fake_get_sets)

    response = client.get("/sets")

    assert response.status_code == 503
    assert "no respondió" in response.json()["detail"]


# ------------------------------------------------------------
# GET /sets/{set_id}/cards
# ------------------------------------------------------------

def test_cartas_de_un_set_responde_200_y_guarda_en_cache(client, monkeypatch):
    """Caso feliz: trae las cartas de un set y las guarda en el caché de
    `cards` (quedarán disponibles para /cards/search y /cards/recent)."""

    def fake_search_cards_in_set(set_id, *args, **kwargs):
        assert set_id == "base1"
        return [_carta_simplificada()]

    monkeypatch.setattr(pokemon_api, "search_cards_in_set", fake_search_cards_in_set)

    response = client.get("/sets/base1/cards")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "base1-4"

    recientes = client.get("/cards/recent").json()
    assert any(c["id"] == "base1-4" for c in recientes)


def test_cartas_de_un_set_con_error_de_api_responde_503(client, monkeypatch):
    """Si `pokemon_api.search_cards_in_set` lanza PokemonAPIError, el
    endpoint responde 503."""

    def fake_search_cards_in_set(set_id, *args, **kwargs):
        raise PokemonAPIError("la API externa no respondió")

    monkeypatch.setattr(pokemon_api, "search_cards_in_set", fake_search_cards_in_set)

    response = client.get("/sets/base1/cards")

    assert response.status_code == 503
    assert "no respondió" in response.json()["detail"]


def test_cartas_de_un_set_cache_miss_registra_en_set_cards_cache(client, monkeypatch):
    """Tras un cache-miss, cada carta devuelta por la API externa debe
    quedar registrada en `set_cards_cache` para ese set."""

    def fake_search_cards_in_set(set_id, *args, **kwargs):
        return [_carta_simplificada("jungle-1", "Clefable")]

    monkeypatch.setattr(pokemon_api, "search_cards_in_set", fake_search_cards_in_set)

    response = client.get("/sets/jungle/cards")
    assert response.status_code == 200

    conn = queries.get_connection()
    try:
        fila = conn.execute(
            "SELECT set_id, card_id FROM set_cards_cache WHERE set_id = ? AND card_id = ?",
            ("jungle", "jungle-1"),
        ).fetchone()
    finally:
        conn.close()

    assert fila is not None
    assert fila["set_id"] == "jungle"
    assert fila["card_id"] == "jungle-1"


def test_cartas_de_un_set_segunda_llamada_no_pega_a_la_api(client, monkeypatch):
    """Regla cache-first: tras un primer cache-miss que llena `set_cards_cache`,
    una segunda consulta al mismo set no debe volver a llamar a
    `pokemon_api.search_cards_in_set`."""

    def fake_search_cards_in_set(set_id, *args, **kwargs):
        return [_carta_simplificada("fossil-2", "Articuno")]

    monkeypatch.setattr(pokemon_api, "search_cards_in_set", fake_search_cards_in_set)

    primera = client.get("/sets/fossil/cards")
    assert primera.status_code == 200
    primer_body = primera.json()

    def fake_search_cards_in_set_que_no_debe_llamarse(set_id, *args, **kwargs):
        pytest.fail("search_cards_in_set no debe llamarse en un cache-hit")

    monkeypatch.setattr(
        pokemon_api, "search_cards_in_set", fake_search_cards_in_set_que_no_debe_llamarse
    )

    segunda = client.get("/sets/fossil/cards")

    assert segunda.status_code == 200
    assert segunda.json() == primer_body


def test_cartas_de_un_set_no_mezcla_cartas_cacheadas_por_otra_via(client, monkeypatch):
    """Una carta que ya está en `cards` con el mismo set_id, pero que llegó
    ahí vía /cards/search (no está en `set_cards_cache` para este set), no
    debe aparecer en la respuesta de este endpoint."""
    conn = queries.get_connection()
    try:
        queries.upsert_card(
            conn,
            {
                "id": "gym1-50",
                "name": "Carta de búsqueda previa",
                "set_id": "gym1",
                "set_name": "Gym Heroes",
                "number": "50",
                "rarity": "Common",
                "image_url": "https://example.com/gym1-50.png",
            },
        )
    finally:
        conn.close()

    def fake_search_cards_in_set(set_id, *args, **kwargs):
        return [_carta_simplificada("gym1-1", "Misty's Wartortle")]

    monkeypatch.setattr(pokemon_api, "search_cards_in_set", fake_search_cards_in_set)

    response = client.get("/sets/gym1/cards")

    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body}
    assert ids == {"gym1-1"}
    assert "gym1-50" not in ids

    def fake_search_cards_in_set_que_no_debe_llamarse(set_id, *args, **kwargs):
        pytest.fail("search_cards_in_set no debe llamarse en un cache-hit")

    monkeypatch.setattr(
        pokemon_api, "search_cards_in_set", fake_search_cards_in_set_que_no_debe_llamarse
    )

    segunda = client.get("/sets/gym1/cards")

    assert segunda.status_code == 200
    segundo_body = segunda.json()
    segundos_ids = {item["id"] for item in segundo_body}
    assert segundos_ids == {"gym1-1"}
    assert "gym1-50" not in segundos_ids
