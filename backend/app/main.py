"""
main.py
Correr con: uvicorn app.main:app --reload   (desde la carpeta backend/)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import cards, collection, browse

app = FastAPI(title="Pokémon Card Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(browse.router)
app.include_router(cards.router)
app.include_router(collection.router)


@app.get("/health")
def health():
    return {"status": "ok"}