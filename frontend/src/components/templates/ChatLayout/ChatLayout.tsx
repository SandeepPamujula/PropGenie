import { useEffect, useRef, type ReactNode, type ReactElement } from 'react'

export interface ChatLayoutProps {
  header: ReactNode
  inputBar: ReactNode
  children: ReactNode
}

export function ChatLayout({ header, inputBar, children }: ChatLayoutProps): ReactElement {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Smooth scroll-to-bottom on children (messages/updates) change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [children])

  return (
    <div
      id="chat-layout-viewport"
      className="flex h-screen w-full flex-col overflow-hidden bg-zinc-50 font-sans text-zinc-950 transition-colors duration-300 dark:bg-zinc-950 dark:text-zinc-50"
    >
      {/* Header Panel */}
      <header
        id="chat-layout-header"
        className="sticky top-0 z-40 w-full border-b border-zinc-200/60 bg-white/70 backdrop-blur-md dark:border-zinc-800/60 dark:bg-zinc-950/70"
      >
        <div className="mx-auto max-w-4xl">{header}</div>
      </header>

      {/* Scrollable Conversation Container */}
      <main
        id="chat-layout-scroll-container"
        className="flex-1 overflow-y-auto px-4 py-4 sm:px-6 md:py-6"
      >
        <div id="chat-layout-content" className="mx-auto flex max-w-3xl flex-col gap-4 pb-4">
          {children}
          {/* Scroll Target element */}
          <div ref={bottomRef} id="chat-layout-scroll-anchor" className="h-2" />
        </div>
      </main>

      {/* Floating Chat Input bar */}
      <footer
        id="chat-layout-footer"
        className="sticky bottom-0 z-30 w-full border-t border-zinc-200/50 bg-white/80 p-4 backdrop-blur-lg dark:border-zinc-800/50 dark:bg-zinc-950/80 sm:px-6"
      >
        <div className="mx-auto max-w-3xl">{inputBar}</div>
      </footer>
    </div>
  )
}
