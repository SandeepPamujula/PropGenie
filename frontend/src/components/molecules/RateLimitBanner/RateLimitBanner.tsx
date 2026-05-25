import type { ReactElement } from 'react'

export interface RateLimitBannerProps {
  maxSearches?: number
  resetTimeIST?: string
}

/**
 * Calculates the next midnight in Indian Standard Time (IST, UTC+5:30)
 * formatted as "12:00 AM IST on YYYY-MM-DD".
 */
export function getISTResetTimeString(): string {
  const now = new Date()
  const utcTime = now.getTime() + now.getTimezoneOffset() * 60000
  const istDate = new Date(utcTime + 3600000 * 5.5)

  const nextMidnightIST = new Date(istDate)
  nextMidnightIST.setHours(24, 0, 0, 0)

  const year = nextMidnightIST.getFullYear()
  const month = String(nextMidnightIST.getMonth() + 1).padStart(2, '0')
  const date = String(nextMidnightIST.getDate()).padStart(2, '0')

  return `12:00 AM IST on ${year}-${month}-${date}`
}

export function RateLimitBanner({
  maxSearches = 10,
  resetTimeIST,
}: RateLimitBannerProps): ReactElement {
  const formattedResetTime = resetTimeIST || getISTResetTimeString()

  return (
    <div
      id="rate-limit-banner"
      role="alert"
      aria-live="polite"
      className="flex items-start gap-3.5 rounded-2xl border border-amber-200/60 bg-amber-50/75 p-4 shadow-sm backdrop-blur-md dark:border-amber-900/40 dark:bg-amber-950/20 w-full animate-fade-in transition-all duration-300"
    >
      {/* Clock Icon */}
      <div className="flex h-5 w-5 shrink-0 items-center justify-center text-amber-600 dark:text-amber-400">
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
            d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
          />
        </svg>
      </div>

      {/* Warning Content */}
      <div className="flex flex-col gap-1 pr-1 min-w-0 text-sm">
        <span
          id="rate-limit-banner-text"
          className="font-semibold text-amber-900 dark:text-amber-200"
        >
          You&apos;ve reached your daily search limit of {maxSearches}. Please try again tomorrow!
        </span>
        <span
          id="rate-limit-banner-reset-time"
          className="text-xs font-medium text-amber-800/80 dark:text-amber-300/80"
        >
          Next reset: {formattedResetTime}
        </span>
      </div>
    </div>
  )
}
