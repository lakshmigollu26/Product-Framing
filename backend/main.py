"""
FastAPI app — all routes in one file, kept intentionally simple.
"""
import statistics
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, func, or_, cast, String, select
from sqlalchemy.orm import sessionmaker, Session, joinedload

from models import Base, Department, Country, Role, Employee, Salary

# ── DB setup ──────────────────────────────────────────────────────────────────

DATABASE_URL = "sqlite:///./salary.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Pydantic schemas (only what we actually return) ────────────────────────

class SalaryIn(BaseModel):
    amount: Decimal
    currency: str = "USD"
    effective_date: date
    reason: Optional[str] = None


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="ACME Salary Manager")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper: serialise an employee row to dict ─────────────────────────────

def emp_to_dict(e: Employee) -> dict:
    current = e.salaries[0] if e.salaries else None
    return {
        "id":                       e.id,
        "first_name":               e.first_name,
        "last_name":                e.last_name,
        "email":                    e.email,
        "hire_date":                str(e.hire_date),
        "department":               {"id": e.department_id, "name": e.department.name},
        "country":                  {"id": e.country_id,    "name": e.country.name,
                                     "currency_code": e.country.currency_code},
        "role":                     {"id": e.role_id, "title": e.role.title, "level": e.role.level},
        "current_salary_amount":    float(current.amount)   if current else None,
        "current_salary_currency":  current.currency         if current else None,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/employees")
def list_employees(
    page:          int           = Query(1, ge=1),
    page_size:     int           = Query(50, ge=1, le=200),
    search:        Optional[str] = None,
    department_id: Optional[int] = None,
    country_id:    Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.country),
        joinedload(Employee.role),
        joinedload(Employee.salaries),
    )
    if search:
        t = f"%{search}%"
        full_name = Employee.first_name + " " + Employee.last_name
        q = q.filter(or_(
            Employee.first_name.ilike(t),
            Employee.last_name.ilike(t),
            full_name.ilike(t),
            Employee.email.ilike(t),
            cast(Employee.id, String).ilike(t),
        ))
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    if country_id:
        q = q.filter(Employee.country_id == country_id)

    total = q.count()
    items = q.order_by(Employee.last_name).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [emp_to_dict(e) for e in items]}


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    e = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.country),
        joinedload(Employee.role),
        joinedload(Employee.salaries),
    ).filter(Employee.id == employee_id).first()
    if not e:
        raise HTTPException(404, "Employee not found")
    data = emp_to_dict(e)
    data["salary_history"] = [
        {"id": s.id, "amount": float(s.amount), "currency": s.currency,
         "effective_date": str(s.effective_date), "reason": s.reason}
        for s in e.salaries
    ]
    return data


@app.put("/employees/{employee_id}/salary")
def update_salary(employee_id: int, body: SalaryIn, db: Session = Depends(get_db)):
    if not db.query(Employee).filter(Employee.id == employee_id).first():
        raise HTTPException(404, "Employee not found")
    record = Salary(
        employee_id=employee_id,
        amount=body.amount,
        currency=body.currency,
        effective_date=body.effective_date,
        reason=body.reason,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "amount": float(record.amount), "currency": record.currency,
            "effective_date": str(record.effective_date), "reason": record.reason}


# ── Analytics ─────────────────────────────────────────────────────────────────

def _latest_amounts(db: Session) -> list[float]:
    """One amount per employee — their most recent salary."""
    sub = (
        select(Salary.employee_id, func.max(Salary.effective_date).label("max_date"))
        .group_by(Salary.employee_id).subquery()
    )
    rows = db.query(Salary.amount).join(
        sub, (Salary.employee_id == sub.c.employee_id) & (Salary.effective_date == sub.c.max_date)
    ).all()
    return [float(r[0]) for r in rows]


def _stats(amounts: list[float]) -> dict:
    if not amounts:
        return {"avg": None, "median": None, "min": None, "max": None, "count": 0}
    return {
        "avg":    round(sum(amounts) / len(amounts), 2),
        "median": round(statistics.median(amounts), 2),
        "min":    round(min(amounts), 2),
        "max":    round(max(amounts), 2),
        "count":  len(amounts),
    }


@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    amounts = _latest_amounts(db)
    s = _stats(amounts)
    return {
        "total_employees":       db.query(func.count(Employee.id)).scalar(),
        "avg_salary":            s["avg"],
        "median_salary":         s["median"],
        "min_salary":            s["min"],
        "max_salary":            s["max"],
        "total_payroll":         round(sum(amounts), 2) if amounts else None,
        "headcount_by_department": [
            {"name": n, "count": c} for n, c in
            db.query(Department.name, func.count(Employee.id))
              .join(Employee, Employee.department_id == Department.id)
              .group_by(Department.name).order_by(func.count(Employee.id).desc()).all()
        ],
        "headcount_by_country": [
            {"name": n, "count": c} for n, c in
            db.query(Country.name, func.count(Employee.id))
              .join(Employee, Employee.country_id == Country.id)
              .group_by(Country.name).order_by(func.count(Employee.id).desc()).all()
        ],
        "headcount_by_level": [
            {"name": lv, "count": c} for lv, c in
            db.query(Role.level, func.count(Employee.id))
              .join(Employee, Employee.role_id == Role.id)
              .group_by(Role.level).order_by(func.count(Employee.id).desc()).all()
        ],
    }


def _salary_by_group(db: Session, group: str) -> list[dict]:
    mapping = {
        "department": (Department, Employee.department_id, Department.id, Department.name),
        "country":    (Country,    Employee.country_id,    Country.id,    Country.name),
    }
    if group not in mapping:
        return []
    _, fk, pk, name_col = mapping[group]
    sub = (
        select(Salary.employee_id, func.max(Salary.effective_date).label("max_date"))
        .group_by(Salary.employee_id).subquery()
    )
    latest = (
        select(Salary).join(
            sub, (Salary.employee_id == sub.c.employee_id) & (Salary.effective_date == sub.c.max_date)
        ).subquery()
    )
    rows = (
        db.query(name_col, latest.c.amount)
          .join(Employee, fk == pk)
          .join(latest, latest.c.employee_id == Employee.id)
          .all()
    )
    groups: dict[str, list[float]] = {}
    for name, amount in rows:
        groups.setdefault(name, []).append(float(amount))
    return [{"name": n, **_stats(v)} for n, v in sorted(groups.items())]


@app.get("/analytics/by-department")
def by_department(db: Session = Depends(get_db)):
    return _salary_by_group(db, "department")


@app.get("/analytics/by-country")
def by_country(db: Session = Depends(get_db)):
    return _salary_by_group(db, "country")


# ── Meta (filter dropdowns) ───────────────────────────────────────────────────

@app.get("/meta/departments")
def meta_departments(db: Session = Depends(get_db)):
    return [{"id": d.id, "name": d.name} for d in db.query(Department).order_by(Department.name).all()]


@app.get("/meta/countries")
def meta_countries(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name} for c in db.query(Country).order_by(Country.name).all()]
