import { useState } from "react";
import { deleteCollectionItem, updateCollectionItem } from "../api/client";

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

function CollectionCard({ item, onChange }) {
  const [editing, setEditing] = useState(false);
  const [quantity, setQuantity] = useState(item.quantity);
  const [condition, setCondition] = useState(item.condition);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const gain =
    item.current_price != null && item.acquired_price != null
      ? item.current_price - item.acquired_price
      : null;

  async function handleSave() {
    setSaving(true);
    try {
      await updateCollectionItem(item.id, { quantity: Number(quantity), condition });
      setEditing(false);
      onChange?.();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteCollectionItem(item.id);
      onChange?.();
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="flex gap-3 rounded-xl border border-border bg-surface p-3">
      {item.image_url && (
        <img
          src={item.image_url}
          alt={item.name}
          className="h-24 w-20 shrink-0 rounded-md object-cover"
        />
      )}
      <div className="flex-1">
        <p className="font-display font-semibold text-text">{item.name}</p>
        <p className="text-xs text-text-muted">{item.set_name}</p>

        {editing ? (
          <div className="mt-2 space-y-1.5">
            <div className="flex gap-2">
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="w-16 rounded-md border border-border bg-ink px-2 py-1 text-sm text-text"
              />
              <select
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                className="flex-1 rounded-md border border-border bg-ink px-2 py-1 text-sm text-text"
              >
                {CONDITIONS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="rounded-md bg-gold px-3 py-1 text-xs font-display font-semibold text-ink disabled:opacity-50"
              >
                {saving ? "Guardando…" : "Guardar"}
              </button>
              <button
                onClick={() => setEditing(false)}
                disabled={saving}
                className="rounded-md border border-border px-3 py-1 text-xs text-text-muted"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <>
            <p className="mt-1 text-xs text-text-muted">
              {item.condition} · x{item.quantity}
            </p>

            <div className="mt-2 flex items-center gap-4 text-sm">
              <span className="font-mono text-text-muted">
                pagado: {formatUSD(item.acquired_price)}
              </span>
              <span className="font-mono text-gold">actual: {formatUSD(item.current_price)}</span>
            </div>

            {gain != null && (
              <p className={`mt-1 font-mono text-sm ${gain >= 0 ? "text-gain" : "text-loss"}`}>
                {gain >= 0 ? "+" : ""}
                {formatUSD(gain)}
              </p>
            )}

            <div className="mt-2 flex gap-3 text-xs">
              <button onClick={() => setEditing(true)} className="text-text-muted hover:text-gold">
                editar
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-text-muted hover:text-loss disabled:opacity-50"
              >
                {deleting ? "quitando…" : "quitar"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function CollectionList({ items, loading, onChange }) {
  if (loading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 animate-pulse rounded-xl border border-border bg-surface" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <p className="text-text-muted">
        Todavía no tienes cartas en tu colección. Busca una carta y agrégala.
      </p>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {items.map((item) => (
        <CollectionCard key={item.id} item={item} onChange={onChange} />
      ))}
    </div>
  );
}