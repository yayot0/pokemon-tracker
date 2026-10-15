"""
routers/collection.py
Endpoints para manejar tu colección personal de cartas.
"""
from fastapi import APIRouter, HTTPException

from app.db import queries
from app.models.schemas import CollectionItemIn, CollectionItemOut, CollectionItemUpdate

router = APIRouter(prefix="/collection", tags=["collection"])


@router.post("", status_code=201)
def add_item(item: CollectionItemIn):
    """
    Agrega una carta a tu colección. La carta debe existir ya en el
    caché (normalmente porque la buscaste/consultaste antes con
    GET /cards/{id}), si no, la operación falla por la llave foránea.
    """
    conn = queries.get_connection()
    try:
        if queries.get_card(conn, item.card_id) is None:
            raise HTTPException(
                status_code=400,
                detail="Esa carta no está en el caché todavía. Consúltala primero con GET /cards/{id}.",
            )

        new_id = queries.add_to_collection(
            conn,
            card_id=item.card_id,
            quantity=item.quantity,
            condition=item.condition,
            acquired_date=item.acquired_date,
            acquired_price=item.acquired_price,
            notes=item.notes,
        )
        return {"id": new_id, "status": "ok"}
    finally:
        conn.close()


@router.get("", response_model=list[CollectionItemOut])
def list_collection():
    conn = queries.get_connection()
    try:
        rows = queries.get_collection(conn)
    finally:
        conn.close()
    return [CollectionItemOut(**dict(row)) for row in rows]


@router.patch("/{item_id}")
def update_item(item_id: int, payload: CollectionItemUpdate):
    conn = queries.get_connection()
    try:
        updated = queries.update_collection_item(conn, item_id, payload.quantity, payload.condition)
    finally:
        conn.close()
    if not updated:
        raise HTTPException(status_code=404, detail="No existe esa entrada en tu colección")
    return {"status": "ok"}


@router.delete("/{item_id}", status_code=204)
def remove_item(item_id: int):
    conn = queries.get_connection()
    try:
        deleted = queries.delete_collection_item(conn, item_id)
    finally:
        conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="No existe esa entrada en tu colección")