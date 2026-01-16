/**
 * Skeleton loading component for anime cards
 */
export default function AnimeCardSkeleton() {
  return (
    <div className="relative group animate-pulse">
      {/* Image skeleton */}
      <div className="aspect-[2/3] w-full bg-gray-200 rounded-lg overflow-hidden" />

      {/* Title skeleton */}
      <div className="mt-2 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-3 bg-gray-200 rounded w-1/2" />
      </div>

      {/* Rating skeleton */}
      <div className="mt-2 flex items-center gap-1">
        <div className="h-4 w-16 bg-gray-200 rounded" />
      </div>
    </div>
  );
}
