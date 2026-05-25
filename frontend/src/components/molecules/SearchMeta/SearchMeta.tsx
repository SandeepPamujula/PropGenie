import type { ReactElement } from 'react'

export interface SearchMetaProps {
  portalsSearched: number
  portalsReturned: number
  defaultsApplied?: string[]
  portalsDropped?: string[]
}

export function SearchMeta({
  portalsSearched,
  portalsReturned,
  defaultsApplied = [],
  portalsDropped = [],
}: SearchMetaProps): ReactElement {
  // Helper to format technical default strings into user-friendly notes
  const formatDefaultApplied = (def: string): string => {
    const d = def.trim().toLowerCase()
    if (d === 'radius_km: 4' || d === 'radius_km:4') {
      return '4 km radius search applied'
    }
    if (d === 'budget_min: 0' || d === 'budget_min:0') {
      return 'Budget floor assumed as ₹0'
    }
    return def
  }

  const formattedDefaults = defaultsApplied.map(formatDefaultApplied)

  return (
    <div
      id="search-meta-container"
      className="flex flex-col gap-2 mt-3.5 px-1 py-2 w-full max-w-2xl border-t border-zinc-200/50 dark:border-zinc-800/40"
    >
      {/* Summary count bar */}
      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-zinc-500 dark:text-zinc-400">
        <svg className="h-4 w-4 text-zinc-400 dark:text-zinc-500" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 15.75l-2.489-2.489m0 0a3.375 3.375 0 10-4.773-4.773 3.375 3.375 0 004.774 4.774zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span id="search-meta-counts">
          Searched {portalsSearched} portal{portalsSearched === 1 ? '' : 's'} · {portalsReturned} result{portalsReturned === 1 ? '' : 's'}
        </span>

        {portalsDropped.length > 0 && (
          <span id="search-meta-dropped" className="text-[10px] text-zinc-400 dark:text-zinc-500 font-normal">
            ({portalsDropped.length} empty or invalid results dropped)
          </span>
        )}
      </div>

      {/* Defaults applied listed as subtle notes */}
      {formattedDefaults.length > 0 && (
        <div id="search-meta-defaults" className="flex flex-wrap gap-x-3 gap-y-1.5 mt-0.5">
          {formattedDefaults.map((note, idx) => (
            <div
              key={idx}
              className="flex items-center gap-1.5 text-[10px] text-zinc-400 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-850 px-2 py-0.5 rounded border border-zinc-200/40 dark:border-zinc-850/40 font-medium"
            >
              <span className="h-1 w-1 rounded-full bg-zinc-400 dark:bg-zinc-500"></span>
              <span>{note}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
