import streamlit as st
import pandas as pd

from datetime import date

from database import create_database, get_session

from models import (
    Client,
    ClientContact,
    Employee,
    EmployeeSkill,
    Job,
    Candidate,
    Placement
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

create_database()

session = get_session()


# --------------------------------------------------
# PAGE
# --------------------------------------------------

st.set_page_config(
    page_title="Averra Staffing Solutions",
    page_icon="💼",
    layout="wide"
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("AVERRA STAFFING SOLUTIONS LTD")

st.caption(
    "Client • Employee • Recruitment • Placement Management System"
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "Clients",
        "Client Contacts",
        "Employees",
        "Jobs",
        "Candidates",
        "Placements"
    ]
)


# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":

    st.header("Dashboard")

    clients = session.query(Client).all()
    employees = session.query(Employee).all()
    jobs = session.query(Job).all()
    placements = session.query(Placement).all()

    active_placements = [
        p for p in placements
        if p.status == "Active"
    ]

    revenue = sum(
        p.client_monthly_fee
        for p in active_placements
    )

    worker_cost = sum(
        p.worker_monthly_cost
        for p in active_placements
    )

    gross_margin = revenue - worker_cost

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Clients",
        len(clients)
    )

    col2.metric(
        "Employees",
        len(employees)
    )

    col3.metric(
        "Open Jobs",
        len([
            j for j in jobs
            if j.status == "Open"
        ])
    )

    col4.metric(
        "Active Placements",
        len(active_placements)
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Monthly Revenue",
        f"£{revenue:,.2f}"
    )

    col2.metric(
        "Worker Costs",
        f"£{worker_cost:,.2f}"
    )

    col3.metric(
        "Gross Margin",
        f"£{gross_margin:,.2f}"
    )

    st.divider()

    st.subheader("Client Pipeline")

    pipeline_statuses = [
        "Lead",
        "Contacted",
        "Replied",
        "Call",
        "Proposal",
        "Negotiation",
        "Contract",
        "Won",
        "Lost"
    ]

    pipeline_data = []

    for status in pipeline_statuses:

        count = len([
            c for c in clients
            if c.status == status
        ])

        pipeline_data.append({
            "Status": status,
            "Clients": count
        })

    df = pd.DataFrame(pipeline_data)

    st.bar_chart(
        df.set_index("Status")
    )


# ==================================================
# CLIENTS
# ==================================================

elif page == "Clients":

    st.header("Clients")

    tab1, tab2 = st.tabs(
        ["Client List", "Add Client"]
    )

    with tab1:

        clients = session.query(Client).all()

        search = st.text_input(
            "Search clients"
        )

        if search:

            clients = [
                c for c in clients
                if search.lower()
                in c.company_name.lower()
            ]

        data = []

        for c in clients:

            data.append({
                "ID": f"CL{c.id:04d}",
                "Company": c.company_name,
                "Industry": c.industry,
                "City": c.city,
                "Status": c.status,
                "Lead Source": c.lead_source,
                "Next Follow-up": c.next_follow_up
            })

        if data:

            st.dataframe(
                pd.DataFrame(data),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No clients found."
            )

    with tab2:

        st.subheader("Add New Client")

        with st.form("client_form"):

            company_name = st.text_input(
                "Company Name *"
            )

            industry = st.text_input(
                "Industry"
            )

            website = st.text_input(
                "Website"
            )

            city = st.text_input(
                "City"
            )

            address = st.text_input(
                "Address"
            )

            postcode = st.text_input(
                "Postcode"
            )

            status = st.selectbox(
                "Status",
                [
                    "Lead",
                    "Contacted",
                    "Replied",
                    "Call",
                    "Proposal",
                    "Negotiation",
                    "Contract",
                    "Won",
                    "Lost"
                ]
            )

            lead_source = st.selectbox(
                "Lead Source",
                [
                    "LinkedIn",
                    "Website",
                    "Referral",
                    "Cold Email",
                    "Cold Call",
                    "Job Board",
                    "Networking",
                    "Other"
                ]
            )

            next_follow_up = st.date_input(
                "Next Follow-up",
                value=date.today()
            )

            notes = st.text_area(
                "Notes"
            )

            submitted = st.form_submit_button(
                "Add Client"
            )

            if submitted:

                if not company_name:

                    st.error(
                        "Company name is required."
                    )

                else:

                    client = Client(
                        company_name=company_name,
                        industry=industry,
                        website=website,
                        city=city,
                        address=address,
                        postcode=postcode,
                        status=status,
                        lead_source=lead_source,
                        date_added=date.today(),
                        next_follow_up=next_follow_up,
                        notes=notes
                    )

                    session.add(client)
                    session.commit()

                    st.success(
                        "Client added successfully."
                    )

                    st.rerun()


# ==================================================
# CLIENT CONTACTS
# ==================================================

elif page == "Client Contacts":

    st.header("Client Contacts")

    clients = session.query(Client).all()

    if not clients:

        st.warning(
            "Add a client first."
        )

    else:

        with st.form("contact_form"):

            client = st.selectbox(
                "Client",
                clients,
                format_func=lambda x:
                    x.company_name
            )

            first_name = st.text_input(
                "First Name"
            )

            last_name = st.text_input(
                "Last Name"
            )

            job_title = st.text_input(
                "Job Title"
            )

            email = st.text_input(
                "Email"
            )

            phone = st.text_input(
                "Phone"
            )

            linkedin = st.text_input(
                "LinkedIn"
            )

            primary = st.selectbox(
                "Primary Contact",
                ["Yes", "No"]
            )

            if st.form_submit_button(
                "Add Contact"
            ):

                contact = ClientContact(
                    client_id=client.id,
                    first_name=first_name,
                    last_name=last_name,
                    job_title=job_title,
                    email=email,
                    phone=phone,
                    linkedin=linkedin,
                    primary_contact=primary
                )

                session.add(contact)
                session.commit()

                st.success(
                    "Contact added."
                )

                st.rerun()

    st.divider()

    contacts = session.query(ClientContact).all()

    data = []

    for c in contacts:

        data.append({
            "Client": c.client.company_name
            if c.client else "",
            "Name":
                f"{c.first_name} {c.last_name}",
            "Job Title": c.job_title,
            "Email": c.email,
            "Phone": c.phone,
            "Primary": c.primary_contact
        })

    if data:

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )


# ==================================================
# EMPLOYEES
# ==================================================

elif page == "Employees":

    st.header("Employees / Remote Workers")

    tab1, tab2 = st.tabs(
        ["Employee List", "Add Employee"]
    )

    with tab1:

        employees = session.query(Employee).all()

        search = st.text_input(
            "Search employees"
        )

        if search:

            employees = [
                e for e in employees
                if search.lower()
                in (
                    f"{e.first_name} {e.last_name} {e.role}"
                ).lower()
            ]

        data = []

        for e in employees:

            data.append({
                "ID": f"EMP{e.id:04d}",
                "Name":
                    f"{e.first_name} {e.last_name}",
                "Country": e.country,
                "Role": e.role,
                "Experience":
                    e.years_experience,
                "English":
                    e.english_level,
                "Availability":
                    e.availability,
                "Rate":
                    f"{e.currency} {e.expected_monthly_rate:,.2f}",
                "Status":
                    e.employment_status
            })

        if data:

            st.dataframe(
                pd.DataFrame(data),
                use_container_width=True,
                hide_index=True
            )

    with tab2:

        with st.form("employee_form"):

            first_name = st.text_input(
                "First Name"
            )

            last_name = st.text_input(
                "Last Name"
            )

            city = st.text_input(
                "City"
            )

            email = st.text_input(
                "Email"
            )

            phone = st.text_input(
                "Phone"
            )

            role = st.text_input(
                "Role"
            )

            experience = st.number_input(
                "Years Experience",
                min_value=0.0,
                max_value=50.0,
                step=0.5
            )

            english = st.selectbox(
                "English Level",
                [
                    "Basic",
                    "Intermediate",
                    "Advanced",
                    "Fluent"
                ]
            )

            availability = st.selectbox(
                "Availability",
                [
                    "Available Now",
                    "Available in 1 Week",
                    "Available in 2 Weeks",
                    "Available in 1 Month",
                    "Not Available"
                ]
            )

            rate = st.number_input(
                "Expected Monthly Rate",
                min_value=0.0,
                step=50.0
            )

            status = st.selectbox(
                "Employment Status",
                [
                    "Sourced",
                    "Screened",
                    "Interview",
                    "Approved",
                    "Available",
                    "Submitted",
                    "Placed",
                    "Active",
                    "Finished",
                    "Inactive"
                ]
            )

            cv_link = st.text_input(
                "CV Link"
            )

            notes = st.text_area(
                "Notes"
            )

            submitted = st.form_submit_button(
                "Add Employee"
            )

            if submitted:

                employee = Employee(
                    first_name=first_name,
                    last_name=last_name,
                    city=city,
                    email=email,
                    phone=phone,
                    role=role,
                    years_experience=experience,
                    english_level=english,
                    availability=availability,
                    expected_monthly_rate=rate,
                    employment_status=status,
                    cv_link=cv_link,
                    notes=notes
                )

                session.add(employee)
                session.commit()

                st.success(
                    "Employee added successfully."
                )

                st.rerun()


# ==================================================
# JOBS
# ==================================================

elif page == "Jobs":

    st.header("Job Requirements")

    clients = session.query(Client).all()

    if not clients:

        st.warning(
            "Add a client first."
        )

    else:

        with st.form("job_form"):

            client = st.selectbox(
                "Client",
                clients,
                format_func=lambda x:
                    x.company_name
            )

            position = st.text_input(
                "Position"
            )

            department = st.text_input(
                "Department"
            )

            skills = st.text_area(
                "Skills Required",
                placeholder=
                "Excel, Xero, SQL, accounting..."
            )

            experience = st.text_input(
                "Experience Required"
            )

            budget = st.number_input(
                "Client Monthly Budget",
                min_value=0.0,
                step=100.0
            )

            openings = st.number_input(
                "Number of Openings",
                min_value=1,
                step=1
            )

            work_pattern = st.selectbox(
                "Work Pattern",
                [
                    "Full-time Remote",
                    "Part-time Remote",
                    "Contract",
                    "Other"
                ]
            )

            priority = st.selectbox(
                "Priority",
                [
                    "Low",
                    "Medium",
                    "High",
                    "Urgent"
                ]
            )

            if st.form_submit_button(
                "Create Job"
            ):

                job = Job(
                    client_id=client.id,
                    position=position,
                    department=department,
                    skills_required=skills,
                    experience_required=experience,
                    client_budget=budget,
                    openings= openings,
                    work_pattern=work_pattern,
                    date_opened=date.today(),
                    status="Open",
                    priority=priority
                )

                session.add(job)
                session.commit()

                st.success(
                    "Job created successfully."
                )

                st.rerun()

    st.divider()

    jobs = session.query(Job).all()

    data = []

    for j in jobs:

        data.append({
            "Job ID": f"JOB{j.id:04d}",
            "Client": j.client.company_name
            if j.client else "",
            "Position": j.position,
            "Budget":
                f"£{j.client_budget:,.2f}",
            "Openings": j.openings,
            "Priority": j.priority,
            "Status": j.status
        })

    if data:

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )


# ==================================================
# CANDIDATES
# ==================================================

elif page == "Candidates":

    st.header("Candidates")

    jobs = session.query(Job).all()
    employees = session.query(Employee).all()

    if not jobs or not employees:

        st.warning(
            "You need at least one job and one employee."
        )

    else:

        with st.form("candidate_form"):

            job = st.selectbox(
                "Job",
                jobs,
                format_func=lambda x:
                    f"{x.position} - "
                    f"{x.client.company_name}"
            )

            employee = st.selectbox(
                "Employee",
                employees,
                format_func=lambda x:
                    f"{x.first_name} "
                    f"{x.last_name} - "
                    f"{x.role}"
            )

            status = st.selectbox(
                "Candidate Status",
                [
                    "New",
                    "Screening",
                    "Shortlisted",
                    "Submitted",
                    "Interview",
                    "Offer",
                    "Rejected",
                    "Withdrawn",
                    "Placed"
                ]
            )

            feedback = st.text_area(
                "Client Feedback"
            )

            if st.form_submit_button(
                "Add Candidate"
            ):

                candidate = Candidate(
                    job_id=job.id,
                    employee_id=employee.id,
                    date_submitted=date.today(),
                    status=status,
                    client_feedback=feedback
                )

                session.add(candidate)
                session.commit()

                st.success(
                    "Candidate added."
                )

                st.rerun()

    st.divider()

    candidates = session.query(Candidate).all()

    data = []

    for c in candidates:

        employee = session.get(
            Employee,
            c.employee_id
        )

        data.append({
            "Candidate ID":
                f"CAN{c.id:04d}",
            "Job": c.job.position
            if c.job else "",
            "Employee":
                f"{employee.first_name} "
                f"{employee.last_name}"
                if employee else "",
            "Status": c.status,
            "Submitted":
                c.date_submitted
        })

    if data:

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )


# ==================================================
# PLACEMENTS
# ==================================================

elif page == "Placements":

    st.header("Placements")

    clients = session.query(Client).all()
    employees = session.query(Employee).all()
    jobs = session.query(Job).all()

    if not clients or not employees or not jobs:

        st.warning(
            "You need clients, employees and jobs first."
        )

    else:

        with st.form("placement_form"):

            client = st.selectbox(
                "Client",
                clients,
                format_func=lambda x:
                    x.company_name
            )

            employee = st.selectbox(
                "Employee",
                employees,
                format_func=lambda x:
                    f"{x.first_name} "
                    f"{x.last_name}"
            )

            job = st.selectbox(
                "Job",
                jobs,
                format_func=lambda x:
                    x.position
            )

            position = st.text_input(
                "Position",
                value=job.position
            )

            client_fee = st.number_input(
                "Client Monthly Fee",
                min_value=0.0,
                step=100.0
            )

            worker_cost = st.number_input(
                "Worker Monthly Cost",
                min_value=0.0,
                step=100.0
            )

            start_date = st.date_input(
                "Start Date",
                value=date.today()
            )

            status = st.selectbox(
                "Placement Status",
                [
                    "Planned",
                    "Active",
                    "On Hold",
                    "Ended",
                    "Cancelled"
                ]
            )

            if st.form_submit_button(
                "Create Placement"
            ):

                placement = Placement(
                    client_id=client.id,
                    employee_id=employee.id,
                    job_id=job.id,
                    position=position,
                    start_date=start_date,
                    client_monthly_fee=client_fee,
                    worker_monthly_cost=worker_cost,
                    status=status
                )

                session.add(placement)

                employee.employment_status = "Placed"

                session.commit()

                st.success(
                    "Placement created successfully."
                )

                st.rerun()

    st.divider()

    placements = session.query(
        Placement
    ).all()

    data = []

    for p in placements:

        margin = p.gross_margin

        margin_percent = (
            p.gross_margin_percentage
        )

        data.append({
            "Placement":
                f"PL{p.id:04d}",
            "Client":
                p.client.company_name
                if p.client else "",
            "Employee":
                f"{p.employee.first_name} "
                f"{p.employee.last_name}"
                if p.employee else "",
            "Position":
                p.position,
            "Client Fee":
                f"£{p.client_monthly_fee:,.2f}",
            "Worker Cost":
                f"£{p.worker_monthly_cost:,.2f}",
            "Gross Margin":
                f"£{margin:,.2f}",
            "Margin %":
                f"{margin_percent:.1f}%",
            "Status":
                p.status
        })

    if data:

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )