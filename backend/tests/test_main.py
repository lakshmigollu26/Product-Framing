"""
Simple tests for the salary management API.
Run: pytest tests/test_main.py
"""
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import app + DB objects using the flat layout
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Base, Department, Country, Role, Employee, Salary
import main as app_module
from main import app, get_db

# ── Test DB setup ─────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///file::memory:?uri=true&cache=shared",
        connect_args={"check_same_thread": False, "uri": True},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c, db
    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ── Seed helpers ──────────────────────────────────────────────────────────────

def make_employee(db):
    dept    = Department(name="Engineering")
    country = Country(name="United States", currency_code="USD")
    role    = Role(title="Software Engineer", level="mid")
    db.add_all([dept, country, role])
    db.flush()
    emp = Employee(first_name="Jane", last_name="Doe", email="jane@acme.com",
                   hire_date=date(2022, 1, 1),
                   department_id=dept.id, country_id=country.id, role_id=role.id)
    db.add(emp)
    db.flush()
    return emp, dept, country


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_health(client):
    c, _ = client
    assert c.get("/health").json() == {"status": "ok"}


def test_list_employees_empty(client):
    c, _ = client
    r = c.get("/employees")
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_list_employees_returns_employee(client):
    c, db = client
    make_employee(db)
    r = c.get("/employees")
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["first_name"] == "Jane"


def test_list_employees_search(client):
    c, db = client
    make_employee(db)
    assert c.get("/employees?search=Jane").json()["total"] == 1
    assert c.get("/employees?search=NOMATCH").json()["total"] == 0


def test_list_employees_department_filter(client):
    c, db = client
    _, dept, _ = make_employee(db)
    r = c.get(f"/employees?department_id={dept.id}")
    assert r.json()["total"] == 1


def test_list_employees_pagination(client):
    c, db = client
    dept    = Department(name="Sales")
    country = Country(name="Canada", currency_code="CAD")
    role    = Role(title="Rep", level="junior")
    db.add_all([dept, country, role]); db.flush()
    for i in range(5):
        db.add(Employee(first_name=f"User{i}", last_name="T", email=f"u{i}@x.com",
                        hire_date=date(2022,1,1), department_id=dept.id,
                        country_id=country.id, role_id=role.id))
    db.flush()
    r = c.get("/employees?page=1&page_size=3")
    assert r.json()["total"] == 5
    assert len(r.json()["items"]) == 3


def test_get_employee(client):
    c, db = client
    emp, _, _ = make_employee(db)
    r = c.get(f"/employees/{emp.id}")
    assert r.status_code == 200
    assert r.json()["email"] == "jane@acme.com"


def test_get_employee_not_found(client):
    c, _ = client
    assert c.get("/employees/99999").status_code == 404


def test_update_salary_creates_record(client):
    c, db = client
    emp, _, _ = make_employee(db)
    r = c.put(f"/employees/{emp.id}/salary", json={
        "amount": 95000, "currency": "USD",
        "effective_date": "2024-01-01", "reason": "Promotion"
    })
    assert r.status_code == 200
    assert r.json()["amount"] == 95000.0
    assert r.json()["reason"] == "Promotion"


def test_update_salary_not_found(client):
    c, _ = client
    r = c.put("/employees/99999/salary", json={
        "amount": 50000, "currency": "USD", "effective_date": "2024-01-01"
    })
    assert r.status_code == 404


def test_salary_history_preserved(client):
    c, db = client
    emp, _, _ = make_employee(db)
    db.add(Salary(employee_id=emp.id, amount=Decimal("80000"), currency="USD",
                  effective_date=date(2022,1,1), reason="Hire"))
    db.flush()
    c.put(f"/employees/{emp.id}/salary", json={
        "amount": 90000, "currency": "USD", "effective_date": "2023-01-01"
    })
    r = c.get(f"/employees/{emp.id}")
    assert len(r.json()["salary_history"]) == 2


def test_analytics_summary(client):
    c, db = client
    emp, _, _ = make_employee(db)
    db.add(Salary(employee_id=emp.id, amount=Decimal("100000"), currency="USD",
                  effective_date=date(2022,1,1), reason="Hire"))
    db.flush()
    r = c.get("/analytics/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_employees"] == 1
    assert data["avg_salary"] == 100000.0


def test_analytics_by_department(client):
    c, db = client
    emp, _, _ = make_employee(db)
    db.add(Salary(employee_id=emp.id, amount=Decimal("100000"), currency="USD",
                  effective_date=date(2022,1,1), reason="Hire"))
    db.flush()
    r = c.get("/analytics/by-department")
    assert r.status_code == 200
    assert r.json()[0]["name"] == "Engineering"
    assert r.json()[0]["avg"] == 100000.0


def test_meta_departments(client):
    c, db = client
    db.add(Department(name="Finance"))
    db.flush()
    r = c.get("/meta/departments")
    assert any(d["name"] == "Finance" for d in r.json())


def test_meta_countries(client):
    c, db = client
    db.add(Country(name="Germany", currency_code="EUR"))
    db.flush()
    r = c.get("/meta/countries")
    assert any(d["name"] == "Germany" for d in r.json())
