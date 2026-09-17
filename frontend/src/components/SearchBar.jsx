import { useState } from "react";

export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Buscar una carta… ej. Charizard"
        className="flex-1 rounded-lg border border-border bg-surface px-4 py-2.5 text-text placeholder:text-text-muted focus:border-gold focus:outline-none"
      />
      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-gold px-5 py-2.5 font-display font-semibold text-ink disabled:opacity-50"
      >
        {loading ? "Buscando…" : "Buscar"}
      </button>
    </form>
  );
}