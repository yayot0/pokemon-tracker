import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { getCardDetail, getCardHistory, addToCollection } from "../api/client";

const CONDITIONS = [
  "Mint",
  "Near Mint",
  "Lightly Played",
  "Moderately Played",
  "Heavily Played",
  "Damaged",
];

function formatUSD(n) {
  if (n == null) return "—";
  return `$${n.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
}

export default function CardDetailPanel({ cardId, onClose, onAdded }) {
  const [card, setCard] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    quantity: 1,
    condition: "Near Mint",
    acquired_date: "",
    acquired_price: "",
    notes: "",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setSaved(false);
    Promise.all([getCardDetail(cardId), getCardHistory(cardId)])
      .then(([cardData, historyData]) => {
        setCard(cardData);
        setHistory(historyData);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [cardId]);

  async function handleAdd(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await addToCollection({
        card_id: cardId,
        quantity: Number(form.quantity) || 1,
        condition: form.condition,
        acquired_date: form.acquired_date || null,
        acquired_price: form.acquired_price ? Number(form.acquired_price) : null,
        notes: form.notes || null,
      });
      setSaved(true);
      onAdded?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <button onClick={onClose} className="mb-4 text-sm text-text-muted hover:text-text">
        ← volver a resultados
      </button>

      {loading && <p className="text-text-muted">Cargando…</p>}
      {error && <p className="text-loss">{error}</p>}

      {card && !loading && (
        <div className="grid gap-6 sm:grid-cols-[180px_1fr]">
          {card.image_url && (
            <img src={card.image_url} alt={card.name} className="w-full rounded-lg" />
          )}

          <div>
            <p className="font-display text-2xl font-semibold text-text">{card.name}</p>
            <p className="mb-3 text-sm text-text-muted">
              {card.set_name} · {card.rarity}
            </p>

            <div className="mb-4 flex gap-6">
              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">TCGPlayer</p>
                <p className="font-mono text-xl text-gold">{formatUSD(card.tcgplayer_market)}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">Cardmarket</p>
                <p className="font-mono text-xl text-gold">
                  {card.cardmarket_avg != null ? `€${card.cardmarket_avg.toFixed(2)}` : "—"}
                </p>
              </div>
            </div>

            {history.length > 1 && (
              <div className="mb-4 h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid stroke="#33366A" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fill: "#8B8FB0", fontSize: 11 }} />
                    <YAxis tick={{ fill: "#8B8FB0", fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: "#181A38", border: "1px solid #33366A" }}
                      labelStyle={{ color: "#EDEAE0" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="tcgplayer_market"
                      stroke="#D4AF37"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            <form onSubmit={handleAdd} className="space-y-2 border-t border-border pt-4">
              <p className="font-display text-sm font-semibold text-text">Agregar a mi colección</p>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  min="1"
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                  placeholder="Cantidad"
                  className="rounded-md border border-border bg-ink px-2 py-1.5 text-sm text-text"
                />
                <select
                  value={form.condition}
                  onChange={(e) => setForm({ ...form, condition: e.target.value })}
                  className="rounded-md border border-border bg-ink px-2 py-1.5 text-sm text-text"
                >
                  {CONDITIONS.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
                <input
                  type="date"
                  value={form.acquired_date}
                  onChange={(e) => setForm({ ...form, acquired_date: e.target.value })}
                  className="rounded-md border border-border bg-ink px-2 py-1.5 text-sm text-text"
                />
                <input
                  type="number"
                  step="0.01"
                  value={form.acquired_price}
                  onChange={(e) => setForm({ ...form, acquired_price: e.target.value })}
                  placeholder="Precio pagado"
                  className="rounded-md border border-border bg-ink px-2 py-1.5 text-sm text-text"
                />
              </div>
              <input
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Notas (opcional)"
                className="w-full rounded-md border border-border bg-ink px-2 py-1.5 text-sm text-text"
              />
              <button
                type="submit"
                disabled={saving}
                className="w-full rounded-md bg-gold py-2 text-sm font-display font-semibold text-ink disabled:opacity-50"
              >
                {saving ? "Guardando…" : saved ? "¡Agregada! Agregar otra copia" : "Agregar"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}