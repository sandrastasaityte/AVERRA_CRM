from datetime import date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship

from database import Base


# ============================================================
# CLIENTS
# ============================================================

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
        default="UK"
    )

    city = Column(String(100))
    address = Column(String(300))
    postcode = Column(String(30))

    company_size = Column(String(50))

    status = Column(
        String(50),
        default="Lead"
    )

    lead_source = Column(String(100))

    date_added = Column(
        Date,
        default=date.today
    )

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
        back_populates="client"
    )

    placements = relationship(
        "Placement",
        back_populates="client"
    )

    activities = relationship(
        "Activity",
        back_populates="client"
    )

    contracts = relationship(
        "Contract",
        back_populates="client"
    )

    invoices = relationship(
        "Invoice",
        back_populates="client"
    )


# ============================================================
# CLIENT CONTACTS
# ============================================================

class ClientContact(Base):

    __tablename__ = "client_contacts"

    id = Column(
        Integer,
        primary_key=True
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    first_name = Column(
        String(100),
        nullable=False
    )

    last_name = Column(
        String(100)
    )

    job_title = Column(
        String(150)
    )

    email = Column(
        String(200)
    )

    phone = Column(
        String(50)
    )

    linkedin = Column(
        String(300)
    )

    preferred_contact = Column(
        String(50)
    )

    primary_contact = Column(
        String(10),
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

    activities = relationship(
        "Activity",
        back_populates="contact"
    )


# ============================================================
# EMPLOYEES
# ============================================================

class Employee(Base):

    __tablename__ = "employees"

    id = Column(
        Integer,
        primary_key=True
    )

    first_name = Column(
        String(100),
        nullable=False
    )

    last_name = Column(
        String(100)
    )

    country = Column(
        String(100),
        default="India"
    )

    city = Column(
        String(100)
    )

    email = Column(
        String(200)
    )

    phone = Column(
        String(50)
    )

    role = Column(
        String(150)
    )

    years_experience = Column(
        Float
    )

    english_level = Column(
        String(50)
    )

    availability = Column(
        String(50)
    )

    expected_monthly_rate = Column(
        Float
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    employment_status = Column(
        String(50),
        default="Sourced"
    )

    cv_link = Column(
        String(500)
    )

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

    candidates = relationship(
        "Candidate",
        back_populates="employee"
    )

    activities = relationship(
        "Activity",
        back_populates="assigned_employee"
    )


# ============================================================
# EMPLOYEE SKILLS
# ============================================================

class EmployeeSkill(Base):

    __tablename__ = "employee_skills"

    id = Column(
        Integer,
        primary_key=True
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    skill = Column(
        String(150),
        nullable=False
    )

    category = Column(
        String(100)
    )

    level = Column(
        String(50)
    )

    years_used = Column(
        Float
    )

    qualification = Column(
        String(200)
    )

    notes = Column(Text)

    employee = relationship(
        "Employee",
        back_populates="skills"
    )


# ============================================================
# JOBS
# ============================================================

class Job(Base):

    __tablename__ = "jobs"

    id = Column(
        Integer,
        primary_key=True
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    position = Column(
        String(200),
        nullable=False
    )

    department = Column(
        String(150)
    )

    skills_required = Column(
        Text
    )

    experience_required = Column(
        String(150)
    )

    client_budget = Column(
        Float
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    openings = Column(
        Integer,
        default=1
    )

    work_pattern = Column(
        String(100)
    )

    remote_country = Column(
        String(100),
        default="India"
    )

    date_opened = Column(
        Date,
        default=date.today
    )

    closing_date = Column(
        Date
    )

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
        back_populates="job"
    )

    placements = relationship(
        "Placement",
        back_populates="job"
    )

    activities = relationship(
        "Activity",
        back_populates="job"
    )


# ============================================================
# CANDIDATES
# ============================================================

class Candidate(Base):

    __tablename__ = "candidates"

    id = Column(
        Integer,
        primary_key=True
    )

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

    date_submitted = Column(
        Date,
        default=date.today
    )

    status = Column(
        String(50),
        default="New"
    )

    interview_date = Column(
        Date
    )

    client_feedback = Column(
        Text
    )

    decision_date = Column(
        Date
    )

    notes = Column(
        Text
    )

    job = relationship(
        "Job",
        back_populates="candidates"
    )

    employee = relationship(
        "Employee",
        back_populates="candidates"
    )

    activities = relationship(
        "Activity",
        back_populates="candidate"
    )


# ============================================================
# PLACEMENTS
# ============================================================

class Placement(Base):

    __tablename__ = "placements"

    id = Column(
        Integer,
        primary_key=True
    )

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

    position = Column(
        String(200)
    )

    start_date = Column(
        Date
    )

    end_date = Column(
        Date
    )

    client_monthly_fee = Column(
        Float
    )

    worker_monthly_cost = Column(
        Float
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

    notes = Column(
        Text
    )

    client = relationship(
        "Client",
        back_populates="placements"
    )

    employee = relationship(
        "Employee",
        back_populates="placements"
    )

    job = relationship(
        "Job",
        back_populates="placements"
    )

    contracts = relationship(
        "Contract",
        back_populates="placement"
    )

    invoices = relationship(
        "Invoice",
        back_populates="placement"
    )

    activities = relationship(
        "Activity",
        back_populates="placement"
    )

    @property
    def gross_margin(self):

        return (
            (self.client_monthly_fee or 0)
            - (self.worker_monthly_cost or 0)
        )

    @property
    def gross_margin_percentage(self):

        if not self.client_monthly_fee:
            return 0

        return (
            self.gross_margin
            / self.client_monthly_fee
        ) * 100


# ============================================================
# ACTIVITIES
# ============================================================

class Activity(Base):

    __tablename__ = "activities"

    id = Column(
        Integer,
        primary_key=True
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=True
    )

    contact_id = Column(
        Integer,
        ForeignKey("client_contacts.id"),
        nullable=True
    )

    assigned_to_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=True
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=True
    )

    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=True
    )

    placement_id = Column(
        Integer,
        ForeignKey("placements.id"),
        nullable=True
    )

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=True
    )

    activity_type = Column(
        String(50),
        nullable=False
    )

    subject = Column(
        String(200),
        nullable=False
    )

    activity_date = Column(
        Date,
        default=date.today
    )

    due_date = Column(
        Date
    )

    status = Column(
        String(50),
        default="Open"
    )

    priority = Column(
        String(50),
        default="Medium"
    )

    notes = Column(
        Text
    )

    client = relationship(
        "Client",
        back_populates="activities"
    )

    contact = relationship(
        "ClientContact",
        back_populates="activities"
    )

    assigned_employee = relationship(
        "Employee",
        back_populates="activities"
    )

    job = relationship(
        "Job",
        back_populates="activities"
    )

    candidate = relationship(
        "Candidate",
        back_populates="activities"
    )

    placement = relationship(
        "Placement",
        back_populates="activities"
    )

    contract = relationship(
        "Contract",
        back_populates="activities"
    )


# ============================================================
# CONTRACTS
# ============================================================

class Contract(Base):

    __tablename__ = "contracts"

    id = Column(
        Integer,
        primary_key=True
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    placement_id = Column(
        Integer,
        ForeignKey("placements.id"),
        nullable=True
    )

    contract_number = Column(
        String(100),
        unique=True
    )

    contract_type = Column(
        String(100)
    )

    start_date = Column(
        Date
    )

    end_date = Column(
        Date
    )

    contract_value = Column(
        Float
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    status = Column(
        String(50),
        default="Draft"
    )

    signed_date = Column(
        Date
    )

    renewal_date = Column(
        Date
    )

    document_link = Column(
        String(500)
    )

    notes = Column(
        Text
    )

    client = relationship(
        "Client",
        back_populates="contracts"
    )

    placement = relationship(
        "Placement",
        back_populates="contracts"
    )

    activities = relationship(
        "Activity",
        back_populates="contract"
    )


# ============================================================
# INVOICES
# ============================================================

class Invoice(Base):

    __tablename__ = "invoices"

    id = Column(
        Integer,
        primary_key=True
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    placement_id = Column(
        Integer,
        ForeignKey("placements.id"),
        nullable=True
    )

    invoice_number = Column(
        String(100),
        unique=True,
        nullable=False
    )

    invoice_date = Column(
        Date,
        default=date.today
    )

    due_date = Column(
        Date
    )

    description = Column(
        Text
    )

    subtotal = Column(
        Float,
        default=0
    )

    tax = Column(
        Float,
        default=0
    )

    total_amount = Column(
        Float,
        default=0
    )

    amount_paid = Column(
        Float,
        default=0
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    status = Column(
        String(50),
        default="Draft"
    )

    document_link = Column(
        String(500)
    )

    notes = Column(
        Text
    )

    client = relationship(
        "Client",
        back_populates="invoices"
    )

    placement = relationship(
        "Placement",
        back_populates="invoices"
    )

    payments = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    @property
    def balance_due(self):

        return (
            (self.total_amount or 0)
            - (self.amount_paid or 0)
        )


# ============================================================
# PAYMENTS
# ============================================================

class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True
    )

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False
    )

    payment_date = Column(
        Date,
        default=date.today
    )

    amount = Column(
        Float,
        nullable=False
    )

    currency = Column(
        String(10),
        default="GBP"
    )

    payment_method = Column(
        String(100)
    )

    reference = Column(
        String(200)
    )

    status = Column(
        String(50),
        default="Received"
    )

    notes = Column(
        Text
    )

    invoice = relationship(
        "Invoice",
        back_populates="payments"
    )