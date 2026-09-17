# Backend — Pokémon Card Tracker

API en FastAPI que consulta la API de pokemontcg.io, cachea resultados,
guarda historial de precios, y maneja la colección personal.

## Estructura

```
backend/
├── app/
│   ├── main.py
│   ├── db/
│   │   ├── schema.sql        # Esquema (SQL puro)
│   │   └── queries.py        # Todas las queries del proyecto
│   ├── services/
│   │   └── pokemon_api.py    # Cliente de la API externa (con reintentos)
│   ├── models/
│   │   └── schemas.py        # Modelos Pydantic
│   └── routers/
│       ├── cards.py          # Búsqueda y detalle de cartas
│       ├── collection.py     # Colección personal
│       └── browse.py         # Pantalla de inicio: recién vistas + sets
└── data/
    └── pokemon.db             # Se genera localmente (no se sube a git)
```

## Instalación

```bash
cd backend
pip install -r requirements.txt --break-system-packages
```

## Crear la base de datos

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/pokemon.db')
conn.executescript(open('app/db/schema.sql').read())
conn.close()
"
```

## API key (opcional)

La API de pokemontcg.io está deprecada y ya no acepta cuentas nuevas.
El proyecto funciona sin key (límites más bajos). Si tienes una key
existente, créala en `backend/.env`:

```
POKEMONTCG_API_KEY=tu_key
```

## Correr el servidor

```bash
python3 -m uvicorn app.main:app --reload
```

Debe correrse desde `backend/` (no desde `app/` ni `data/`). API en
`http://127.0.0.1:8000`, docs interactivas en `/docs`.

## Endpoints

| Método | Ruta                    | Descripción                              |
|--------|-------------------------|--------------------------------------------|
| GET    | `/health`               | Health check                                |
| GET    | `/cards/search?q=`      | Busca cartas (caché local primero)          |
| GET    | `/cards/recent`         | Últimas cartas consultadas                  |
| GET    | `/cards/{id}`           | Detalle + guarda snapshot de precio de hoy  |
| GET    | `/cards/{id}/history`   | Historial de precios de una carta           |
| GET    | `/sets`                 | Sets disponibles (caché local primero)      |
| GET    | `/sets/{id}/cards`      | Cartas de un set específico                 |
| POST   | `/collection`           | Agrega una carta a tu colección             |
| GET    | `/collection`           | Lista tu colección con valor actual         |
| PATCH  | `/collection/{id}`      | Edita cantidad/condición                    |
| DELETE | `/collection/{id}`      | Quita una carta de tu colección             |