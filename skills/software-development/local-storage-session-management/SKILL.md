---
name: local-storage-session-management
description: "Add localStorage-based session persistence, history sidebar, and compare view to React/Next.js analysis tools. Covers CRUD hooks, date-grouped history lists, side-by-side comparison grids, and integration with existing components via callback props."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# LocalStorage session management

Use when adding client-side session persistence, analysis history, or multi-item comparison views to a React or Next.js app.

## When to use

- App needs to persist user's analysis results across browser sessions without a backend
- Adding a history sidebar that groups saved items by date (Today, Yesterday, This week, Older)
- Building a compare/contrast view for side-by-side review of multiple saved results
- Adding auto-save on analysis completion with the ability to remove individual items or clear all

## Core architecture

Three-layer pattern:

1. **Hook layer** — `use*History.ts` — localStorage CRUD + React state. Single source of truth.
2. **Sidebar component** — `*sidebar.tsx` — date-grouped list with select/remove/clear.
3. **Compare component** — `*compare.tsx` — full-screen modal grid of selected items.

## Steps

### 1. Define data model

```typescript
interface SavedItem {
  id: string;           // crypto.randomUUID() or Date.now().toString(36)
  listingText: string;  // user input
  preferences: {        // optional filter/preference inputs
    budgetVnd?: number;
    workplaceDistrict?: string;
    maxCommuteMinutes?: number;
  };
  result: AnalyzeResponse; // the analysis/result payload
  createdAt: string;       // new Date().toISOString()
}
```

Max items cap (e.g. 20) prevents localStorage quota issues.

### 2. Create the hook

Pattern: `use*History` hook wrapping `useState` + `useEffect` for hydration.

```typescript
function useAnalysisHistory() {
  const [items, setItems] = useState<SavedItem[]>([]);
  useEffect(() => { setItems(load()); }, []);

  const add = useCallback((...args) => {
    // prepend new item, slice to MAX_ITEMS, persist
  }, []);

  const remove = useCallback((id: string) => { ... }, []);
  const clear = useCallback(() => { ... }, []);

  return { items, add, remove, clear };
}
```

Key details:
- `load()` reads from `localStorage.getItem(STORAGE_KEY)` at init only
- `save(items)` called inside every mutation, writes JSON string back
- Wrap both in try/catch for private browsing / quota errors
- `crypto.randomUUID()` preferred for IDs (available in secure contexts)

### 3. Build history sidebar

Date-grouped list component:

- Group items by comparing `createdAt` against today/yesterday/this-week boundaries
- Each group rendered as a section with uppercase label
- Each item shows verdict + score + text preview
- Checkbox for multi-select (feeds into compare view)
- Remove button (x) per item
- Clear all button
- Compare button (visible when 2+ selected)

### 4. Build compare view

Full-screen overlay with side-by-side grid:

- Fixed position, z-index 1000, dark backdrop
- Grid layout: 180px label column + N data columns (one per selected item)
- Rows for each analysis field (match, risk, price, red flags, summary, etc.)
- Close button to dismiss
- Conditional rows: only show commute row if any item has commute data

### 5. Integrate with existing components

Add an `onAnalysisComplete` callback to the existing analysis component:

```typescript
interface AnalyzerProps {
  onAnalysisComplete?: (
    input: string,
    preferences: { ... },
    result: AnalyzeResult,
  ) => void;
}
```

The parent page orchestrator wires hook + sidebar + compare + analyzer together:

```typescript
export default function Page() {
  const { items, add, remove, clear } = useAnalysisHistory();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showCompare, setShowCompare] = useState(false);

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <HistorySidebar ... />
      <Analyzer onAnalysisComplete={add} />
      {showCompare && <CompareView onClose={() => setShowCompare(false)} />}
    </div>
  );
}
```

## Pitfalls

- **localStorage SSR guard**: always guard reads with `typeof window === 'undefined'` for Next.js SSR
- **Quota exhaustion**: set MAX_ITEMS cap (20 is safe); localStorage is 5-10MB
- **Private browsing**: some browsers throw on localStorage.setItem in private mode — wrap in try/catch
- **Stale data on tab sync**: localStorage does not sync between tabs. For cross-tab sync, add a `storage` event listener
- **Date grouping boundaries**: use `setHours(0,0,0,0)` on today to create clean day boundaries, not relative-from-now math
- **Compare grid overflow**: use a scrollable container for the modal, not fixed height
- **ReactNode import**: when using `React.ReactNode` type in the compare component, import `{ ReactNode }` from 'react' — avoid the `React.` namespace prefix which assumes default import

## Support files

- See `references/analysis-history-implementation.md` for the full implementation from GIN-12: hook, sidebar, compare view, and analyzer integration with exact file contents.
