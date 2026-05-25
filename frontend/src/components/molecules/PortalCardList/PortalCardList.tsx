import type { ReactElement } from 'react'
import type { PortalResult } from '../../../types/domain'
import { PortalCard } from '../PortalCard/PortalCard'

export interface PortalCardListProps {
  cards: PortalResult[]
}

export function PortalCardList({ cards }: PortalCardListProps): ReactElement {
  // Sort cards so that priority cards are rendered first
  const sortedCards = [...cards].sort((a, b) => {
    const aPriority = a.isPriority ? 1 : 0
    const bPriority = b.isPriority ? 1 : 0
    return bPriority - aPriority
  })

  return (
    <div
      id="portal-card-list"
      className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2.5 w-full max-w-2xl"
    >
      {sortedCards.map((card, idx) => (
        <div
          key={`${card.portal}-${idx}`}
          className="flex w-full animate-fade-in"
          style={{
            animationDelay: `${idx * 100}ms`,
            animationFillMode: 'both',
          }}
        >
          <PortalCard card={card} />
        </div>
      ))}
    </div>
  )
}
