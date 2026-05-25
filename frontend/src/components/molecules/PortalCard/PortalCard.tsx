import type { ReactElement } from 'react'
import type { PortalResult } from '../../../types/domain'

export interface PortalCardProps {
  card: PortalResult
}

export function PortalCard({ card }: PortalCardProps): ReactElement {
  const { portal, label, summary, url, isPriority, notes } = card

  // Determine brand colors and labels dynamically
  const getPortalDetails = (portalName: string) => {
    const nameLower = portalName.toLowerCase()
    switch (nameLower) {
      case 'nobroker':
        return {
          displayName: 'NoBroker',
          dotColor: 'bg-[var(--color-portal-nobroker-green)]',
          textColor: 'text-[var(--color-portal-nobroker-green)]',
          badgeBg: 'bg-[var(--color-portal-nobroker-green)]/10 dark:bg-[var(--color-portal-nobroker-green)]/20',
          badgeBorder: 'border-[var(--color-portal-nobroker-green)]/30',
          ctaBg: 'bg-[var(--color-portal-nobroker-green)] hover:bg-[var(--color-portal-nobroker-green)]/90 shadow-[0_0_12px_rgba(16,185,129,0.2)]',
          focusRing: 'focus:ring-[var(--color-portal-nobroker-green)]',
        }
      case '99acres':
        return {
          displayName: '99acres',
          dotColor: 'bg-[var(--color-portal-acres-blue)]',
          textColor: 'text-[var(--color-portal-acres-blue)]',
          badgeBg: 'bg-[var(--color-portal-acres-blue)]/10 dark:bg-[var(--color-portal-acres-blue)]/20',
          badgeBorder: 'border-[var(--color-portal-acres-blue)]/30',
          ctaBg: 'bg-[var(--color-portal-acres-blue)] hover:bg-[var(--color-portal-acres-blue)]/90 shadow-[0_0_12px_rgba(2,132,199,0.2)]',
          focusRing: 'focus:ring-[var(--color-portal-acres-blue)]',
        }
      case 'magicbricks':
        return {
          displayName: 'MagicBricks',
          dotColor: 'bg-[var(--color-portal-magicbricks)]',
          textColor: 'text-[var(--color-portal-magicbricks)]',
          badgeBg: 'bg-[var(--color-portal-magicbricks)]/10 dark:bg-[var(--color-portal-magicbricks)]/20',
          badgeBorder: 'border-[var(--color-portal-magicbricks)]/30',
          ctaBg: 'bg-[var(--color-portal-magicbricks)] hover:bg-[var(--color-portal-magicbricks)]/90 shadow-[0_0_12px_rgba(42,157,143,0.2)]',
          focusRing: 'focus:ring-[var(--color-portal-magicbricks)]',
        }
      case 'housing':
        return {
          displayName: 'Housing.com',
          dotColor: 'bg-[var(--color-portal-housing)]',
          textColor: 'text-[var(--color-portal-housing)]',
          badgeBg: 'bg-[var(--color-portal-housing)]/10 dark:bg-[var(--color-portal-housing)]/20',
          badgeBorder: 'border-[var(--color-portal-housing)]/30',
          ctaBg: 'bg-[var(--color-portal-housing)] hover:bg-[var(--color-portal-housing)]/90 shadow-[0_0_12px_rgba(69,123,157,0.2)]',
          focusRing: 'focus:ring-[var(--color-portal-housing)]',
        }
      case 'squareyards':
        return {
          displayName: 'Square Yards',
          dotColor: 'bg-[var(--color-portal-squareyards)]',
          textColor: 'text-[var(--color-portal-squareyards)]',
          badgeBg: 'bg-[var(--color-portal-squareyards)]/10 dark:bg-[var(--color-portal-squareyards)]/20',
          badgeBorder: 'border-[var(--color-portal-squareyards)]/30',
          ctaBg: 'bg-[var(--color-portal-squareyards)] hover:bg-[var(--color-portal-squareyards)]/90 shadow-[0_0_12px_rgba(106,76,147,0.2)]',
          focusRing: 'focus:ring-[var(--color-portal-squareyards)]',
        }
      default:
        return {
          displayName: portalName.charAt(0).toUpperCase() + portalName.slice(1),
          dotColor: 'bg-zinc-400',
          textColor: 'text-zinc-600 dark:text-zinc-400',
          badgeBg: 'bg-zinc-100 dark:bg-zinc-800',
          badgeBorder: 'border-zinc-200 dark:border-zinc-700',
          ctaBg: 'bg-zinc-700 hover:bg-zinc-800 focus:ring-zinc-500',
          focusRing: 'focus:ring-zinc-500',
        }
    }
  }

  const details = getPortalDetails(portal)

  // Priority Badge Custom Label
  const getPriorityLabel = (portalName: string) => {
    const nameLower = portalName.toLowerCase()
    if (nameLower === 'nobroker') return 'Best for Rent'
    if (nameLower === '99acres') return 'Best for Buy'
    return 'Priority Choice'
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
      </div>
    </div>
  )
}
