# Milestone 4 — Frontend Chat UI

> **Goal:** Build the Next.js static-export chat interface with SSE consumption, session management, portal card rendering, and responsive design. The frontend connects to the backend via CloudFront (prod) or FastAPI (local dev) and renders real-time agent status updates and search results.

---

## US-17 — Chat Interface Layout & Design System

**User Story:**
As a **property seeker**,
I want a clean, modern chat interface that feels premium and responsive,
So that I have a delightful experience searching for properties.

**Tasks:**
- **CRITICAL RULE:** Do not create a `src/app/api` directory in the Next.js frontend, as it will conflict with CloudFront routing `/api/*` to the Lambda Function URL in a static export setup.
- Design the CSS design system in `frontend/src/app/globals.css`:
  - Color palette: dark/light mode support, accent colors for portal brands (NoBroker, 99acres)
  - Typography: Google Font (Inter), heading/body/caption sizes
  - Spacing, border-radius, shadow, and transition tokens
  - Glassmorphism card styles for portal cards
- Create `frontend/src/components/ChatLayout.tsx`:
  - Full-viewport layout with header (PropGenie logo + tagline), chat area (scrollable), and input bar (sticky bottom)
  - Responsive: works on mobile (360px) through desktop (1440px)
  - Smooth scroll-to-bottom on new messages
- Create `frontend/src/components/ChatHeader.tsx`:
  - App name, tagline ("Find your perfect property with AI"), and daily search counter badge
- Create `frontend/src/components/ChatInput.tsx`:
  - Text input with send button
  - Enter-to-send, Shift+Enter for newline
  - 2000 character limit with visual counter
  - Disabled state while agent is processing
- Add micro-animations: message fade-in, typing indicator pulse, input focus glow

**Acceptance Criteria:**
- Chat layout renders correctly on mobile (360px), tablet (768px), and desktop (1440px)
- Dark mode is supported via `prefers-color-scheme` media query
- Input field enforces 2000 character maximum with visual feedback
- Send button is disabled when input is empty or agent is processing
- All interactive elements have unique IDs for testability
- Page loads with proper `<title>`, `<meta description>`, and semantic HTML

**Status:** Completed

---

## US-18 — Session Management (Client-Side)

**User Story:**
As a **property seeker**,
I want my conversation to persist within a session so multi-turn clarifications work seamlessly,
So that I don't have to repeat information I've already provided.

**Tasks:**
- Create `frontend/src/lib/session.ts`:
  - Generate UUID v4 session ID on first visit (use `crypto.randomUUID()`)
  - Store session ID in `sessionStorage` (cleared on tab close, matching 30-min server TTL intent)
  - Expose `getSessionId()` utility
- Create `frontend/src/lib/api.ts`:
  - Determine `API_BASE_URL` from `NEXT_PUBLIC_API_URL` environment variable (defaults to `` for prod)
  - `sendMessage(message: string)` function that sends `POST ${API_BASE_URL}/api/chat` with:
    - `Content-Type: application/json`
    - `Accept: text/event-stream`
    - `X-Session-ID` header
  - Returns a `ReadableStream` for SSE consumption
- Handle session expiry gracefully: if server returns a session-not-found indicator, generate a new session ID and inform the user

**Acceptance Criteria:**
- Session ID is a valid UUID v4 format
- Session ID persists across page refreshes within the same tab
- New session ID is generated when opening a new tab
- API requests include the `X-Session-ID` header
- Session expiry is handled without crashing the UI
- API URL defaults to `http://localhost:8000` in local dev, empty string (same-origin) in production

**Status:** Completed

---

## US-19 — SSE Stream Consumer & Message Rendering

**User Story:**
As a **property seeker**,
I want to see real-time status updates as the AI processes my search,
So that I know the system is working and can follow its progress.

**Tasks:**
- Create `frontend/src/lib/sse.ts`:
  - Parse SSE events from the fetch response stream
  - Handle event types: `agent_status`, `clarification`, `portal_card`, `search_meta`, `error`, `done`
  - Dispatch parsed events to the message store via callbacks
- Create `frontend/src/components/MessageList.tsx`:
  - Render user messages (right-aligned, accent color)
  - Render assistant messages (left-aligned, neutral background)
  - Support different message types: text, clarification, portal cards, status updates
- Create `frontend/src/components/AgentStatus.tsx`:
  - Animated status indicator showing current agent phase
  - Examples: "Understanding your search…", "Building portal links…", "Validating URLs…"
  - Pulse animation while active, checkmark when complete
- Create `frontend/src/components/ClarificationMessage.tsx`:
  - Display clarification question with round indicator (e.g., "1 of 3")
  - Show resolved fields as subtle chips/tags below the question
- Implement auto-scroll to latest message with smooth animation

**Acceptance Criteria:**
- SSE events are parsed correctly for all 6 event types
- Agent status updates render with appropriate animations
- Clarification messages show round count and resolved fields
- Messages appear in chronological order with smooth scroll
- Connection errors display a retry button
- Stream is properly closed after receiving a `done` event

**Status:** Completed

---

## US-20 — Portal Card Component

**User Story:**
As a **property seeker**,
I want search results displayed as visually distinct portal cards with clear summaries and clickable links,
So that I can quickly compare results across portals and navigate to the one I prefer.

**Tasks:**
- Create `frontend/src/components/PortalCard.tsx`:
  - Portal name with brand color/icon indicator (NoBroker green, 99acres blue)
  - Priority badge based on intent (NoBroker for rent, 99acres for buy)
  - One-line search summary (e.g., "3BHK rentals near HSR Layout — ₹20K to ₹30K/mo")
  - Deep-link URL as a prominent CTA button ("View on NoBroker →")
  - Notes section for defaults applied (e.g., "4 km radius applied")
  - Glassmorphism card styling with hover elevation effect
- Create `frontend/src/components/PortalCardList.tsx`:
  - Renders portal cards in priority order (priority portal first)
  - Grid layout on desktop (2 columns), stack on mobile
  - Staggered fade-in animation for each card
- Create `frontend/src/components/SearchMeta.tsx`:
  - Summary bar below portal cards: "Searched 2 portals · 2 results"
  - Defaults applied listed as subtle notes

**Acceptance Criteria:**
- Portal cards render with correct brand indicators for NoBroker and 99acres
- Priority badge reflects the search intent (NoBroker for rent, 99acres for buy)
- CTA button opens the deep-link URL in a new tab (`target="_blank"`, `rel="noopener noreferrer"`)
- Cards have hover effects (elevation/shadow change)
- Search meta shows accurate counts
- Mobile layout stacks cards vertically with full-width

**Status:** Completed

### Implementation Summary
- **Design Decisions:**
  - Followed Atomic Design by implementing components (`PortalCard`, `PortalCardList`, `SearchMeta`) as molecules and re-exporting them from the components root.
  - Used custom CSS variables (`--color-portal-nobroker-green`, `--color-portal-acres-blue`, etc.) and the `glass-card` utility class to deliver a premium, glassmorphism-based design with transition animations and hover elevation effects.
  - Sorted the cards list client-side to guarantee that priority cards (NoBroker for rentals, 99acres for buy) are displayed first.
  - Used dynamic inline delays to implement staggered fade-in animations on cards.
  - Mapped technical defaults (`radius_km: 4`, `budget_min: 0`) to user-friendly messages ("4 km radius search applied", "Budget floor assumed as ₹0").
- **Key Files Created/Modified:**
  - Created: `frontend/src/components/molecules/PortalCard/PortalCard.tsx` (and `PortalCard.test.tsx`, re-export file `PortalCard.tsx`)
  - Created: `frontend/src/components/molecules/PortalCardList/PortalCardList.tsx` (and `PortalCardList.test.tsx`, re-export file `PortalCardList.tsx`)
  - Created: `frontend/src/components/molecules/SearchMeta/SearchMeta.tsx` (and `SearchMeta.test.tsx`, re-export file `SearchMeta.tsx`)
  - Modified: `frontend/src/types/domain.ts` (updated models to include `notes` and `SearchMeta`)
  - Modified: `frontend/src/types/sse.ts` (updated `PortalCardEvent` payload model)
  - Modified: `frontend/src/app/page.tsx` (updated event mapping for SSE events)
  - Modified: `frontend/src/components/organisms/MessageList/MessageList.tsx` (integrated the new molecules)
- **Verification/Testing Steps:**
  - Wrote comprehensive unit tests for each component to cover brand coloring, priority labeling, CTAs, counts, and sorting.
  - Verified linting runs cleanly (`npm run lint`).
  - Ran the test suite successfully with Jest (`npm test`).

---

## US-21 — Rate Limit UI Handling

**User Story:**
As a **property seeker**,
I want to see a friendly message when I've reached my daily search limit,
So that I understand why I can't search and know when I can try again.

**Tasks:**
- Create `frontend/src/components/RateLimitBanner.tsx`:
  - Friendly message: "You've reached your daily search limit of 10. Please try again tomorrow!"
  - Display the IST reset time
  - Visually distinct from error messages (informational tone, not alarming)
- Update `frontend/src/lib/api.ts` to detect `429 Too Many Requests` responses
- Display the daily search counter in the header (e.g., "3 of 10 searches used today")
- Update counter from the `done` event's `search_count_today` field

**Acceptance Criteria:**
- 429 response is intercepted and the rate limit banner is displayed (not a raw error)
- Search counter in header updates after each successful search
- Rate limit banner includes the reset time in IST
- Input field is disabled when rate limit is reached
- Clarification exchanges do not increment the displayed counter

**Status:** Completed

---

## US-22 — Error Handling & Edge Cases

**User Story:**
As a **property seeker**,
I want graceful error handling for network failures, timeouts, and unexpected server errors,
So that the application never shows a broken state or raw error messages.

**Tasks:**
- Create `frontend/src/components/ErrorMessage.tsx`:
  - User-friendly error display with retry button for retryable errors
  - Different styles for retryable vs non-retryable errors
- Handle SSE connection drop: show "Connection lost" with automatic retry (3 attempts, exponential backoff)
- Handle empty results: "No portals returned results for your search. Try adjusting your criteria."
- Handle network offline: detect `navigator.onLine` and show offline banner
- Add loading skeleton for message area while waiting for first SSE event
- Add global error boundary (`frontend/src/components/ErrorBoundary.tsx`)

**Acceptance Criteria:**
- Network errors display a user-friendly message with retry button
- SSE disconnection triggers automatic reconnection attempts
- Empty search results show a helpful suggestion message
- Offline state is detected and displayed immediately
- Error boundary catches and displays React rendering errors gracefully
- No raw error messages, stack traces, or blank screens visible to users

**Status:** Completed

---

## US-23 — Frontend Component Tests

**User Story:**
As a **frontend developer**,
I want unit and component tests for all key UI components,
So that regressions are caught early and the CI pipeline can validate frontend code quality.

**Tasks:**
- Configure Jest + React Testing Library in `frontend/`
- Write tests for `ChatInput.tsx`: character limit enforcement, disabled state, enter-to-send
- Write tests for `PortalCard.tsx`: correct rendering of portal data, CTA link, priority badge
- Write tests for `RateLimitBanner.tsx`: message display, reset time formatting
- Write tests for `ErrorMessage.tsx`: retry button behavior, different error types
- Write tests for `session.ts`: UUID generation, sessionStorage persistence
- Write tests for `sse.ts`: event parsing for all 6 event types
- Write tests for `api.ts`: request headers, 429 handling
- Ensure `npm test` runs all tests and exits with correct status code

**Acceptance Criteria:**
- All component tests pass with `npm test`
- Test coverage exists for all 6 SSE event types
- Session ID generation and persistence are tested
- Rate limit and error UI states are tested
- Tests can run in CI without a browser (JSDOM environment)
- Minimum 80% line coverage for `src/lib/` and `src/components/`

**Status:** Completed
