import type { ReactElement } from 'react'

export interface ClarificationMessageProps {
  question: string
  round: number
  maxRounds?: number | undefined
  resolvedFields?: Record<string, unknown> | undefined
}

export function ClarificationMessage({
  question,
  round,
  maxRounds = 3,
  resolvedFields = {},
}: ClarificationMessageProps): ReactElement {
  // Helper to format field names and values nicely
  const formatResolvedField = (
    key: string,
    value: unknown,
  ): { label: string; val: string } | null => {
    if (value === undefined || value === null || value === '') {
      return null
    }

    const formatKey = (k: string) => {
      switch (k) {
        case 'intent':
          return 'Intent'
        case 'city':
          return 'City'
        case 'location_anchor':
          return 'Locality'
        case 'property_type':
          return 'Type'
        case 'bhk':
          return 'BHK'
        case 'budget_min':
          return 'Min Budget'
        case 'budget_max':
          return 'Max Budget'
        case 'radius_km':
          return 'Radius'
        default:
          return k.replace('_', ' ')
      }
    }

    const formatVal = (k: string, v: unknown) => {
      const strVal = String(v)
      if (k === 'bhk') {
        return `${strVal} BHK`
      }
      if (k === 'intent') {
        return strVal === 'rent' ? 'Rent' : strVal === 'buy' ? 'Buy' : strVal
      }
      if (k === 'radius_km') {
        return `${strVal} km`
      }
      if (k === 'budget_min' || k === 'budget_max') {
        const num = Number(v)
        if (isNaN(num)) return strVal
        if (num >= 10000000) return `₹${(num / 10000000).toFixed(1)} Cr`
        if (num >= 100000) return `₹${(num / 100000).toFixed(1)} L`
        if (num >= 1000) return `₹${(num / 1000).toFixed(0)} K`
        return `₹${num}`
      }
      // Capitalize standard text values
      return strVal.charAt(0).toUpperCase() + strVal.slice(1)
    }

    return {
      label: formatKey(key),
      val: formatVal(key, value),
    }
  }

  const chips = Object.entries(resolvedFields)
    .map(([key, val]) => formatResolvedField(key, val))
    .filter((chip): chip is { label: string; val: string } => chip !== null)

  return (
    <div
      id="clarification-message"
      className="flex flex-col gap-3 rounded-2xl border border-amber-500/20 bg-amber-50/20 p-4 shadow-sm dark:border-amber-500/30 dark:bg-amber-900/10 w-full animate-fade-in"
    >
      <div className="flex items-center justify-between border-b border-amber-500/10 pb-2 dark:border-amber-500/20">
        <span
          id="clarification-round-indicator"
          className="text-xs font-semibold text-amber-800 dark:text-amber-300"
        >
          Clarification Round {round} of {maxRounds}
        </span>
        <span className="flex h-2 w-2 rounded-full bg-amber-500 animate-pulse-slow"></span>
      </div>

      <p
        id="clarification-question-text"
        className="text-sm font-medium leading-relaxed text-zinc-800 dark:text-zinc-100"
      >
        {question}
      </p>

      {/* Resolved fields list */}
      {chips.length > 0 && (
        <div id="clarification-resolved-section" className="flex flex-col gap-1.5 pt-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
            Resolved Parameters
          </span>
          <div id="clarification-chips-container" className="flex flex-wrap gap-1.5">
            {chips.map((chip, idx) => (
              <div
                key={idx}
                className="flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border border-zinc-200/50 dark:border-zinc-700/50"
              >
                <span className="font-semibold text-zinc-400 dark:text-zinc-500">
                  {chip.label}:
                </span>
                <span>{chip.val}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
