import type { ReactElement } from 'react'
import type { PropertyLink } from '../../../types/domain'

export interface PropertyLinkListProps {
  propertyLinks?: PropertyLink[] | undefined
  portalDisplayName: string
  portalNameLower: string
  isLoading?: boolean | undefined
}

export function PropertyLinkList({
  propertyLinks = [],
  portalDisplayName,
  portalNameLower,
  isLoading = false,
}: PropertyLinkListProps): ReactElement | null {
  if (isLoading) {
    return (
      <div
        id={`property-links-loading-${portalNameLower}`}
        className="mt-3.5 pt-3 border-t border-dashed border-zinc-200 dark:border-zinc-800/60 flex flex-col gap-2.5"
      >
        <span className="h-2.5 w-1/3 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800 mb-1"></span>
        {[1, 2, 3].map((j) => (
          <div key={j} className="flex items-center gap-2">
            <div className="h-5 w-5 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
            <div className="h-3 flex-1 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!propertyLinks || propertyLinks.length === 0) {
    return null
  }

  // Display up to 5 property links
  const linksToShow = propertyLinks.slice(0, 5)

  return (
    <div
      id={`property-links-${portalNameLower}`}
      className="mt-3.5 pt-3 border-t border-dashed border-zinc-200 dark:border-zinc-800/60 flex flex-col gap-2"
    >
      <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 block mb-1">
        Top Listings Found
      </span>
      <div className="flex flex-col gap-2">
        {linksToShow.map((link) => (
          <a
            key={link.url}
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            id={`property-link-${portalNameLower}-${link.rank}`}
            className="flex items-center gap-2 group/link text-xs text-zinc-600 hover:text-brand-500 dark:text-zinc-400 dark:hover:text-brand-400 transition-colors duration-150"
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-zinc-100 dark:bg-zinc-800 text-[10px] font-bold text-zinc-500 dark:text-zinc-400 group-hover/link:bg-brand-500 group-hover/link:text-white transition-colors duration-150">
              {link.rank}
            </span>
            <span className="truncate flex-1 hover:underline">
              View Property #{link.rank} on {portalDisplayName}
            </span>
            <svg
              className="h-3 w-3 shrink-0 opacity-0 group-hover/link:opacity-100 transition-opacity duration-150"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
            </svg>
          </a>
        ))}
      </div>
    </div>
  )
}
