interface Props {
  className?: string
}

export function Skeleton({ className = '' }: Props) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-[var(--color-border-subtle)]/60 ${className}`}
      aria-hidden
    />
  )
}

export function ChatSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-4 max-w-3xl mx-auto w-full" aria-label="Loading messages">
      <div className="flex gap-3 justify-end">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-8 w-8 rounded-xl shrink-0" />
      </div>
      <div className="flex gap-3">
        <Skeleton className="h-8 w-8 rounded-xl shrink-0" />
        <Skeleton className="h-24 w-3/4" />
      </div>
      <div className="flex gap-3 justify-end">
        <Skeleton className="h-10 w-56" />
        <Skeleton className="h-8 w-8 rounded-xl shrink-0" />
      </div>
      <div className="flex gap-3">
        <Skeleton className="h-8 w-8 rounded-xl shrink-0" />
        <Skeleton className="h-16 w-2/3" />
      </div>
    </div>
  )
}

export function SessionListSkeleton() {
  return (
    <div className="flex flex-col gap-2 px-1" aria-label="Loading chats">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-9 w-full" />
      ))}
    </div>
  )
}

export function DocumentListSkeleton() {
  return (
    <div className="flex flex-col gap-2 p-4" aria-label="Loading documents">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  )
}
