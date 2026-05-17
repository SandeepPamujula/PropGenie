import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'PropGenie | AI Real Estate Search Assistant for India',
  description:
    'Find your perfect rental or purchase property in India using PropGenie, the AI-powered search assistant that aggregates and prioritizes listings from top real estate portals.',
  keywords: [
    'real estate',
    'property search',
    'India',
    'NoBroker',
    '99acres',
    'AI assistant',
    'rent',
    'buy',
  ],
  authors: [{ name: 'PropGenie Team' }],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-50">
        {children}
      </body>
    </html>
  )
}
