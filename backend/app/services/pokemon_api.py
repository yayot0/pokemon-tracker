"""
pokemon_api.py
Habla con la API pública de pokemontcg.io (https://pokemontcg.io/) para
buscar cartas y obtener sus precios actuales de TCGPlayer y Cardmarket.

Esta API está deprecada (ya no acepta cuentas nuevas), así que se usa
sin API key. Eso implica límites de uso más bajos y respuestas a veces
lentas o intermitentes - por eso cada request tiene reintentos.
"""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.pokemontcg.io/v2"
API_KEY = os.getenv("POKEMONTCG_API_KEY")
HEADERS = {"X-Api-Key": API_KEY} if API_KEY else {}


class PokemonAPIError(Exception):
    """La API externa no respondió a tiempo o regresó un error del servidor."""


def _get_with_retries(url, params, attempts=3, timeout=20):
    """
    Le pega a la API con hasta 3 intentos antes de rendirse, con una
    pequeña espera entre cada uno. La API pública sin key a veces falla
    de forma intermitente, no siempre está caída de verdad.
    """
    last_error = None
    for attempt in range(attempts):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(1.5)
    raise PokemonAPIError(
        "La API de pokemontcg.io no respondió después de varios intentos. Intenta de nuevo en un momento."
    ) from last_error


def search_cards(query, page=1, page_size=40):
    """
    Busca cartas por nombre. El wildcard en ambos lados (*query*) encuentra
    coincidencias en cualquier parte del nombre, no solo al inicio -
    así 'Greninja' también encuentra 'Ash-Greninja-EX'.
    """
    params = {"q": f"name:*{query}*", "page": page, "pageSize": page_size}
    resp = _get_with_retries(f"{BASE_URL}/cards", params)
    data = resp.json().get("data", [])
    return [_simplify_card(card) for card in data]


def get_card(card_id):
    """Trae el detalle completo de una carta específica por su id."""
    resp = _get_with_retries(f"{BASE_URL}/cards/{card_id}", params=None)
    return resp.json().get("data")


def search_cards_in_set(set_id, page_size=20):
    """
    Trae las cartas de un set específico. page_size más chico que en la
    búsqueda normal para que la respuesta sea más rápida - esta consulta
    es de las más pesadas para la API.
    """
    params = {"q": f"set.id:{set_id}", "pageSize": page_size, "orderBy": "number"}
    resp = _get_with_retries(f"{BASE_URL}/cards", params)
    data = resp.json().get("data", [])
    return [_simplify_card(card) for card in data]


def get_sets(page_size=12):
    """
    Trae los sets ordenados del más reciente al más viejo (según lo que
    tenga esta API, que puede no incluir lo último que salió en tiendas).
    """
    params = {"orderBy": "-releaseDate", "pageSize": page_size}
    resp = _get_with_retries(f"{BASE_URL}/sets", params)
    data = resp.json().get("data", [])
    return [_simplify_set(s) for s in data]


def extract_prices(card_json):
    """
    El JSON de pokemontcg.io trae los precios de TCGPlayer separados por
    'finish' (normal, holofoil, reverseHolofoil, etc.) y no todas las
    cartas tienen todos los finishes. Esta función toma el primer precio
    'market' que encuentre como representativo, y el promedio de Cardmarket.
    Regresa (None, None) si la carta no tiene datos de precio todavía.
    """
    tcgplayer_market = None
    tcgplayer_prices = (card_json.get("tcgplayer") or {}).get("prices") or {}
    for finish_data in tcgplayer_prices.values():
        if finish_data.get("market") is not None:
            tcgplayer_market = finish_data["market"]
            break

    cardmarket_prices = (card_json.get("cardmarket") or {}).get("prices") or {}
    cardmarket_avg = cardmarket_prices.get("averageSellPrice")

    return tcgplayer_market, cardmarket_avg


def _simplify_set(set_json):
    images = set_json.get("images", {}) or {}
    return {
        "id": set_json["id"],
        "name": set_json.get("name"),
        "series": set_json.get("series"),
        "release_date": set_json.get("releaseDate"),
        "logo_url": images.get("logo"),
        "symbol_url": images.get("symbol"),
    }


def _simplify_card(card_json):
    return {
        "id": card_json["id"],
        "name": card_json["name"],
        "set_id": card_json.get("set", {}).get("id"),
        "set_name": card_json.get("set", {}).get("name"),
        "number": card_json.get("number"),
        "rarity": card_json.get("rarity"),
        "image_url": card_json.get("images", {}).get("small"),
    }