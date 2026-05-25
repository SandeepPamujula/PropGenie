'use client'

import { Component, type ReactNode, type ErrorInfo } from 'react'

export interface ErrorBoundaryProps {
  children: ReactNode
}

export interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // You could also log the error to an error reporting service
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 p-6 dark:bg-zinc-950 animate-fade-in">
          <div className="flex max-w-md flex-col items-center text-center">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-100 text-red-600 shadow-sm dark:bg-red-900/30 dark:text-red-400">
              <svg
                className="h-10 w-10"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h1 className="mb-3 text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Something went wrong
            </h1>
            <p className="mb-8 text-base text-zinc-600 dark:text-zinc-400">
              We encountered an unexpected error while rendering this page. Please try reloading.
            </p>
            <button
              onClick={this.handleReload}
              className="rounded-full bg-zinc-900 px-8 py-3.5 text-sm font-semibold text-white shadow-md transition-all hover:bg-zinc-800 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:ring-offset-2 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200 dark:focus:ring-zinc-50 dark:focus:ring-offset-zinc-950"
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
