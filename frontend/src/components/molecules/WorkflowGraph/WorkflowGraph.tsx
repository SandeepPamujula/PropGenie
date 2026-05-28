import { useState, useEffect, type ReactElement } from 'react'

export type AgentPhase =
  | 'orchestrator'
  | 'clarification'
  | 'query_builder'
  | 'url_validator'
  | 'property_scraper'
  | 'response_formatter'
  | 'complete'

export interface WorkflowGraphProps {
  currentPhase: AgentPhase
}

type NodeStatus = 'idle' | 'active' | 'completed' | 'skipped'

interface NodeConfig {
  id: string
  label: string
  icon: (color: string) => ReactElement
  x: number // percentage left
  y: number // percentage top
}

export function WorkflowGraph({ currentPhase }: WorkflowGraphProps): ReactElement {
  const [visited, setVisited] = useState<string[]>(['restore_state'])

  useEffect(() => {
    if (currentPhase) {
      setVisited((prev) => {
        // Map 'complete' phase to save_state completion
        const phaseName = currentPhase === 'complete' ? 'save_state' : currentPhase
        if (!prev.includes(phaseName)) {
          return [...prev, phaseName]
        }
        return prev
      })
    }
  }, [currentPhase])

  // Reset visited path if starting a new run
  useEffect(() => {
    if (currentPhase === 'orchestrator') {
      setVisited(['restore_state', 'orchestrator'])
    }
  }, [currentPhase])

  // Determine status of each node
  const getNodeStatus = (nodeId: string): NodeStatus => {
    const activeId = currentPhase === 'complete' ? 'save_state' : currentPhase

    if (nodeId === 'restore_state') {
      return 'completed'
    }

    if (nodeId === 'orchestrator') {
      if (activeId === 'orchestrator') return 'active'
      return visited.includes('orchestrator') ? 'completed' : 'idle'
    }

    if (nodeId === 'clarification') {
      if (activeId === 'clarification') return 'active'
      if (visited.includes('query_builder')) return 'skipped'
      return visited.includes('clarification') ? 'completed' : 'idle'
    }

    if (nodeId === 'query_builder') {
      if (activeId === 'query_builder') return 'active'
      if (visited.includes('clarification')) return 'skipped'
      return visited.includes('query_builder') ? 'completed' : 'idle'
    }

    // Pipeline nodes
    if (['url_validator', 'property_scraper', 'response_formatter'].includes(nodeId)) {
      if (activeId === nodeId) return 'active'
      if (visited.includes('clarification')) return 'skipped'
      return visited.includes(nodeId) ? 'completed' : 'idle'
    }

    if (nodeId === 'save_state') {
      if (activeId === 'save_state') return 'active'
      return visited.includes('save_state') ? 'completed' : 'idle'
    }

    return 'idle'
  }

  // Helper to determine color schemes for nodes based on status
  const getNodeClasses = (status: NodeStatus): string => {
    switch (status) {
      case 'active':
        return 'border-sky-500 bg-sky-500/10 text-sky-600 dark:border-sky-500 dark:bg-sky-500/20 dark:text-sky-400 font-extrabold animate-pulse-slow shadow-md shadow-sky-500/15'
      case 'completed':
        return 'border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:border-emerald-500 dark:bg-emerald-500/15 dark:text-emerald-400 font-medium'
      case 'skipped':
        return 'border-zinc-200 bg-zinc-100/30 text-zinc-300 dark:border-zinc-800/40 dark:bg-zinc-900/10 dark:text-zinc-600 line-through opacity-40'
      case 'idle':
      default:
        return 'border-zinc-200 bg-zinc-50/40 text-zinc-400 dark:border-zinc-800/60 dark:bg-zinc-950/20 dark:text-zinc-500'
    }
  }

  // Database restore icon
  const databaseIcon = (color: string) => (
    <svg className={`h-3.5 w-3.5 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  )

  // Brain/Orchestrator icon
  const brainIcon = (color: string) => (
    <svg className={`h-3.5 w-3.5 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  )

  // Chat/Clarification question bubble icon
  const questionIcon = (color: string) => (
    <svg className={`h-3.5 w-3.5 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )

  // Hammer/Query Builder icon
  const buildIcon = (color: string) => (
    <svg className={`h-3.5 w-3.5 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )

  // Shield Check/URL Validator icon
  const shieldIcon = (color: string) => (
    <svg className={`h-3.5 w-3.5 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  )

  // Globe/Scraper icon
  const scraperIcon = (color: string) => (
    <svg className={`h-3.5 w-3.5 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
    </svg>
  )

  // Text/Formatter icon
  const textIcon = (color: string) => (
    <svg className={`h-3.5 w-3.5 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  )

  const nodes: NodeConfig[] = [
    { id: 'restore_state', label: 'Rehydrate State', icon: databaseIcon, x: 50, y: 6.25 },
    { id: 'orchestrator', label: 'Orchestrator', icon: brainIcon, x: 50, y: 20.8 },
    { id: 'clarification', label: 'Clarification', icon: questionIcon, x: 23.4, y: 38.5 },
    { id: 'query_builder', label: 'Query Builder', icon: buildIcon, x: 76.6, y: 38.5 },
    { id: 'url_validator', label: 'URL Validator', icon: shieldIcon, x: 76.6, y: 53.1 },
    { id: 'property_scraper', label: 'Property Scraper', icon: scraperIcon, x: 76.6, y: 67.7 },
    { id: 'response_formatter', label: 'Formatter', icon: textIcon, x: 76.6, y: 82.3 },
    { id: 'save_state', label: 'Save State', icon: databaseIcon, x: 50, y: 92.7 },
  ]

  // Render edge line
  const renderEdge = (
    id: string,
    pathData: string,
    sourceId: string,
    targetId: string
  ) => {
    const srcStatus = getNodeStatus(sourceId)
    const tgtStatus = getNodeStatus(targetId)

    let strokeColor = 'stroke-zinc-200 dark:stroke-zinc-800/80'
    let isAnimated = false
    let dashStyle = 'stroke-dasharray-[3,3]'

    if (tgtStatus === 'active') {
      strokeColor = 'stroke-sky-500'
      isAnimated = true
      dashStyle = 'animate-pg-dash'
    } else if (tgtStatus === 'completed') {
      strokeColor = 'stroke-emerald-500'
      dashStyle = ''
    } else if (srcStatus === 'skipped' || tgtStatus === 'skipped') {
      strokeColor = 'stroke-zinc-100 dark:stroke-zinc-900/50 opacity-20'
      dashStyle = ''
    }

    return (
      <g key={id}>
        <path
          d={pathData}
          fill="none"
          className={`${strokeColor} transition-colors duration-300`}
          strokeWidth={tgtStatus === 'active' ? 3 : 2}
          strokeDasharray={dashStyle === 'animate-pg-dash' ? undefined : (dashStyle.includes('stroke-dasharray') ? '4 4' : undefined)}
          style={isAnimated ? {
            strokeDasharray: '8, 8',
            animation: 'pg-dash 1.2s linear infinite'
          } : undefined}
        />
      </g>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center p-4 w-full bg-zinc-50/10 dark:bg-zinc-900/10 border border-zinc-200/30 dark:border-zinc-800/30 rounded-2xl shadow-inner animate-fade-in">
      <style>{`
        @keyframes pg-dash {
          to {
            stroke-dashoffset: -20;
          }
        }
      `}</style>
      
      <div className="relative w-full aspect-[2/3] max-w-[320px] select-none">
        {/* Background Edges Canvas */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 320 480"
          preserveAspectRatio="none"
        >
          {/* Edge 1: restore_state -> orchestrator */}
          {renderEdge('e-restore-orch', 'M 160 30 L 160 100', 'restore_state', 'orchestrator')}
          
          {/* Edge 2: orchestrator -> clarification */}
          {renderEdge('e-orch-clar', 'M 160 100 C 160 135, 75 145, 75 185', 'orchestrator', 'clarification')}
          
          {/* Edge 3: orchestrator -> query_builder */}
          {renderEdge('e-orch-query', 'M 160 100 C 160 135, 245 145, 245 185', 'orchestrator', 'query_builder')}
          
          {/* Edge 4: clarification -> save_state */}
          {renderEdge('e-clar-save', 'M 75 185 C 75 285, 110 395, 160 445', 'clarification', 'save_state')}
          
          {/* Edge 5: query_builder -> url_validator */}
          {renderEdge('e-query-val', 'M 245 185 L 245 255', 'query_builder', 'url_validator')}
          
          {/* Edge 6: url_validator -> property_scraper */}
          {renderEdge('e-val-scrap', 'M 245 255 L 245 325', 'url_validator', 'property_scraper')}
          
          {/* Edge 7: property_scraper -> response_formatter */}
          {renderEdge('e-scrap-form', 'M 245 325 L 245 395', 'property_scraper', 'response_formatter')}
          
          {/* Edge 8: response_formatter -> save_state */}
          {renderEdge('e-form-save', 'M 245 395 C 245 425, 160 425, 160 445', 'response_formatter', 'save_state')}
        </svg>

        {/* Foreground Nodes */}
        {nodes.map((node) => {
          const status = getNodeStatus(node.id)
          const nodeColorClass = status === 'active' 
            ? 'text-sky-500' 
            : status === 'completed'
              ? 'text-emerald-500'
              : status === 'skipped'
                ? 'text-zinc-300 dark:text-zinc-700'
                : 'text-zinc-400 dark:text-zinc-500'

          return (
            <div
              key={node.id}
              className={`absolute -translate-x-1/2 -translate-y-1/2 flex items-center gap-1.5 px-2.5 py-1.5 w-[110px] h-[36px] rounded-lg border text-[10px] sm:text-[11px] shadow-sm transition-all duration-500 select-none ${getNodeClasses(status)}`}
              style={{
                left: `${node.x}%`,
                top: `${node.y}%`,
              }}
            >
              <div className="flex shrink-0 items-center justify-center">
                {node.icon(nodeColorClass)}
              </div>
              <span className="truncate font-semibold leading-none">{node.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
