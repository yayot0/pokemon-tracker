export default function CardGrid({ cards, onSelect }) {
  if (cards.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {cards.map((card) => (
        <button
          key={card.id}
          onClick={() => onSelect(card.id)}
          className="group rounded-xl border border-border bg-surface p-3 text-left transition-colors hover:border-gold"
        >
          {card.image_url && (
            <img
              src={card.image_url}
              alt={card.name}
              className="mb-2 w-full rounded-md"
              loading="lazy"
            />
          )}
          <p className="truncate font-display text-sm font-semibold text-text">{card.name}</p>
          <p className="truncate text-xs text-text-muted">{card.set_name}</p>
        </button>
      ))}
    </div>
  );
}