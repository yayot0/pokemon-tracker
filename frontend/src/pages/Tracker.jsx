import { useEffect, useState, useCallback } from "react";
import { searchCards, getCollection, getSetCards } from "../api/client";
import SearchBar from "../components/SearchBar";
import CardGrid from "../components/CardGrid";
import CardGridSkeleton from "../components/CardGridSkeleton";
import CardDetailPanel from "../components/CardDetailPanel";
import CollectionList from "../components/CollectionList";
import Home from "../components/Home";

export default function Tracker() {
  const [tab, setTab] = useState("search"); // 'search' | 'collection'
  // view: 'home' | 'results' | 'set' | 'detail'
  const [view, setView] = useState("home");
  const [results, setResults] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [collection, setCollection] = useState([]);
  const [collectionLoading, setCollectionLoading] = useState(true);

  const loadCollection = useCallback(() => {
    setCollectionLoading(true);
    getCollection()
      .then(setCollection)
      .catch(() => {})
      .finally(() => setCollectionLoading(false));
  }, []);

  useEffect(() => {
    loadCollection();
  }, [loadCollection]);

  async function handleSearch(query) {
    setLoading(true);
    setError(null);
    setView("results");
    try {
      const data = await searchCards(query);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectSet(setId) {
    setLoading(true);
    setError(null);
    setView("set");
    try {
      const data = await getSetCards(setId);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSelectCard(cardId) {
    setSelectedId(cardId);
    setView("detail");
  }

  function handleBack() {
    setSelectedId(null);
    setView("home");
  }

  return (
    <div className="min-h-screen bg-ink text-text">
      <header className="border-b border-border px-6 py-4 sm:px-10">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <button
            onClick={() => {
              setTab("search");
              setView("home");
            }}
            className="font-display text-xl font-semibold"
          >
            <span className="text-gold">✦</span> Card Tracker
          </button>
          <nav className="flex gap-1 rounded-lg border border-border bg-surface p-1">
            <button
              onClick={() => setTab("search")}
              className={`rounded-md px-3 py-1.5 text-sm font-display ${
                tab === "search" ? "bg-gold text-ink" : "text-text-muted"
              }`}
            >
              Buscar
            </button>
            <button
              onClick={() => setTab("collection")}
              className={`rounded-md px-3 py-1.5 text-sm font-display ${
                tab === "collection" ? "bg-gold text-ink" : "text-text-muted"
              }`}
            >
              Mi colección ({collection.length})
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-6 py-8 sm:px-10">
        {tab === "search" && (
          <>
            <SearchBar onSearch={handleSearch} loading={loading} />
            {error && <p className="text-loss">{error}</p>}

            {view === "detail" && selectedId && (
              <CardDetailPanel cardId={selectedId} onClose={handleBack} onAdded={loadCollection} />
            )}

            {view === "home" && (
              <Home onSelectCard={handleSelectCard} onSelectSet={handleSelectSet} />
            )}

            {(view === "results" || view === "set") &&
              (loading ? (
                <CardGridSkeleton />
              ) : (
                <>
                  <button onClick={handleBack} className="text-sm text-text-muted hover:text-text">
                    ← volver a inicio
                  </button>
                  {results.length === 0 && !error ? (
                    <p className="text-text-muted">No encontré cartas.</p>
                  ) : (
                    <CardGrid cards={results} onSelect={handleSelectCard} />
                  )}
                </>
              ))}
          </>
        )}

        {tab === "collection" && (
          <CollectionList items={collection} loading={collectionLoading} onChange={loadCollection} />
        )}
      </main>
    </div>
  );
}