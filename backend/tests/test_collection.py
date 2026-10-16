"""
test_collection.py
Tests del router app/routers/collection.py: agregar, listar, actualizar
y eliminar cartas de la colección personal del usuario.
"""
from app.db import queries


def _insertar_carta_en_cache(card_id="base1-4"):
    """Inserta una carta directamente en la tabla `cards` (caché), como si
    ya se hubiera consultado antes con GET /cards/{id}."""
    conn = queries.get_connection()
    try:
        queries.upsert_card(
            conn,
            {
                "id": card_id,
                "name": "Charizard",
                "set_id": "base1",
                "set_name": "Base Set",
                "number": "4/102",
                "rarity": "Rare Holo",
                "image_url": "https://example.com/charizard.png",
            },
        )
    finally:
        conn.close()


def _insertar_snapshot(card_id, date, tcgplayer_market, cardmarket_avg):
    conn = queries.get_connection()
    try:
        queries.insert_price_snapshot(conn, card_id, date, tcgplayer_market, cardmarket_avg)
    finally:
        conn.close()


def test_agregar_carta_a_la_coleccion_responde_201(client):
    """Caso feliz: agregar una carta que ya está en el caché."""
    _insertar_carta_en_cache()

    response = client.post(
        "/collection",
        json={
            "card_id": "base1-4",
            "quantity": 2,
            "condition": "Near Mint",
            "acquired_date": "2024-01-15",
            "acquired_price": 120.0,
            "notes": "Comprada en torneo local",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["id"], int)


def test_agregar_carta_no_cacheada_responde_400(client):
    """Si la carta no está en el caché de `cards`, la operación falla por
    la regla de negocio explícita del router (no por FK de sqlite)."""
    response = client.post(
        "/collection",
        json={"card_id": "base1-999", "quantity": 1, "condition": "Near Mint"},
    )

    assert response.status_code == 400
    assert "caché" in response.json()["detail"]


def test_agregar_carta_con_condicion_invalida_responde_422(client):
    """`condition` debe ser uno de los valores del Literal en schemas.py."""
    _insertar_carta_en_cache()

    response = client.post(
        "/collection",
        json={"card_id": "base1-4", "quantity": 1, "condition": "Como Nueva"},
    )

    assert response.status_code == 422


def test_listar_coleccion_vacia_devuelve_lista_vacia(client):
    """Caso feliz: sin cartas en la colección, GET devuelve []."""
    response = client.get("/collection")

    assert response.status_code == 200
    assert response.json() == []


def test_listar_coleccion_incluye_precio_actual_mas_reciente(client):
    """
    get_collection hace un JOIN con `cards` y una subquery correlacionada
    a price_snapshots que trae el precio más reciente por fecha. Con dos
    snapshots de distintas fechas, debe devolver el de la fecha más
    reciente, no el primero insertado.
    """
    _insertar_carta_en_cache()
    _insertar_snapshot("base1-4", "2024-01-01", 100.0, 90.0)
    _insertar_snapshot("base1-4", "2024-06-01", 150.0, 140.0)

    client.post(
        "/collection",
        json={"card_id": "base1-4", "quantity": 1, "condition": "Mint", "acquired_price": 80.0},
    )

    response = client.get("/collection")

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    item = items[0]
    assert item["card_id"] == "base1-4"
    assert item["name"] == "Charizard"
    assert item["set_name"] == "Base Set"
    assert item["quantity"] == 1
    assert item["condition"] == "Mint"
    assert item["acquired_price"] == 80.0
    assert item["current_price"] == 150.0


def test_actualizar_item_de_coleccion_responde_200(client):
    """Caso feliz: PATCH actualiza quantity y condition de una entrada
    existente."""
    _insertar_carta_en_cache()
    crear = client.post(
        "/collection",
        json={"card_id": "base1-4", "quantity": 1, "condition": "Near Mint"},
    )
    item_id = crear.json()["id"]

    response = client.patch(
        f"/collection/{item_id}",
        json={"quantity": 5, "condition": "Lightly Played"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    listado = client.get("/collection").json()
    actualizado = next(i for i in listado if i["id"] == item_id)
    assert actualizado["quantity"] == 5
    assert actualizado["condition"] == "Lightly Played"


def test_actualizar_item_inexistente_responde_404(client):
    """No existe ninguna entrada con ese id en `collection`."""
    response = client.patch(
        "/collection/9999",
        json={"quantity": 1, "condition": "Mint"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No existe esa entrada en tu colección"


def test_actualizar_item_con_condicion_invalida_responde_422(client):
    """Validación de entrada: condition fuera del Literal permitido."""
    _insertar_carta_en_cache()
    crear = client.post(
        "/collection",
        json={"card_id": "base1-4", "quantity": 1, "condition": "Near Mint"},
    )
    item_id = crear.json()["id"]

    response = client.patch(
        f"/collection/{item_id}",
        json={"quantity": 1, "condition": "Perfecta"},
    )

    assert response.status_code == 422


def test_eliminar_item_de_coleccion_responde_204(client):
    """Caso feliz: DELETE quita la entrada y ya no aparece en el listado."""
    _insertar_carta_en_cache()
    crear = client.post(
        "/collection",
        json={"card_id": "base1-4", "quantity": 1, "condition": "Near Mint"},
    )
    item_id = crear.json()["id"]

    response = client.delete(f"/collection/{item_id}")

    assert response.status_code == 204
    assert client.get("/collection").json() == []


def test_eliminar_item_inexistente_responde_404(client):
    """No existe ninguna entrada con ese id en `collection`."""
    response = client.delete("/collection/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "No existe esa entrada en tu colección"
