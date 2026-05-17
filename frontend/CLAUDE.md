# PropGenie — Frontend Guidelines for Claude Code

## Project Overview

**PropGenie** is a conversational property search assistant for the Indian real estate market.
Users find properties to buy or rent via a chat interface; the system returns deep-link search
URLs from portals like NoBroker, 99acres, MagicBricks, Housing.com, and Square Yards.

- Framework: **Next.js** (static export, no SSR)
- Styling: **Tailwind CSS only** (no component libraries)
- Language: **TypeScript** (strict mode)
- Hosting: **S3 + CloudFront**
- Streaming: **Server-Sent Events (SSE)**, token-by-token

---

## Component Architecture — Atomic Design (Enforced)

All components must be organised strictly under `src/components/` following the five atomic levels.
Never place a component at the wrong level. When in doubt, go smaller.

```
src/
├── components/
│   ├── atoms/          # Smallest indivisible UI units
│   ├── molecules/      # Compositions of 2–4 atoms
│   ├── organisms/      # Complex, self-contained UI sections
│   ├── templates/      # Page-level layout shells (no real data)
│   └── pages/          # Hydrated templates with real data/state
├── hooks/              # Custom React hooks
├── lib/                # Utilities, API clients, helpers
├── types/              # Shared TypeScript types and interfaces
├── stories/            # Storybook stories (co-located by level)
└── __tests__/          # Jest + React Testing Library tests
```

### Atoms
Single-responsibility, stateless where possible. Accept all customisation via props.

**Examples for PropGenie:**
- `Button` — primary, secondary, ghost variants
- `Input` — text input with label and error state
- `Badge` — portal name tag (NoBroker, 99acres, etc.)
- `Spinner` — loading indicator
- `Icon` — wraps SVG icons with size/color props
- `Text` — typography primitive (heading, body, caption)
- `Divider`
- `Avatar` — user / bot avatar in chat

**Rules:**
- No business logic
- No direct API calls
- No internal state except pure UI state (e.g. hover, focus)
- Must have a Storybook story
- Must have a Jest unit test

### Molecules
Combine atoms to form a reusable functional unit with a single, clear purpose.

**Examples for PropGenie:**
- `ChatBubble` — Avatar + Text + timestamp
- `PortalCard` — Badge + search summary Text + link Button
- `SearchInput` — Input + send Button
- `ClarificationPrompt` — Text question + option Buttons
- `RateLimitBanner` — Icon + Text warning

**Rules:**
- May have local UI state
- No direct API calls
- Each molecule owns its own Storybook story with all states shown
- Jest test for each meaningful interaction

### Organisms
Self-contained, feature-complete UI sections. May connect to hooks or context.

**Examples for PropGenie:**
- `ChatWindow` — scrollable list of ChatBubbles (user + bot)
- `PortalResultsList` — ordered list of PortalCards
- `ChatInputBar` — SearchInput + streaming state indicator
- `SessionExpiredBanner` — full-width overlay organism
- `RateLimitReachedView` — empty state when 10 searches exhausted

**Rules:**
- May consume custom hooks (`useChat`, `useSession`, `useSSE`)
- Must not contain page-level routing logic
- Storybook story required with mocked hook data
- Integration test required (RTL, mocked API)

### Templates
Layout shells that define the page structure. Receive all content via props or slots.
Templates contain no real data — they are purely compositional.

**Examples for PropGenie:**
- `ChatPageTemplate` — header + chat window area + input bar layout
- `ErrorPageTemplate` — centered error state layout

**Rules:**
- No hooks, no API calls, no state
- Storybook story showing the layout with placeholder content
- Snapshot test acceptable here

### Pages
Next.js page components (`app/` or `pages/` dir). Hydrate templates with real data and state.
This is where routing, SSE connections, and session management live.

**Examples for PropGenie:**
- `app/page.tsx` — main chat page, initialises session, connects SSE stream
- `app/error.tsx` — error boundary page

**Rules:**
- One page component per route
- Delegates all rendering to a Template
- Contains hooks and data-fetching logic
- No inline JSX beyond `<SomeChatPageTemplate .../>`

---

## TypeScript — Strict Mode

`tsconfig.json` must include:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "exactOptionalPropertyTypes": true
  }
}
```

**Conventions:**
- All props interfaces named `[ComponentName]Props` and exported
- No `any` — use `unknown` and narrow with type guards
- Prefer `type` over `interface` for unions and intersections
- All API response shapes defined in `src/types/api.ts`
- SSE event payloads typed in `src/types/sse.ts`
- Shared domain types (portal, session, message) in `src/types/domain.ts`

**Key domain types:**
```ts
// src/types/domain.ts

export type Intent = 'buy' | 'rent' | 'ambiguous'

export type PropertyType = 'plot' | 'apartment' | 'villa' | 'house'

export type Portal =
  | 'nobroker'
  | '99acres'
  | 'magicbricks'
  | 'housing'
  | 'squareyards'

export interface PortalResult {
  portal: Portal
  label: string
  summary: string
  url: string
  isPriority: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  portalResults?: PortalResult[]
}

export interface SessionContext {
  sessionId: string
  intent?: Intent
  city?: string
  locationAnchor?: string
  propertyType?: PropertyType
  bhk?: number
  budgetMin?: number
  budgetMax?: number
  radiusKm: number
  clarificationRound: number
}
```

---

## Tailwind CSS Conventions

- **No inline styles** — Tailwind utility classes only
- **No arbitrary values** unless absolutely necessary (e.g. `w-[340px]`)
- Define PropGenie's design tokens in `tailwind.config.ts`:

```ts
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f9ff',
          500: '#0ea5e9',
          900: '#0c4a6e',
        },
        portal: {
          nobroker:    '#e63946',
          acres:       '#f4a261',
          magicbricks: '#2a9d8f',
          housing:     '#457b9d',
          squareyards: '#6a4c93',
        },
      },
      fontFamily: {
        sans: ['Geist', 'sans-serif'],
        mono: ['Geist Mono', 'monospace'],
      },
      animation: {
        'typing': 'typing 1.2s steps(3) infinite',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
    },
  },
}
```

- Use `cn()` utility (clsx + tailwind-merge) for conditional class merging:

```ts
// src/lib/utils.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

---

## ESLint + Prettier

`.eslintrc.json`:
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended-type-checked",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/consistent-type-imports": "warn",
    "import/order": ["warn", { "alphabetize": { "order": "asc" } }],
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

`.prettierrc`:
```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

Run on every save in VS Code (`editor.formatOnSave: true`).
CI pipeline must fail on lint errors — no warnings allowed in prod builds.

---

## Storybook

- Version: Storybook 8+ with `@storybook/nextjs` framework
- Every **atom**, **molecule**, and **organism** must have a `.stories.tsx` file
- Story file lives alongside the component: `Button.stories.tsx` next to `Button.tsx`
- Each story must cover: default state, all variants, loading state, error/disabled state

**Story naming convention:**
```ts
// src/components/atoms/Button/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'Atoms/Button',
  component: Button,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof Button>

export const Primary: Story = { args: { variant: 'primary', children: 'Search' } }
export const Loading: Story = { args: { variant: 'primary', loading: true } }
export const Disabled: Story = { args: { variant: 'primary', disabled: true } }
```

---

## Jest + React Testing Library

- Config: `jest.config.ts` with `@testing-library/jest-dom`
- Test files: `__tests__/` folder mirroring `src/components/` structure,
  or co-located as `Component.test.tsx`
- Coverage threshold (enforced in CI):

```json
{
  "coverageThreshold": {
    "global": {
      "branches": 70,
      "functions": 80,
      "lines": 80,
      "statements": 80
    }
  }
}
```

**Testing conventions:**
- Test behaviour, not implementation — no snapshot tests except for Templates
- Use `userEvent` over `fireEvent` for interactions
- Mock SSE and API calls in `src/__mocks__/`
- Each atom: unit test for all prop variants
- Each molecule: interaction test (click, input, state change)
- Each organism: integration test with mocked hooks

**Example test structure:**
```ts
// __tests__/atoms/Button.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/atoms/Button/Button'

describe('Button', () => {
  it('renders label correctly', () => {
    render(<Button variant="primary">Search</Button>)
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn()
    render(<Button variant="primary" onClick={handleClick}>Search</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when loading', () => {
    render(<Button variant="primary" loading>Search</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

---

## SSE Streaming Hook

The chat interface streams agent responses token-by-token. Use this hook pattern:

```ts
// src/hooks/useSSE.ts
export function useSSE(sessionId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)

  const send = useCallback(async (userInput: string) => {
    setStreaming(true)
    const es = new EventSource(`/api/chat?sessionId=${sessionId}&q=${encodeURIComponent(userInput)}`)

    es.onmessage = (e) => {
      const token = JSON.parse(e.data) as SSEToken
      // append token to last assistant message
    }

    es.onerror = () => {
      setStreaming(false)
      es.close()
    }
  }, [sessionId])

  return { messages, streaming, send }
}
```

---

## File & Folder Naming Conventions

| Artifact | Convention | Example |
|---|---|---|
| Component folder | PascalCase | `Button/` |
| Component file | PascalCase | `Button.tsx` |
| Story file | PascalCase | `Button.stories.tsx` |
| Test file | PascalCase | `Button.test.tsx` |
| Hook | camelCase with `use` prefix | `useSSE.ts` |
| Utility | camelCase | `formatBudget.ts` |
| Type file | camelCase | `domain.ts` |
| Page (Next.js) | lowercase (Next.js convention) | `page.tsx` |

---

## Accessibility (a11y) — Non-Negotiable

- All interactive elements must have accessible labels (`aria-label`, `aria-describedby`)
- Chat messages must use `role="log"` and `aria-live="polite"` for screen reader support
- Color contrast ratio minimum: 4.5:1 (WCAG AA)
- Keyboard navigation must work end-to-end (Tab, Enter, Escape)
- Portal result links must open in a new tab with `rel="noopener noreferrer"` and visible focus ring

---

## What Claude Code Should Always Do

- Place every new component in the correct atomic level folder — never in `src/components/` root
- Create the `.stories.tsx` and `.test.tsx` files alongside every new component automatically
- Use `cn()` for all conditional Tailwind class merging
- Export all prop interfaces from the component file
- Use `type` imports (`import type { ... }`) for TypeScript types
- Never install a UI component library — Tailwind only
- Never use `any` — ask for the correct type if unsure
- Run `eslint --fix` and `prettier --write` before considering a component done

## What Claude Code Should Never Do

- Skip the Storybook story or Jest test for a new component
- Place business logic inside atoms or molecules
- Use inline styles or arbitrary Tailwind values without justification
- Import from a sibling atomic level (organisms must not import from pages)
- Use `console.log` in production code — use `console.warn` or `console.error` only
- Hardcode portal URLs — always import from `src/lib/portals.ts`
