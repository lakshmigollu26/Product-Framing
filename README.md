# ACME Salary Management

Employee salary management for 10,000 employees. Built with Python/FastAPI + React/TypeScript.

## Structure

```
backend/
  models.py   — SQLAlchemy models (Employee, Salary, Department, Country, Role)
  main.py     — FastAPI app, all routes
  seed.py     — seeds 10,000 employees into SQLite
  tests/
    test_main.py — 15 tests

frontend/
  src/
    App.tsx   — entire UI (employee list, detail, analytics)
    api.ts    — plain fetch wrapper
```

## Run locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed.py          # seed 10,000 employees (one-time)
uvicorn main:app --reload
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

**Tests**
```bash
cd backend && source venv/bin/activate
pytest tests/test_main.py -v
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/employees` | Paginated list. Params: `page`, `page_size`, `search`, `department_id`, `country_id` |
| GET | `/employees/:id` | Employee detail + salary history |
| PUT | `/employees/:id/salary` | Add a salary record |
| GET | `/analytics/summary` | Org-wide stats |
| GET | `/analytics/by-department` | Salary stats per department |
| GET | `/analytics/by-country` | Salary stats per country |
| GET | `/meta/departments` | Department list (for filters) |
| GET | `/meta/countries` | Country list (for filters) |
