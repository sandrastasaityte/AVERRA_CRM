import streamlit as st

from database import create_database

from screens.clients import show_clients
from screens.client_contacts import show_client_contacts
from screens.activities import show_activities
from screens.employees import show_employees
from screens.employee_skills import show_employee_skills
from screens.jobs import show_jobs
from screens.candidates import show_candidates
from screens.placements import show_placements
from screens.contracts import show_contracts
from screens.invoices import show_invoices
from screens.payments import show_payments
from screens.reports import show_reports


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AVERRA CRM",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CREATE DATABASE
# ============================================================

create_database()


# ============================================================
# HEADER
# ============================================================

st.sidebar.title("AVERRA CRM")
st.sidebar.caption("Staffing & Outsourcing Management")


# ============================================================
# NAVIGATION
# ============================================================

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Clients",
        "Client Contacts",
        "Activities",
        "Employees",
        "Employee Skills",
        "Jobs",
        "Candidates",
        "Placements",
        "Contracts",
        "Invoices",
        "Payments",
        "Reports"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("AVERRA CRM")
    st.subheader("Staffing & Outsourcing Management")

    st.write(
        "Welcome to the AVERRA CRM."
    )

    st.info(
        "Use the navigation menu on the left "
        "to manage clients, employees, jobs, "
        "candidates, placements, contracts, "
        "invoices and payments."
    )


# ============================================================
# CLIENTS
# ============================================================

elif page == "Clients":

    show_clients()


# ============================================================
# CLIENT CONTACTS
# ============================================================

elif page == "Client Contacts":

    show_client_contacts()


# ============================================================
# ACTIVITIES
# ============================================================

elif page == "Activities":

    show_activities()


# ============================================================
# EMPLOYEES
# ============================================================

elif page == "Employees":

    show_employees()


# ============================================================
# EMPLOYEE SKILLS
# ============================================================

elif page == "Employee Skills":

    show_employee_skills()


# ============================================================
# JOBS
# ============================================================

elif page == "Jobs":

    show_jobs()


# ============================================================
# CANDIDATES
# ============================================================

elif page == "Candidates":

    show_candidates()


# ============================================================
# PLACEMENTS
# ============================================================

elif page == "Placements":

    show_placements()


# ============================================================
# CONTRACTS
# ============================================================

elif page == "Contracts":

    show_contracts()


# ============================================================
# INVOICES
# ============================================================

elif page == "Invoices":

    show_invoices()


# ============================================================
# PAYMENTS
# ============================================================

elif page == "Payments":

    show_payments()


# ============================================================
# REPORTS
# ============================================================

elif page == "Reports":

    show_reports()