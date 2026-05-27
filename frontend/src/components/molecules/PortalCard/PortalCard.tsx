import type { ReactElement } from 'react'
import type { PortalResult } from '../../../types/domain'
import { PORTAL_CONFIG, PRIORITY_LABELS } from '../../../lib/constants'

export interface PortalCardProps {
  card: PortalResult
}

export function PortalCard({ card }: PortalCardProps): ReactElement {
  const { portal, label, summary, url, isPriority, notes, propertyLinks } = card

  // Determine brand colors and labels dynamically
  const getPortalDetails = (portalName: string) => {
    const nameLower = portalName.toLowerCase() as keyof typeof PORTAL_CONFIG
    return PORTAL_CONFIG[nameLower] || PORTAL_CONFIG.default
  }

  const details = getPortalDetails(portal)

  // Priority Badge Custom Label
  const getPriorityLabel = (portalName: string) => {
    const nameLower = portalName.toLowerCase()
    return PRIORITY_LABELS[nameLower] || PRIORITY_LABELS.default
  }

  return (
    <div
      id={`portal-card-${portal.toLowerCase()}`}
      className="glass-card flex flex-col justify-between p-4 rounded-xl shadow-sm hover:-translate-y-1 hover:shadow-md transition-all duration-300 w-full"
    >
      <div>
        {/* Header containing Portal Badge and Priority Badge */}
        <div className="flex items-center justify-between mb-3 w-full">
          <div
            id={`portal-badge-${portal.toLowerCase()}`}
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${details.badgeBg} ${details.badgeBorder} ${details.textColor}`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${details.dotColor} animate-pulse-slow`}></span>
            <span>{details.displayName}</span>
          </div>

          {isPriority && (
            <div
              id={`priority-badge-${portal.toLowerCase()}`}
              className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wide bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 text-amber-700 dark:text-amber-300"
            >
              <svg className="h-3 w-3 shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.562.562 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.562.562 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
              <span>{getPriorityLabel(portal)}</span>
            </div>
          )}
        </div>

        {/* Label & Summary */}
        <h4
          id={`portal-card-label-${portal.toLowerCase()}`}
          className="text-sm font-bold text-zinc-800 dark:text-zinc-200 line-clamp-1 leading-snug"
        >
          {label}
        </h4>
        <p
          id={`portal-card-summary-${portal.toLowerCase()}`}
          className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 line-clamp-2 leading-relaxed"
        >
          {summary}
        </p>

        {/* Notes for defaults applied */}
        {notes && (
          <div
            id={`portal-card-notes-${portal.toLowerCase()}`}
            className="mt-2.5 flex items-start gap-1 text-[10px] text-zinc-400 dark:text-zinc-500 italic leading-snug"
          >
            <svg className="h-3 w-3 shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 111.063.852l-.708 2.836a.75.75 0 001.063.852l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
            <span>{notes}</span>
          </div>
        )}
      </div>

      {/* Prominent CTA Link */}
      <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          id={`cta-button-${portal.toLowerCase()}`}
          className={`flex items-center justify-center gap-1.5 w-full rounded-lg px-3.5 py-2 text-xs font-bold text-white transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-zinc-900 ${details.ctaBg} ${details.focusRing}`}
        >
          <span>View on {details.displayName}</span>
          <svg className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </a>

        {/* Property Links Section */}
        {propertyLinks && propertyLinks.length > 0 && (
          <div
            id={`property-links-${portal.toLowerCase()}`}
            className="mt-3.5 pt-3 border-t border-dashed border-zinc-200 dark:border-zinc-800/60 flex flex-col gap-2"
          >
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 block mb-1">
              Top Listings Found
            </span>
            <div className="flex flex-col gap-2">
              {propertyLinks.map((link) => (
                <a
                  key={link.url}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  id={`property-link-${portal.toLowerCase()}-${link.rank}`}
                  className="flex items-center gap-2 group/link text-xs text-zinc-600 hover:text-brand-500 dark:text-zinc-400 dark:hover:text-brand-400 transition-colors duration-150"
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-zinc-100 dark:bg-zinc-800 text-[10px] font-bold text-zinc-500 dark:text-zinc-400 group-hover/link:bg-brand-500 group-hover/link:text-white transition-colors duration-150">
                    {link.rank}
                  </span>
                  <span className="truncate flex-1 hover:underline">
                    View Property #{link.rank} on {details.displayName}
                  </span>
                  <svg className="h-3 w-3 shrink-0 opacity-0 group-hover/link:opacity-100 transition-opacity duration-150" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                  </svg>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
