"""
schemas.py
Modelos Pydantic: definen cómo se ve cada request/response de la API.
"""
from pydantic import BaseModel


class SetOut(BaseModel):
    id: str
    name: str
    series: str | None = None
    release_date: str | None = None
    logo_url: str | None = None
    symbol_url: str | None = None


class CardSearchResult(BaseModel):
    id: str
    name: str
    set_id: str | None = None
    set_name: str | None = None
    number: str | None = None
    rarity: str | None = None
    image_url: str | None = None


class PriceSnapshotOut(BaseModel):
    date: str
    tcgplayer_market: float | None = None
    cardmarket_avg: float | None = None


class CardDetail(BaseModel):
    id: str
    name: str
    set_name: str | None = None
    image_url: str | None = None
    rarity: str | None = None
    tcgplayer_market: float | None = None
    cardmarket_avg: float | None = None


class CollectionItemIn(BaseModel):
    card_id: str
    quantity: int = 1
    condition: str = "Near Mint"
    acquired_date: str | None = None
    acquired_price: float | None = None
    notes: str | None = None


class CollectionItemUpdate(BaseModel):
    quantity: int
    condition: str


class CollectionItemOut(BaseModel):
    id: int
    card_id: str
    name: str
    set_name: str | None = None
    image_url: str | None = None
    quantity: int
    condition: str
    acquired_price: float | None = None
    acquired_date: str | None = None
    current_price: float | None = None