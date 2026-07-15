import { Skeleton } from '@/components/ui/Skeleton'

export default function LoadingScreen({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-surface)]">
      <div className="flex flex-col items-center gap-6 animate-fade-in w-full max-w-xs px-6">
        <div className="w-full space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-4 w-3/4 mx-auto" />
          <Skeleton className="h-4 w-1/2 mx-auto" />
        </div>
        <p className="text-sm text-[var(--color-text-muted)]" role="status">
          {message}
        </p>
      </div>
    </div>
  )
}
