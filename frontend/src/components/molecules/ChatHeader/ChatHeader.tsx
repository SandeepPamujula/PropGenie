import type { ReactElement } from 'react'

export interface ChatHeaderProps {
  currentSearches?: number
  maxSearches?: number
}

export function ChatHeader({
  currentSearches = 0,
  maxSearches = 50,
}: ChatHeaderProps): ReactElement {
  return (
    <div id="chat-header" className="flex w-full items-center justify-between px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        {/* Animated Brand Logo */}
        <div
          id="chat-header-logo"
          className="flex h-10 w-10 shrink-0 select-none items-center justify-center rounded-xl bg-gradient-to-tr from-brand-500 to-brand-900 font-sans text-lg font-extrabold tracking-tight text-white shadow-md shadow-brand-500/20 transition-transform duration-300 hover:scale-105"
        >
          PG
        </div>
        <div>
          <h1
            id="chat-header-title"
            className="font-sans text-base sm:text-lg font-bold tracking-tight text-zinc-900 dark:text-zinc-50"
          >
            PropGenie
          </h1>
          <p
            id="chat-header-tagline"
            className="font-sans text-[11px] sm:text-xs text-zinc-500 dark:text-zinc-400"
          >
            Find your perfect property with AI
          </p>
        </div>
      </div>

      {/* Daily Search Counter Badge */}
      <div
        id="search-counter-badge"
        className="flex items-center gap-1.5 rounded-full border border-brand-500/20 bg-brand-50/50 px-2.5 py-1 text-xs font-semibold text-brand-900 dark:border-brand-500/30 dark:bg-brand-900/20 dark:text-brand-50"
      >
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-500 opacity-75"></span>
          <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-500"></span>
        </span>
        <span id="search-counter-text">
          {currentSearches} of {maxSearches} searches used today
        </span>
      </div>
    </div>
  )
}
