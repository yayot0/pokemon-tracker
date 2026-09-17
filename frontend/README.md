# Frontend — Pokémon Card Tracker

Interfaz en React. Identidad visual tipo "carpeta de cartas": fondo azul
oscuro, acentos dorados, tipografía Space Grotesk para títulos.

## Estructura

```
frontend/
└── src/
    ├── api/
    │   └── client.js
    ├── components/
    │   ├── SearchBar.jsx
    │   ├── CardGrid.jsx
    │   ├── CardGridSkeleton.jsx
    │   ├── CardDetailPanel.jsx
    │   ├── CollectionList.jsx
    │   └── Home.jsx
    └── pages/
        └── Tracker.jsx
```

## Instalación y desarrollo

```bash
npm install
npm run dev
```

Abre `http://localhost:5173`. El backend debe estar corriendo en
`http://127.0.0.1:8000` al mismo tiempo.

## Build de producción

```bash
npm run build
```