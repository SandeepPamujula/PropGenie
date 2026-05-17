import type { ReactNode } from 'react'

export interface ChatPageTemplateProps {
  header: ReactNode
  chatWindow: ReactNode
  inputBar: ReactNode
}

export function ChatPageTemplate({ header, chatWindow, inputBar }: ChatPageTemplateProps) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-zinc-50 font-sans text-zinc-950 transition-colors duration-300 dark:bg-zinc-950 dark:text-zinc-50">
      {/* Header Panel */}
      <header className="sticky top-0 z-40 w-full border-b border-zinc-200/60 bg-white/70 backdrop-blur-md dark:border-zinc-800/60 dark:bg-zinc-950/70">
        {header}
      </header>

      {/* Main Conversation Container */}
      <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 md:py-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-6" id="conversation-area">
          {chatWindow}
        </div>
      </main>

      {/* Floating Chat Input bar */}
      <footer className="sticky bottom-0 z-30 w-full border-t border-zinc-200/50 bg-white/80 p-4 backdrop-blur-lg dark:border-zinc-800/50 dark:bg-zinc-950/80">
        <div className="mx-auto max-w-3xl">{inputBar}</div>
      </footer>
    </div>
  )
}
