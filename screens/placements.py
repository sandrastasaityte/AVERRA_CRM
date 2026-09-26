import streamlit as st

from database import get_session
from models import (
    Client,
    Employee,
    Job,
    Candidate,
    Placement,
    Contract,
    Invoice,
    Payment
)


def show_reports():

    st.title("Reports")
    st.caption("AVERRA CRM business and financial reports.")

    session = get_session()

    # ============================================================
    # LOAD DATA
    # ============================================================

    clients = session.query(Client).all()
    employees = session.query(Employee).all()
    jobs = session.query(Job).all()
    candidates = session.query(Candidate).all()
    placements = session.query(Placement).all()
    contracts = session.query(Contract).all()
    invoices = session.query(Invoice).all()
    payments = session.query(Payment).all()

    # ============================================================
    # SUMMARY
    # ============================================================

    st.subheader("CRM Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Clients",
            len(clients)
        )

    with col2:

        st.metric(
            "Employees",
            len(employees)
        )

    with col3:

        st.metric(
            "Open Jobs",
            len([
                job
                for job in jobs
                if job.status == "Open"
            ])
        )

    with col4:

        st.metric(
            "Placements",
            len(placements)
        )

    # ============================================================
    # RECRUITMENT PIPELINE
    # ============================================================

    st.divider()

    st.subheader("Recruitment Pipeline")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Jobs",
            len(jobs)
        )

    with col2:

        st.metric(
            "Candidates",
            len(candidates)
        )

    with col3:

        st.metric(
            "Placements",
            len(placements)
        )

    with col4:

        active_placements = len([
            placement
            for placement in placements
            if placement.status in [
                "Planned",
                "Active"
            ]
        ])

        st.metric(
            "Active Placements",
            active_placements
        )

    # ============================================================
    # JOB STATUS
    # ============================================================

    st.divider()

    st.subheader("Jobs by Status")

    if jobs:

        job_statuses = {}

        for job in jobs:

            status = job.status or "Unknown"

            job_statuses[status] = (
                job_statuses.get(status, 0) + 1
            )

        for status, count in job_statuses.items():

            st.write(
                f"**{status}:** {count}"
            )

    else:

        st.info("No jobs available.")

    # ============================================================
    # CANDIDATE STATUS
    # ============================================================

    st.divider()

    st.subheader("Candidates by Status")

    if candidates:

        candidate_statuses = {}

        for candidate in candidates:

            status = candidate.status or "Unknown"

            candidate_statuses[status] = (
                candidate_statuses.get(status, 0) + 1
            )

        for status, count in candidate_statuses.items():

            st.write(
                f"**{status}:** {count}"
            )

    else:

        st.info("No candidates available.")

    # ============================================================
    # PLACEMENT FINANCIALS
    # ============================================================

    st.divider()

    st.subheader("Placement Financials")

    if placements:

        total_revenue = 0.0
        total_worker_cost = 0.0
        total_margin = 0.0

        for placement in placements:

            revenue = float(
                placement.client_monthly_fee or 0
            )

            worker_cost = float(
                placement.worker_monthly_cost or 0
            )

            margin = revenue - worker_cost

            total_revenue += revenue
            total_worker_cost += worker_cost
            total_margin += margin

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Monthly Client Revenue",
                f"£{total_revenue:,.2f}"
            )

        with col2:

            st.metric(
                "Monthly Worker Cost",
                f"£{total_worker_cost:,.2f}"
            )

        with col3:

            st.metric(
                "Monthly Gross Margin",
                f"£{total_margin:,.2f}"
            )

    else:

        st.info(
            "No placements available."
        )

    # ============================================================
    # PLACEMENT REGISTER
    # ============================================================

    st.subheader("Placement Register")

    if placements:

        for placement in placements:

            client_name = (
                placement.client.company_name
                if placement.client
                else "Unknown Client"
            )

            employee_name = "Unknown Employee"

            if placement.employee:

                employee_name = (
                    f"{placement.employee.first_name} "
                    f"{placement.employee.last_name or ''}"
                ).strip()

            position = (
                placement.position
                or (
                    placement.job.position
                    if placement.job
                    else "No position"
                )
            )

            revenue = float(
                placement.client_monthly_fee or 0
            )

            worker_cost = float(
                placement.worker_monthly_cost or 0
            )

            margin = revenue - worker_cost

            if revenue:

                margin_percentage = (
                    margin / revenue
                ) * 100

            else:

                margin_percentage = 0

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.write(
                        f"**Placement #{placement.id}**"
                    )

                    st.caption(
                        client_name
                    )

                with col2:

                    st.write(
                        f"**{employee_name}**"
                    )

                    st.caption(
                        position
                    )

                with col3:

                    st.write(
                        f"Revenue: **"
                        f"{placement.currency} "
                        f"{revenue:,.2f}"
                        f"**"
                    )

                    st.write(
                        f"Worker Cost: **"
                        f"{placement.currency} "
                        f"{worker_cost:,.2f}"
                        f"**"
                    )

                with col4:

                    st.write(
                        f"Margin: **"
                        f"{placement.currency} "
                        f"{margin:,.2f}"
                        f"**"
                    )

                    st.caption(
                        f"Margin %: "
                        f"{margin_percentage:.1f}%"
                    )

    else:

        st.info(
            "No placements available."
        )

    # ============================================================
    # CONTRACT SUMMARY
    # ============================================================

    st.divider()

    st.subheader("Contracts")

    contract_statuses = {}

    for contract in contracts:

        status = contract.status or "Unknown"

        contract_statuses[status] = (
            contract_statuses.get(status, 0) + 1
        )

    if contract_statuses:

        for status, count in contract_statuses.items():

            st.write(
                f"**{status}:** {count}"
            )

    else:

        st.info(
            "No contracts available."
        )

    # ============================================================
    # INVOICE SUMMARY
    # ============================================================

    st.divider()

    st.subheader("Invoice Summary")

    total_invoiced = 0.0
    total_paid = 0.0
    total_outstanding = 0.0

    for invoice in invoices:

        total = float(
            invoice.total_amount or 0
        )

        paid = float(
            invoice.amount_paid or 0
        )

        balance = max(
            total - paid,
            0
        )

        total_invoiced += total
        total_paid += paid
        total_outstanding += balance

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Invoiced",
            f"£{total_invoiced:,.2f}"
        )

    with col2:

        st.metric(
            "Total Paid",
            f"£{total_paid:,.2f}"
        )

    with col3:

        st.metric(
            "Outstanding",
            f"£{total_outstanding:,.2f}"
        )

    # ============================================================
    # INVOICE STATUS
    # ============================================================

    if invoices:

        st.subheader("Invoices by Status")

        invoice_statuses = {}

        for invoice in invoices:

            status = invoice.status or "Unknown"

            invoice_statuses[status] = (
                invoice_statuses.get(status, 0) + 1
            )

        for status, count in invoice_statuses.items():

            st.write(
                f"**{status}:** {count}"
            )

    # ============================================================
    # PAYMENT SUMMARY
    # ============================================================

    st.divider()

    st.subheader("Payments")

    total_payments = 0.0

    for payment in payments:

        total_payments += float(
            payment.amount or 0
        )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Payments Received",
            len(payments)
        )

    with col2:

        st.metric(
            "Payment Value",
            f"£{total_payments:,.2f}"
        )

    # ============================================================
    # CLIENT SUMMARY
    # ============================================================

    st.divider()

    st.subheader("Client Summary")

    if clients:

        for client in clients:

            client_jobs = [
                job
                for job in jobs
                if job.client_id == client.id
            ]

            client_placements = [
                placement
                for placement in placements
                if placement.client_id == client.id
            ]

            client_invoices = [
                invoice
                for invoice in invoices
                if invoice.client_id == client.id
            ]

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.write(
                        f"**{client.company_name}**"
                    )

                    st.caption(
                        client.status or ""
                    )

                with col2:

                    st.write(
                        f"Jobs: **{len(client_jobs)}**"
                    )

                with col3:

                    st.write(
                        f"Placements: **"
                        f"{len(client_placements)}**"
                    )

                with col4:

                    st.write(
                        f"Invoices: **"
                        f"{len(client_invoices)}**"
                    )

    else:

        st.info(
            "No clients available."
        )

    # ============================================================
    # CLOSE SESSION
    # ============================================================

    session.close()