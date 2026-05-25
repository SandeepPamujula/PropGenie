import type { ReactElement } from 'react'

export interface ErrorMessageProps {
  message: string
  retryable?: boolean
  onRetry?: () => void
}

export function ErrorMessage({
  message,
  retryable = false,
  onRetry,
}: ErrorMessageProps): ReactElement {
  const containerClasses = retryable
    ? 'border-orange-200/60 bg-orange-50/75 dark:border-orange-900/40 dark:bg-orange-950/20 text-orange-900 dark:text-orange-200'
    : 'border-red-200/60 bg-red-50/75 dark:border-red-900/40 dark:bg-red-950/20 text-red-900 dark:text-red-200'

  const iconClasses = retryable
    ? 'text-orange-600 dark:text-orange-400'
    : 'text-red-600 dark:text-red-400'

  return (
    <div
      id="error-message"
      role="alert"
      aria-live="assertive"
      className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border p-4 shadow-sm backdrop-blur-md w-full animate-fade-in transition-all duration-300 ${containerClasses}`}
    >
      <div className="flex items-start gap-3.5">
        <div className={`flex h-5 w-5 shrink-0 items-center justify-center ${iconClasses}`}>
          {retryable ? (
            // Warning Icon
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          ) : (
            // Critical / Stop Icon
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          )}
        </div>
        <div className="flex flex-col justify-center min-w-0 text-sm">
          <span id="error-message-text" className="font-semibold leading-relaxed">
            {message}
          </span>
        </div>
      </div>
      
      {retryable && onRetry && (
        <button
          id="retry-search-button"
          onClick={onRetry}
          className="shrink-0 rounded-xl bg-orange-100 px-4 py-2 text-sm font-medium text-orange-700 transition-colors hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-500/50 dark:bg-orange-900/50 dark:text-orange-200 dark:hover:bg-orange-900/70"
        >
          Retry Search
        </button>
      )}
    </div>
  )
}
