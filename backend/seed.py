"""
Seed 10,000 employees. Run: python seed.py
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Department, Country, Role, Employee, Salary

fake = Faker()
random.seed(42)
Faker.seed(42)

DEPARTMENTS = ["Engineering","Product","Design","Data Science","Marketing",
               "Sales","Finance","Legal","HR","Customer Success","IT","Security"]

COUNTRIES = [
    ("United States","USD",1.0), ("United Kingdom","GBP",0.88),
    ("Germany","EUR",0.72),      ("France","EUR",0.70),
    ("India","INR",0.22),        ("Canada","CAD",0.82),
    ("Australia","AUD",0.85),    ("Singapore","SGD",0.95),
    ("Brazil","BRL",0.28),       ("Japan","JPY",0.68),
]

ROLES = [
    ("Software Engineer","junior",55_000,85_000),
    ("Software Engineer","mid",85_000,120_000),
    ("Software Engineer","senior",120_000,165_000),
    ("Engineering Manager","manager",160_000,220_000),
    ("Product Manager","mid",90_000,130_000),
    ("Senior Product Manager","senior",130_000,170_000),
    ("UX Designer","mid",80_000,115_000),
    ("Data Scientist","mid",90_000,130_000),
    ("Data Scientist","senior",130_000,175_000),
    ("Marketing Manager","mid",70_000,100_000),
    ("Sales Representative","junior",45_000,65_000),
    ("Account Executive","mid",65_000,95_000),
    ("Financial Analyst","junior",55_000,80_000),
    ("HR Business Partner","mid",70_000,100_000),
    ("Security Engineer","senior",130_000,175_000),
    ("DevOps Engineer","mid",90_000,130_000),
    ("Customer Success Manager","mid",65_000,95_000),
]

REASONS = ["Annual review", "Promotion", "Market adjustment", "Role change"]


def seed():
    engine = create_engine("sqlite:///./salary.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("Clearing old data…")
    for model in [Salary, Employee, Role, Department, Country]:
        db.query(model).delete()
    db.commit()

    depts   = [db.add(Department(name=n)) or db.query(Department).filter_by(name=n).first()
               for n in DEPARTMENTS]
    db.commit()
    depts   = db.query(Department).all()

    countries = []
    for name, code, _ in COUNTRIES:
        c = Country(name=name, currency_code=code)
        db.add(c)
    db.commit()
    countries = db.query(Country).all()
    country_multiplier = {c.name: m for c, (_, _, m) in zip(countries, COUNTRIES)}

    roles = []
    for title, level, lo, hi in ROLES:
        db.add(Role(title=title, level=level))
    db.commit()
    roles = db.query(Role).all()
    role_range = {r.id: ROLES[i][2:4] for i, r in enumerate(roles)}

    print("Seeding 10,000 employees…")
    for i in range(10_000):
        role    = random.choice(roles)
        country = random.choice(countries)
        dept    = random.choice(depts)
        emp = Employee(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            hire_date=fake.date_between(date(2010,1,1), date(2024,6,30)),
            department_id=dept.id,
            country_id=country.id,
            role_id=role.id,
        )
        db.add(emp)
        db.flush()

        lo, hi   = role_range[role.id]
        mult     = country_multiplier.get(country.name, 0.7)
        amount   = round(random.uniform(lo, hi) * mult, 2)
        cur_date = emp.hire_date

        db.add(Salary(employee_id=emp.id, amount=Decimal(str(amount)),
                      currency=country.currency_code, effective_date=cur_date,
                      reason="Initial salary"))

        for _ in range(random.choices([0,1,2], weights=[40,40,20])[0]):
            cur_date = cur_date + timedelta(days=random.randint(180, 730))
            if cur_date > date(2024, 12, 31): break
            amount = round(amount * random.uniform(1.02, 1.12), 2)
            db.add(Salary(employee_id=emp.id, amount=Decimal(str(amount)),
                          currency=country.currency_code, effective_date=cur_date,
                          reason=random.choice(REASONS)))

        if (i + 1) % 1000 == 0:
            db.commit()
            print(f"  {i+1}/10000")

    db.commit()
    db.close()
    print("Done.")


if __name__ == "__main__":
    seed()
