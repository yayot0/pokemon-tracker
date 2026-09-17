export default function CardGridSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse rounded-xl border border-border bg-surface p-3"
        >
          <div className="mb-2 aspect-[3/4] w-full rounded-md bg-surface-alt" />
          <div className="mb-1 h-3 w-3/4 rounded bg-surface-alt" />
          <div className="h-2.5 w-1/2 rounded bg-surface-alt" />
        </div>
      ))}
    </div>
  );
}