const BASE_URL = "http://127.0.0.1:8000";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Ocurrió un error al hablar con el backend");
  }
  return res.json();
}

export async function getRecentlyViewed() {
  const res = await fetch(`${BASE_URL}/cards/recent`);
  return handle(res);
}

export async function getSets() {
  const res = await fetch(`${BASE_URL}/sets`);
  return handle(res);
}

export async function getSetCards(setId) {
  const res = await fetch(`${BASE_URL}/sets/${setId}/cards`);
  return handle(res);
}

export async function searchCards(query) {
  const res = await fetch(`${BASE_URL}/cards/search?q=${encodeURIComponent(query)}`);
  return handle(res);
}

export async function getCardDetail(cardId) {
  const res = await fetch(`${BASE_URL}/cards/${cardId}`);
  return handle(res);
}

export async function getCardHistory(cardId) {
  const res = await fetch(`${BASE_URL}/cards/${cardId}/history`);
  return handle(res);
}

export async function addToCollection(payload) {
  const res = await fetch(`${BASE_URL}/collection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

export async function getCollection() {
  const res = await fetch(`${BASE_URL}/collection`);
  return handle(res);
}

export async function updateCollectionItem(itemId, payload) {
  const res = await fetch(`${BASE_URL}/collection/${itemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

export async function deleteCollectionItem(itemId) {
  const res = await fetch(`${BASE_URL}/collection/${itemId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("No se pudo eliminar");
}