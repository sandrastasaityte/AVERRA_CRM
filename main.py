import streamlit as st

from database import create_database

from dashboard import show_dashboard

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
    initial_sidebar_state="expanded",
)


# ============================================================
# DATABASE INITIALISATION
# ============================================================

create_database()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("AVERRA CRM")

st.sidebar.caption(
    "Staffing & Outsourcing Management"
)

st.sidebar.divider()


# ============================================================
# NAVIGATION
# ============================================================

NAVIGATION_OPTIONS = [
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
    "Reports",
]


page = st.sidebar.radio(
    "Navigation",
    NAVIGATION_OPTIONS,
)


# ============================================================
# PAGE ROUTING
# ============================================================

if page == "Dashboard":

    show_dashboard()


elif page == "Clients":

    show_clients()


elif page == "Client Contacts":

    show_client_contacts()


elif page == "Activities":

    show_activities()


elif page == "Employees":

    show_employees()


elif page == "Employee Skills":

    show_employee_skills()


elif page == "Jobs":

    show_jobs()


elif page == "Candidates":

    show_candidates()


elif page == "Placements":

    show_placements()


elif page == "Contracts":

    show_contracts()


elif page == "Invoices":

    show_invoices()


elif page == "Payments":

    show_payments()


elif page == "Reports":

    show_reports()


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "AVERRA CRM • Staffing & Outsourcing"
)