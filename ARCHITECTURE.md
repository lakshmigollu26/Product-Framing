# High-Level Design — ACME Salary Management System

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                            │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │           React + TypeScript (Vite)             │   │
│   │                                                 │   │
│   │  ┌──────────────┐  ┌───────────┐  ┌─────────┐  │   │
│   │  │ Employee List│  │  Detail / │  │Analytics│  │   │
│   │  │ Search/Filter│  │  Salary   │  │Dashboard│  │   │
│   │  └──────────────┘  └───────────┘  └─────────┘  │   │
│   │                                                 │   │
│   │              api.ts (plain fetch)               │   │
│   └────────────────────┬────────────────────────────┘   │
│                        │ HTTP/JSON                       │
└────────────────────────┼────────────────────────────────┘
                         │ port 8000
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI (Python)                        │
│                                                         │
│   GET  /employees          — paginated list + filters   │
│   GET  /employees/:id      — detail + salary history    │
│   PUT  /employees/:id/salary — add salary record        │
│   GET  /analytics/summary  — org-wide stats             │
│   GET  /analytics/by-department                         │
│   GET  /analytics/by-country                            │
│   GET  /meta/departments   — filter dropdown data       │
│   GET  /meta/countries                                  │
│                                                         │
│   SQLAlchemy ORM                                        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  SQLite (salary.db)                      │
│                                                         │
│  departments   countries   roles                        │
│       └──────────┴────────────┘                         │
│                    │ FK                                  │
│               employees                                 │
│                    │ FK                                  │
│                 salaries  ← append-only history         │
└─────────────────────────────────────────────────────────┘
```

## Data Model

```
Department   Country        Role
  id, name   id, name       id, title, level
             currency_code  (junior/mid/senior/lead/manager)
     │              │              │
     └──────────────┴──────────────┘
                    │ FK x3
               Employee
               id, first_name, last_name
               email, hire_date
                    │ FK
               Salary  (append-only)
               id, employee_id
               amount, currency
               effective_date, reason
               created_at
```

**Key design choice:** Salary is append-only. Every change creates a new row. This gives a full audit trail — you can always see what someone was paid and when it changed.

## Request Flow — Employee List

```
User types search "Laura Baker"
        │
        ▼
App.tsx — builds query params
  ?search=Laura+Baker&page=1&page_size=50
        │
        ▼
api.ts fetch → GET /employees
        │
        ▼
FastAPI list_employees()
  → SQLAlchemy query with OR filter:
      first_name ILIKE '%Laura Baker%'
      last_name  ILIKE '%Laura Baker%'
      full_name  ILIKE '%Laura Baker%'   ← concatenated
      email      ILIKE '%Laura Baker%'
  → returns { total, page, items[] }
        │
        ▼
React renders table rows
```

## Request Flow — Salary Update

```
HR Manager fills form → clicks Save
        │
        ▼
PUT /employees/:id/salary
  { amount, currency, effective_date, reason }
        │
        ▼
FastAPI — inserts new Salary row (does NOT update old row)
        │
        ▼
Returns new record → UI refreshes salary history
```

## Analytics — How Stats Are Computed

SQLite has no `PERCENTILE_CONT`, so median is computed in Python:

```
1. Subquery: get max(effective_date) per employee
2. Join back to salaries to get the latest amount per employee
3. Pull all amounts into Python list
4. Use statistics.median() for median
5. avg/min/max computed in Python too (simple, no SQL complexity)
```

## What Was Deliberately Kept Simple

| Decision | Reason |
|----------|--------|
| SQLite (not Postgres) | Zero infra, sufficient for 10k employees, easy to swap |
| No auth | Single HR Manager persona, internal tool |
| No ORM migrations (Alembic) | `create_all()` is enough for this scope |
| All routes in one file | Avoids premature abstraction — easy to read top to bottom |
| Plain `fetch` in frontend | No extra dependencies, React Query would be overkill here |
| No state management (Redux/Zustand) | Local `useState` is sufficient for 3 views |

## What Would Change at Scale

| If... | Then... |
|-------|---------|
| Multiple HR teams / orgs | Add auth (JWT), RBAC, tenant isolation |
| Postgres in prod | Change `DATABASE_URL`, remove `check_same_thread` |
| Large analytics queries | Precompute aggregates with a background job or materialized view |
| File import from Excel | Add `/import` endpoint with pandas CSV/Excel parsing |
| Audit requirements | Add `changed_by` field to Salary + request logging middleware |
