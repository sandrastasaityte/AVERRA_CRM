from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    Text,
    ForeignKey
)

from sqlalchemy.orm import relationship

from database import Base


# ==========================================================
# CLIENT
# ==========================================================

class Client(Base):

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)

    company_name = Column(
        String(200),
        nullable=False
    )

    industry = Column(String(100))

    website = Column(String(300))

    country = Column(
        String(100),
        default="United Kingdom"
    )

    city = Column(String(100))

    address = Column(String(300))

    postcode = Column(String(30))

    company_size = Column(String(100))

    status = Column(
        String(50),
        default="Lead"
    )

    lead_source = Column(String(100))

    date_added = Column(Date)

    next_follow_up = Column(Date)

    account_owner = Column(String(100))

    notes = Column(Text)

    contacts = relationship(
        "ClientContact",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    jobs = relationship(
        "Job",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    placements = relationship(
        "Placement",
        back_populates="client"
    )


# ==========================================================
# CLIENT CONTACT
# ==========================================================

class ClientContact(Base):

    __tablename__ = "client_contacts"

    id = Column(Integer, primary_key=True)

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    first_name = Column(String(100))

    last_name = Column(String(100))

    job_title = Column(String(150))

    email = Column(String(200))

    phone = Column(String(50))

    linkedin = Column(String(300))

    preferred_contact = Column(
        String(50)
    )

    primary_contact = Column(
        String(20),
        default="No"
    )

    status = Column(
        String(50),
        default="Active"
    )

    notes = Column(Text)

    client = relationship(
        "Client",
        back_populates="contacts"
    )


# ==========================================================
# EMPLOYEE
# ==========================================================

class Employee(Base):

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)

    first_name = Column(String(100))

    last_name = Column(String(100))

    country = Column(
        String(100),
        default="India"
    )

    city = Column(String(100))

    email = Column(String(200))

    phone = Column(String(50))

    role = Column(String(150))

    years_experience = Column(
        Float,
        default=0
    )

    english_level = Column(String(50))

    availability = Column(String(100))

    expected_monthly_rate = Column(
        Float,
        default=0
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    employment_status = Column(
        String(50),
        default="Sourced"
    )

    cv_link = Column(String(500))

    notes = Column(Text)

    skills = relationship(
        "EmployeeSkill",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    placements = relationship(
        "Placement",
        back_populates="employee"
    )


# ==========================================================
# EMPLOYEE SKILL
# ==========================================================

class EmployeeSkill(Base):

    __tablename__ = "employee_skills"

    id = Column(Integer, primary_key=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    skill = Column(String(150))

    category = Column(String(100))

    level = Column(String(50))

    years_used = Column(
        Float,
        default=0
    )

    qualification = Column(String(200))

    notes = Column(Text)

    employee = relationship(
        "Employee",
        back_populates="skills"
    )


# ==========================================================
# JOB
# ==========================================================

class Job(Base):

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    position = Column(
        String(200),
        nullable=False
    )

    department = Column(String(100))

    skills_required = Column(Text)

    experience_required = Column(String(200))

    client_budget = Column(
        Float,
        default=0
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    openings = Column(
        Integer,
        default=1
    )

    work_pattern = Column(String(100))

    remote_country = Column(
        String(100),
        default="India"
    )

    date_opened = Column(Date)

    closing_date = Column(Date)

    status = Column(
        String(50),
        default="Open"
    )

    priority = Column(
        String(50),
        default="Medium"
    )

    notes = Column(Text)

    client = relationship(
        "Client",
        back_populates="jobs"
    )

    candidates = relationship(
        "Candidate",
        back_populates="job",
        cascade="all, delete-orphan"
    )


# ==========================================================
# CANDIDATE
# ==========================================================

class Candidate(Base):

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    date_submitted = Column(Date)

    status = Column(
        String(50),
        default="New"
    )

    interview_date = Column(Date)

    client_feedback = Column(Text)

    decision_date = Column(Date)

    notes = Column(Text)

    job = relationship(
        "Job",
        back_populates="candidates"
    )

    employee = relationship(
        "Employee"
    )


# ==========================================================
# PLACEMENT
# ==========================================================

class Placement(Base):

    __tablename__ = "placements"

    id = Column(Integer, primary_key=True)

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=True
    )

    position = Column(String(200))

    start_date = Column(Date)

    end_date = Column(Date)

    client_monthly_fee = Column(
        Float,
        default=0
    )

    worker_monthly_cost = Column(
        Float,
        default=0
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    billing_frequency = Column(
        String(50),
        default="Monthly"
    )

    status = Column(
        String(50),
        default="Planned"
    )

    notes = Column(Text)

    client = relationship(
        "Client",
        back_populates="placements"
    )

    employee = relationship(
        "Employee",
        back_populates="placements"
    )

    @property
    def gross_margin(self):

        return (
            self.client_monthly_fee or 0
        ) - (
            self.worker_monthly_cost or 0
        )

    @property
    def gross_margin_percentage(self):

        if not self.client_monthly_fee:
            return 0

        return (
            self.gross_margin
            / self.client_monthly_fee
        ) * 100