---
name: constants_rule
description: Coding standard requiring all hardcoded strings and magic numbers to be defined as grouped constants.
---
# Coding Standard: Constants and Magic Numbers

To maintain clean, maintainable, and readable code, all developers (and AI agents) must adhere to the following rules regarding hardcoded strings and magic numbers in this repository.

## The Rule

- **No Hardcoded Strings**: All string literals (except for simple log formats or trivial internal labels) must be defined as named constants.
- **No Magic Numbers**: Any numeric literals representing thresholds, limits, timeouts, ports, or business logic bounds must be defined as named constants.
- **Group Constants**: Group constants logically (e.g., by feature, component, or namespace) in a dedicated file (like `constants.py` or `constants.ts`) or class to avoid polluting the global namespace and to make them easily reusable.

## Python Example

```python
# GOOD: Constants grouped logically
class RateLimitConfig:
    MAX_DAILY_SEARCHES = 10
    RESET_TIME_ZONE = "Asia/Kolkata"

class ScrapingDefaults:
    DEFAULT_TIMEOUT_SECONDS = 5.0
    DEFAULT_MAX_PROPERTIES = 5
```

## TypeScript Example

```typescript
// GOOD: Constants grouped logically
export const PORTAL_BRAND_COLORS = {
  NOBROKER: "#00B050",
  ACRES: "#0078D4",
} as const;
```
