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
    try:
        rows = queries.get_recently_viewed(conn)
    finally:
        conn.close()
    return [CardSearchResult(**dict(row)) for row in rows]


@router.get("/sets", response_model=list[SetOut])
def list_sets():
    """
    Sets para explorar. Cache-first, igual que la búsqueda de cartas:
    si ya los consultamos antes, regresa del caché local (instantáneo).
    """
    conn = queries.get_connection()
    try:
        cached = queries.get_cached_sets(conn)

        if cached:
            return [SetOut(**dict(row)) for row in cached]

        try:
            sets_data = pokemon_api.get_sets()
        except PokemonAPIError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

        for s in sets_data:
            queries.upsert_set(conn, s)

        return sets_data
    finally:
        conn.close()


@router.get("/sets/{set_id}/cards", response_model=list[CardSearchResult])
def cards_in_set(set_id: str):
    """
    Cartas de un set específico. Cache-first: si ya guardamos qué
    cartas devolvió la API para este set, se sirven desde 'cards'
    sin pegarle a la API externa.
    """
    conn = queries.get_connection()
    try:
        cached = queries.get_cached_set_cards(conn, set_id)
        if cached:
            return [CardSearchResult(**dict(row)) for row in cached]

        try:
            results = pokemon_api.search_cards_in_set(set_id)
        except PokemonAPIError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

        for card in results:
            queries.upsert_card(conn, card)
            queries.mark_set_card_cached(conn, set_id, card["id"])

        return [CardSearchResult(**dict(row)) for row in queries.get_cached_set_cards(conn, set_id)]
    finally:
        conn.close()