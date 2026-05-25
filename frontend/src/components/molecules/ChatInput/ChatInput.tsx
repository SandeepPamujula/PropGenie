import type { ReactElement, KeyboardEvent, ChangeEvent } from 'react'

export interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = 'Ask for rentals or sale properties in India...',
}: ChatInputProps): ReactElement {
  const charLimit = 2000
  const isCloseToLimit = value.length > 1800
  const isEmpty = !value.trim()
  const isSendDisabled = disabled || isEmpty

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isSendDisabled) {
        onSubmit()
      }
    }
  }

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value
    if (val.length <= charLimit) {
      onChange(val)
    }
  }

  return (
    <div className="w-full" id="chat-input-container">
      {/* Visual Typing Indicator when disabled (agent processing) */}
      {disabled && (
        <div
          id="chat-input-typing-indicator"
          className="mb-2 flex items-center gap-1.5 px-1 text-xs text-zinc-400 dark:text-zinc-500 animate-pulse-slow"
        >
          <div className="flex gap-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-500 [animation-delay:-0.3s]"></span>
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-500 [animation-delay:-0.15s]"></span>
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-500"></span>
          </div>
          <span>PropGenie is searching...</span>
        </div>
      )}

      {/* Styled Input Wrapper with focus glow animation */}
      <div
        className={`relative flex flex-col rounded-2xl border transition-all duration-300 ${
          disabled
            ? 'border-zinc-200/50 bg-zinc-50/30 dark:border-zinc-800/50 dark:bg-zinc-900/30'
            : 'border-zinc-200 bg-zinc-50/50 focus-within:border-brand-500/70 focus-within:bg-white focus-within:ring-4 focus-within:ring-brand-500/10 dark:border-zinc-800 dark:bg-zinc-900/50 dark:focus-within:border-brand-500/60 dark:focus-within:bg-zinc-950 dark:focus-within:ring-brand-500/5'
        }`}
      >
        <textarea
          id="chat-input-textarea"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          rows={2}
          maxLength={charLimit}
          className="w-full resize-none rounded-t-2xl bg-transparent px-4 py-3 text-sm text-zinc-900 outline-none placeholder:text-zinc-400 dark:text-zinc-100 dark:placeholder:text-zinc-500"
        />

        <div className="flex items-center justify-between border-t border-zinc-100/80 px-4 py-2.5 dark:border-zinc-800/60">
          {/* Character counter with warning state */}
          <span
            id="chat-input-counter"
            className={`text-xs font-medium select-none transition-colors duration-200 ${
              isCloseToLimit
                ? 'text-amber-500 dark:text-amber-400 font-semibold'
                : 'text-zinc-400 dark:text-zinc-500'
            }`}
          >
            {value.length} / {charLimit}
          </span>

          {/* Send Button */}
          <button
            id="chat-input-send-button"
            onClick={onSubmit}
            disabled={isSendDisabled}
            aria-label="Send message"
            className={`flex h-8 w-8 items-center justify-center rounded-xl text-white shadow-sm transition-all duration-300 ${
              isSendDisabled
                ? 'bg-zinc-200 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-600 cursor-not-allowed shadow-none'
                : 'bg-brand-500 shadow-brand-500/20 hover:bg-brand-900 hover:scale-105 active:scale-95'
            }`}
          >
            <svg
              className="h-4.5 w-4.5 transform rotate-90"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9-7-9-7v14z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
