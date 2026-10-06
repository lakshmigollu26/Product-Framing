# Requirements Document — ACME Employee Salary Management System

## Goal

Replace ACME's spreadsheet-based salary management process with a web application that lets HR managers view, manage, and analyze salary data for 10,000+ employees across multiple countries — from a single interface.

---

## User Persona

**Primary User:** HR Manager  
A non-technical power user who needs fast access to employee salary records, wants to slice data by department, country, and role, and needs confidence that changes are audited.

---

## Scope & Features

### Core Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | Employee Directory | Paginated, searchable list of all employees with key attributes (name, department, country, role, salary) |
| 2 | Salary Management | View and edit an employee's current salary; record salary revisions with effective date and reason |
| 3 | Salary History | Per-employee timeline of all salary changes |
| 4 | Analytics Dashboard | Org-wide stats: average/median salary by department, country, and role; headcount distribution; pay band ranges |
| 5 | Filter & Search | Filter employees by department, country, role, salary range; full-text search by name or ID |
| 6 | Data Seeding | Seed script to generate 10,000 realistic employees with varied departments, countries, roles, and salaries |

### API Surface (Backend)

- `GET /employees` — paginated list with filters
- `GET /employees/:id` — single employee detail + salary history
- `PUT /employees/:id/salary` — update salary (creates history entry)
- `GET /analytics/summary` — org-wide aggregates
- `GET /analytics/by-department` — salary stats grouped by department
- `GET /analytics/by-country` — salary stats grouped by country
- `GET /analytics/by-role` — salary stats grouped by role

---

## Deliberately Left Out (and Why)

| Feature | Reason for Exclusion |
|---------|----------------------|
| Authentication / Authorization | Out of scope for an internal tool prototype; adds infrastructure complexity without validating core value |
| Multi-tenancy | ACME is a single org — no need for tenant isolation |
| Payroll Processing / Payslips | Payroll execution is a separate, regulated domain (tax, compliance) — out of scope |
| Leave / Benefits Management | Different problem space; HR modules are additive once core salary is solid |
| Real-time notifications | Not needed for a batch-oriented HR workflow |
| Role-based access control | Single HR Manager persona defined; RBAC can be layered later |
| Audit logging to external systems | Basic salary history captures the change trail; full audit pipeline is infra-heavy |
| Mobile native app | Web-responsive is sufficient for desktop HR use |
| File import/export (Excel) | The goal is to *replace* Excel dependence; import bridges legacy habit — phase 2 |

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend language | Python | Required by assessment; clean, readable, strong ecosystem |
| Backend framework | FastAPI | Async, auto-generated OpenAPI docs, fast development |
| Database | SQLite (dev) | Zero-config relational DB; schema is easily migrated to Postgres |
| ORM | SQLAlchemy + Alembic | Industry standard, migrations included |
| Frontend | React + TypeScript (Vite) | Fast build, strong typing, component ecosystem |
| UI Library | Tailwind CSS + shadcn/ui | Utility-first CSS with accessible, composable components |
| Testing | pytest (backend) + Vitest (frontend) | Fast, readable, deterministic |

---

## Data Model (Simplified)

```
Employee
  id, first_name, last_name, email, hire_date,
  department_id → Department,
  country_id    → Country,
  role_id       → Role

SalaryRecord
  id, employee_id, amount, currency, effective_date, reason, created_at

Department  — id, name
Country     — id, name, currency_code
Role        — id, title, level (junior/mid/senior/lead/manager)
```

---

## Non-Functional Requirements

- Page load < 2s for employee list (paginated, 50/page)
- Seed script completes in < 30s for 10,000 employees
- API response < 200ms for paginated queries with indexes
- All endpoints return JSON; errors follow RFC 7807 problem detail format

---

## Success Criteria

1. HR Manager can find any employee in under 5 seconds via search or filter
2. Salary update is reflected immediately with history preserved
3. Dashboard shows accurate org-wide compensation analytics
4. Codebase has meaningful test coverage on core business logic
