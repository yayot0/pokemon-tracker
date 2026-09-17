"""
routers/cards.py
Endpoints para buscar cartas, ver su detalle+precio actual, y su historial.
"""
from datetime import date

from fastapi import APIRouter, HTTPException

from app.db import queries
from app.services import pokemon_api
from app.services.pokemon_api import PokemonAPIError
from app.models.schemas import CardSearchResult, CardDetail, PriceSnapshotOut

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/search", response_model=list[CardSearchResult])
def search(q: str):
    """
    Busca cartas. Primero revisa el caché local (instantáneo); si no
    encuentra nada ahí, le pega a la API externa (más lento) y guarda
    los resultados nuevos en caché para la próxima vez.
    """
    conn = queries.get_connection()
    cached = queries.search_cached_cards(conn, q)

    if cached:
        conn.close()
        return [CardSearchResult(**dict(row)) for row in cached]

    try:
        results = pokemon_api.search_cards(q)
    except PokemonAPIError as exc:
        conn.close()
        raise HTTPException(status_code=503, detail=str(exc))

    for card in results:
        queries.upsert_card(conn, card)
    conn.close()

    return results


@router.get("/{card_id}", response_model=CardDetail)
def get_card_detail(card_id: str):
    """
    Trae el detalle de una carta y su precio actual. Cada vez que se
    consulta, se guarda un snapshot de precio con la fecha de hoy —
    así es como se va construyendo el historial con el tiempo.
    """
    try:
        card_json = pokemon_api.get_card(card_id)
    except PokemonAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if card_json is None:
        raise HTTPException(status_code=404, detail="Carta no encontrada")

    simplified = pokemon_api._simplify_card(card_json)
    tcgplayer_market, cardmarket_avg = pokemon_api.extract_prices(card_json)

    conn = queries.get_connection()
    queries.upsert_card(conn, simplified)
    queries.insert_price_snapshot(
        conn, card_id, date.today().isoformat(), tcgplayer_market, cardmarket_avg
    )
    conn.close()

    return CardDetail(
        id=simplified["id"],
        name=simplified["name"],
        set_name=simplified["set_name"],
        image_url=simplified["image_url"],
        rarity=simplified["rarity"],
        tcgplayer_market=tcgplayer_market,
        cardmarket_avg=cardmarket_avg,
    )


@router.get("/{card_id}/history", response_model=list[PriceSnapshotOut])
def get_history(card_id: str):
    """Historial completo de precios guardados para esta carta."""
    conn = queries.get_connection()
    rows = queries.get_price_history(conn, card_id)
    conn.close()
    return [PriceSnapshotOut(**dict(row)) for row in rows]