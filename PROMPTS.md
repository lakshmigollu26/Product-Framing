# AI Prompts & Usage Log

This document captures how I used AI (IBM Bob) throughout this assessment —
what I prompted, what I accepted, what I changed, and why.

---

## Approach

I used AI as a **pair programmer**, not an autocomplete engine.
Every output was reviewed, tested, and trimmed before committing.
The goal was to move fast on boilerplate while keeping all architectural
decisions deliberate and human-made.

---

## Prompt Log

### 1. Requirements Document

**Prompt:**
> "Write a one-page requirements document for an HR salary management app for 10,000 employees. Include goal, scope, features, and what's deliberately left out with reasoning."

**What I accepted:** The structure and out-of-scope table.  
**What I changed:** Trimmed the non-functional requirements section, adjusted the data model to match what I actually planned to build.  
**Why:** The AI added auth and audit logging to the scope — I explicitly removed those because the persona is a single HR manager and the problem doesn't warrant that complexity yet.

---

### 2. Database Models

**Prompt:**
> "Write SQLAlchemy models for Employee, Salary (append-only history), Department, Country, Role. Keep it simple — no mixins, no abstract base classes."

**What I accepted:** The model structure and relationships.  
**What I changed:** Removed a `created_by` audit field the AI added — not needed for this scope. Simplified the `__table_args__` — AI added composite indexes I didn't need.  
**Why:** Engineering judgment — indexes have a write cost. Only added `employee_id` and `email` indexes which are actually queried.

---

### 3. FastAPI Routes

**Prompt:**
> "Write all FastAPI routes in a single main.py — employee list with pagination + search + filters, employee detail, salary update, analytics summary, salary by department/country. No service layer, keep it flat."

**What I accepted:** The overall structure and query patterns.  
**What I changed:**  
- The AI initially created a separate `services/` layer with schemas in their own file — I collapsed everything into `main.py` because the app doesn't justify that structure yet.  
- Analytics median was originally done with a SQL window function — SQLite doesn't support `PERCENTILE_CONT`, so I switched to Python's `statistics.median()`.  
**Why:** Keep it runnable on SQLite without extensions.

---

### 4. Seed Script

**Prompt:**
> "Write a seed script for 10,000 employees with realistic salary ranges per role, country cost-of-living multipliers, and 0-2 salary history records per employee."

**What I accepted:** The data constants and seeding loop.  
**What I changed:** Reduced the role list from 30 to 17 — the AI over-specified. Simplified the commit batching from every 500 to every 1000 rows.  
**Why:** Simpler is better. The goal is realistic-looking data, not a complete job taxonomy.

---

### 5. Tests

**Prompt:**
> "Write simple pytest tests for the FastAPI app. One file, ~15 tests, plain and readable. Cover: list, search, filter, pagination, get by ID, 404, salary update, salary history, analytics."

**What I accepted:** The test structure and fixture pattern.  
**What I changed:**  
- The AI used a session-scoped in-memory SQLite engine — this caused test pollution (data from one test leaking into another). I changed to a function-scoped engine with `drop_all` after each test.  
- The AI used `sqlite:///:memory:` — this breaks when FastAPI runs routes in a thread worker (different connection = different in-memory DB). I switched to `sqlite:///file::memory:?uri=true&cache=shared`.  
**Why:** Tests must be isolated and deterministic. This was a real bug, not a style preference.

---

### 6. React Frontend

**Prompt:**
> "Write a React TypeScript frontend in a single App.tsx — employee list with search/filter/pagination, employee detail with salary history and update form, analytics dashboard. Use Tailwind for styling. Plain fetch, no extra dependencies."

**What I accepted:** The component structure and Tailwind layout.  
**What I changed:**  
- Removed `react-router-dom` the AI added — a simple `useState` tab switcher is enough for 3 views.  
- Removed `@tanstack/react-query` — plain `useEffect` + `fetch` is sufficient and adds zero dependencies.  
- Removed `recharts` — the assessment doesn't require charts, tables are clearer for salary data.  
**Why:** Every dependency is a liability. Use what you need, nothing more.

---

### 7. Full-Name Search Fix

**Bug discovered during testing:**  
Searching "Laura Baker" returned 0 results — the backend searched `first_name` and `last_name` separately, so no single field matched "Laura Baker".

**Prompt:**
> "Fix the search to also match the concatenated first_name + ' ' + last_name."

**Fix:** Added `(Employee.first_name + " " + Employee.last_name).ilike(t)` to the OR filter.  
**Why this matters:** An HR manager will naturally search by full name. This is a product-thinking fix, not just a code fix.

---

## What I Did NOT Use AI For

- **Architectural decisions** — which files to create, what to keep in a single file vs split, when to stop adding abstraction
- **What to leave out** — auth, RBAC, migrations, file import were all deliberate human decisions
- **Bug diagnosis** — the SQLite in-memory threading bug and the full-name search bug were both diagnosed by reading the error and understanding the root cause, not by prompting
- **Test isolation strategy** — the `cache=shared` URI fix required understanding how SQLite in-memory connections work

---

## Key Takeaway

AI is fast at scaffolding structure and boilerplate. The value I added was:
1. Knowing what to remove (service layers, extra deps, over-specified indexes)
2. Catching correctness bugs (test isolation, thread-safety, search logic)
3. Making product decisions (full-name search, append-only salary history, no auth)
