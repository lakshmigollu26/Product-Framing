from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"
    id   = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    employees = relationship("Employee", back_populates="department")


class Country(Base):
    __tablename__ = "countries"
    id            = Column(Integer, primary_key=True)
    name          = Column(String, unique=True, nullable=False)
    currency_code = Column(String(3), nullable=False)
    employees     = relationship("Employee", back_populates="country")


class Role(Base):
    __tablename__ = "roles"
    id    = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    level = Column(String, nullable=False)   # junior / mid / senior / lead / manager
    employees = relationship("Employee", back_populates="role")


class Employee(Base):
    __tablename__ = "employees"
    id            = Column(Integer, primary_key=True, index=True)
    first_name    = Column(String, nullable=False)
    last_name     = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False, index=True)
    hire_date     = Column(Date, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    country_id    = Column(Integer, ForeignKey("countries.id"),    nullable=False)
    role_id       = Column(Integer, ForeignKey("roles.id"),        nullable=False)
    department    = relationship("Department", back_populates="employees")
    country       = relationship("Country",    back_populates="employees")
    role          = relationship("Role",       back_populates="employees")
    salaries      = relationship("Salary", back_populates="employee",
                                 order_by="Salary.effective_date.desc()")


class Salary(Base):
    __tablename__ = "salaries"
    id             = Column(Integer, primary_key=True)
    employee_id    = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    amount         = Column(Numeric(12, 2), nullable=False)
    currency       = Column(String(3), nullable=False, default="USD")
    effective_date = Column(Date, nullable=False)
    reason         = Column(String, nullable=True)
    created_at     = Column(DateTime, server_default=func.now())
    employee       = relationship("Employee", back_populates="salaries")
