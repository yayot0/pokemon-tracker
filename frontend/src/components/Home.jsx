import { useEffect, useState } from "react";
import { getRecentlyViewed, getSets } from "../api/client";

export default function Home({ onSelectCard, onSelectSet }) {
  const [recent, setRecent] = useState([]);
  const [sets, setSets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getRecentlyViewed().catch(() => []), getSets().catch(() => [])]).then(
      ([recentData, setsData]) => {
        setRecent(recentData);
        setSets(setsData);
        setLoading(false);
      }
    );
  }, []);

  if (loading) {
    return <p className="text-text-muted">Cargando…</p>;
  }

  return (
    <div className="space-y-8">
      {recent.length > 0 && (
        <section>
          <p className="mb-3 font-display text-sm font-semibold text-text-muted">
            Tus últimas vistas
          </p>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {recent.map((card) => (
              <button
                key={card.id}
                onClick={() => onSelectCard(card.id)}
                className="w-24 shrink-0 text-left"
              >
                {card.image_url && (
                  <img src={card.image_url} alt={card.name} className="mb-1 rounded-md" />
                )}
                <p className="truncate text-xs text-text-muted">{card.name}</p>
              </button>
            ))}
          </div>
        </section>
      )}

      <section>
        <p className="mb-1 font-display text-sm font-semibold text-text-muted">
          Sets para explorar
        </p>
        <p className="mb-3 text-xs text-text-muted">
          Según lo que tiene disponible esta API — puede no incluir lo más reciente.
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {sets.map((set) => (
            <button
              key={set.id}
              onClick={() => onSelectSet(set.id)}
              className="flex flex-col items-center gap-2 rounded-xl border border-border bg-surface p-4 hover:border-gold"
            >
              {set.logo_url && (
                <img src={set.logo_url} alt={set.name} className="h-10 object-contain" />
              )}
              <p className="text-center text-xs font-display text-text">{set.name}</p>
              <p className="text-[10px] text-text-muted">{set.release_date}</p>
            </button>
          ))}
        </div>
      </section>

      {recent.length === 0 && sets.length === 0 && (
        <p className="text-text-muted">Busca una carta para empezar a explorar.</p>
      )}
    </div>
  );
}