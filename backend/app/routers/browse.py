"""
routers/browse.py
Endpoints para la pantalla de inicio: cartas recién vistas y sets
para explorar (con caché local, mismo patrón que la búsqueda de cartas).
"""
from fastapi import APIRouter, HTTPException

from app.db import queries
from app.services import pokemon_api
from app.services.pokemon_api import PokemonAPIError
from app.models.schemas import CardSearchResult, SetOut

router = APIRouter(tags=["browse"])


@router.get("/cards/recent", response_model=list[CardSearchResult])
def recent_cards():
    """Últimas cartas que consultaste, para 'tus últimas vistas'."""
    conn = queries.get_connection()
    rows = queries.get_recently_viewed(conn)
    conn.close()
    return [CardSearchResult(**dict(row)) for row in rows]


@router.get("/sets", response_model=list[SetOut])
def list_sets():
    """
    Sets para explorar. Cache-first, igual que la búsqueda de cartas:
    si ya los consultamos antes, regresa del caché local (instantáneo).
    """
    conn = queries.get_connection()
    cached = queries.get_cached_sets(conn)

    if cached:
        conn.close()
        return [SetOut(**dict(row)) for row in cached]

    try:
        sets_data = pokemon_api.get_sets()
    except PokemonAPIError as exc:
        conn.close()
        raise HTTPException(status_code=503, detail=str(exc))

    for s in sets_data:
        queries.upsert_set(conn, s)
    conn.close()

    return sets_data


@router.get("/sets/{set_id}/cards", response_model=list[CardSearchResult])
def cards_in_set(set_id: str):
    """Cartas de un set específico, para cuando le das clic a un set."""
    try:
        results = pokemon_api.search_cards_in_set(set_id)
    except PokemonAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    conn = queries.get_connection()
    for card in results:
        queries.upsert_card(conn, card)
    conn.close()

    return results