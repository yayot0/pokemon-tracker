"""
test_cards.py
Tests del router app/routers/cards.py: búsqueda (cache-first), detalle de
una carta (con snapshot de precio diario) e historial de precios.
"""
from app.db import queries
from app.services import pokemon_api
from app.services.pokemon_api import PokemonAPIError


def _carta_simplificada(card_id="base1-4", name="Charizard"):
    """Shape que devuelve `pokemon_api._simplify_card` (y por lo tanto
    `pokemon_api.search_cards`/`search_cards_in_set`)."""
    return {
        "id": card_id,
        "name": name,
        "set_id": "base1",
        "set_name": "Base Set",
        "number": "4",
        "rarity": "Rare Holo",
        "image_url": "https://example.com/charizard.png",
    }


def _card_json_externo(card_id="base1-4", name="Charizard", market=350.5, avg=300.0):
    """Shape del JSON crudo que devolvería la API externa para una carta
    (lo que recibe `_simplify_card`/`extract_prices` dentro del router)."""
    return {
        "id": card_id,
        "name": name,
        "number": "4",
        "rarity": "Rare Holo",
        "set": {"id": "base1", "name": "Base Set"},
        "images": {"small": "https://example.com/charizard.png"},
        "tcgplayer": {"prices": {"holofoil": {"market": market}}},
        "cardmarket": {"prices": {"averageSellPrice": avg}},
    }


def _insertar_carta_en_cache(card_id="base1-4", name="Charizard"):
    """Inserta una carta directamente en la tabla `cards`, simulando que ya
    se consultó/buscó antes."""
    conn = queries.get_connection()
    try:
        queries.upsert_card(conn, _carta_simplificada(card_id, name))
    finally:
        conn.close()


def _insertar_snapshot(card_id, date, tcgplayer_market, cardmarket_avg):
    conn = queries.get_connection()
    try:
        queries.insert_price_snapshot(conn, card_id, date, tcgplayer_market, cardmarket_avg)
    finally:
        conn.close()


# ------------------------------------------------------------
# GET /cards/search
# ------------------------------------------------------------

def test_buscar_cartas_con_cache_miss_llama_a_la_api_y_guarda_en_cache(client, monkeypatch):
    """Sin nada en el caché local, debe pegarle a `pokemon_api.search_cards`
    y guardar el resultado en la tabla `cards` para la próxima vez."""
    llamadas = []

    def fake_search_cards(query, *args, **kwargs):
        llamadas.append(query)
        return [_carta_simplificada()]

    monkeypatch.setattr(pokemon_api, "search_cards", fake_search_cards)

    response = client.get("/cards/search", params={"q": "charizard"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "base1-4"
    assert body[0]["name"] == "Charizard"
    assert len(llamadas) == 1


def test_buscar_cartas_con_cache_hit_no_llama_a_la_api(client, monkeypatch):
    """Regla cache-first: si la carta ya está en caché local, la segunda
    búsqueda no debe volver a llamar a `pokemon_api.search_cards`."""
    _insertar_carta_en_cache()

    llamadas = []

    def fake_search_cards(query, *args, **kwargs):
        llamadas.append(query)
        return [_carta_simplificada()]

    monkeypatch.setattr(pokemon_api, "search_cards", fake_search_cards)

    response = client.get("/cards/search", params={"q": "charizard"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "base1-4"
    assert llamadas == []


def test_buscar_cartas_guarda_en_cache_tras_un_miss(client, monkeypatch):
    """Tras un cache miss, el resultado se guarda en `cards`: una segunda
    búsqueda igual ya no debe llamar a la API externa."""
    llamadas = []

    def fake_search_cards(query, *args, **kwargs):
        llamadas.append(query)
        return [_carta_simplificada()]

    monkeypatch.setattr(pokemon_api, "search_cards", fake_search_cards)

    primera = client.get("/cards/search", params={"q": "charizard"})
    segunda = client.get("/cards/search", params={"q": "charizard"})

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert len(llamadas) == 1


def test_buscar_cartas_con_error_de_api_responde_503(client, monkeypatch):
    """Si `pokemon_api.search_cards` lanza PokemonAPIError (cache miss),
    el endpoint debe traducirlo a un 503."""

    def fake_search_cards(query, *args, **kwargs):
        raise PokemonAPIError("la API externa no respondió")

    monkeypatch.setattr(pokemon_api, "search_cards", fake_search_cards)

    response = client.get("/cards/search", params={"q": "charizard"})

    assert response.status_code == 503
    assert "no respondió" in response.json()["detail"]


def test_buscar_cartas_sin_query_responde_422(client):
    """`q` es un parámetro requerido del endpoint; omitirlo es un 422."""
    response = client.get("/cards/search")

    assert response.status_code == 422


# ------------------------------------------------------------
# GET /cards/{card_id}
# ------------------------------------------------------------

def test_detalle_de_carta_responde_200_y_guarda_snapshot(client, monkeypatch):
    """Caso feliz: trae el detalle de la carta y guarda un snapshot de
    precio del día de hoy."""

    def fake_get_card(card_id):
        assert card_id == "base1-4"
        return _card_json_externo()

    monkeypatch.setattr(pokemon_api, "get_card", fake_get_card)

    response = client.get("/cards/base1-4")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "base1-4"
    assert body["name"] == "Charizard"
    assert body["set_name"] == "Base Set"
    assert body["rarity"] == "Rare Holo"
    assert body["tcgplayer_market"] == 350.5
    assert body["cardmarket_avg"] == 300.0

    historial = client.get("/cards/base1-4/history").json()
    assert len(historial) == 1
    assert historial[0]["tcgplayer_market"] == 350.5


def test_detalle_de_carta_inexistente_responde_404(client, monkeypatch):
    """Si `pokemon_api.get_card` devuelve None (la API no encontró la
    carta), el endpoint responde 404."""

    def fake_get_card(card_id):
        return None

    monkeypatch.setattr(pokemon_api, "get_card", fake_get_card)

    response = client.get("/cards/no-existe-1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Carta no encontrada"


def test_detalle_de_carta_con_error_de_api_responde_503(client, monkeypatch):
    """Si `pokemon_api.get_card` lanza PokemonAPIError, el endpoint
    responde 503."""

    def fake_get_card(card_id):
        raise PokemonAPIError("la API externa no respondió")

    monkeypatch.setattr(pokemon_api, "get_card", fake_get_card)

    response = client.get("/cards/base1-4")

    assert response.status_code == 503
    assert "no respondió" in response.json()["detail"]


def test_consultar_misma_carta_dos_veces_el_mismo_dia_no_duplica_snapshot(client, monkeypatch):
    """Regla de negocio: UNIQUE(card_id, date) + INSERT OR REPLACE implica
    que consultar la misma carta dos veces el mismo día deja un solo
    registro en price_snapshots (se actualiza, no se duplica)."""

    def fake_get_card(card_id):
        return _card_json_externo(market=350.5, avg=300.0)

    monkeypatch.setattr(pokemon_api, "get_card", fake_get_card)

    client.get("/cards/base1-4")
    client.get("/cards/base1-4")

    historial = client.get("/cards/base1-4/history").json()
    assert len(historial) == 1


# ------------------------------------------------------------
# GET /cards/{card_id}/history
# ------------------------------------------------------------

def test_historial_de_precios_vacio_devuelve_lista_vacia(client):
    """Caso feliz: una carta sin snapshots devuelve []."""
    response = client.get("/cards/base1-4/history")

    assert response.status_code == 200
    assert response.json() == []


def test_historial_de_precios_devuelve_ordenado_por_fecha_ascendente(client):
    """`get_price_history` ordena por fecha ASC; el endpoint debe
    reflejarlo tal cual (del snapshot más viejo al más nuevo)."""
    _insertar_carta_en_cache()
    _insertar_snapshot("base1-4", "2024-06-01", 150.0, 140.0)
    _insertar_snapshot("base1-4", "2024-01-01", 100.0, 90.0)

    response = client.get("/cards/base1-4/history")

    assert response.status_code == 200
    body = response.json()
    assert [item["date"] for item in body] == ["2024-01-01", "2024-06-01"]
    assert body[0]["tcgplayer_market"] == 100.0
    assert body[1]["tcgplayer_market"] == 150.0
