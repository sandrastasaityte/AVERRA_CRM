import csv
import io
from datetime import date, datetime


# ============================================================
# SAFE HELPERS
# ============================================================

def clean_text(value):
    """
    Safely convert a value to clean text.
    """
    if value is None:
        return ""

    return str(value).strip()


def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def format_date(value):
    """
    Format dates consistently for CSV export.
    """
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    text = clean_text(value)

    if not text:
        return ""

    return text


def format_datetime(value):
    """
    Format datetime values consistently.
    """
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    return clean_text(value)


def format_money(value, currency=None):
    """
    Format money for CSV export.
    """
    amount = safe_float(value)

    if currency:
        currency_text = clean_text(currency).upper()

        if currency_text:
            return f"{currency_text} {amount:,.2f}"

    return f"{amount:,.2f}"


def get_attr(record, name, default=""):
    """
    Safely retrieve an attribute.
    """
    try:
        value = getattr(record, name, default)

        if value is None:
            return default

        return value

    except Exception:
        return default


def get_client_name(client):
    """
    Safely retrieve client company name.
    """
    if not client:
        return "Unknown Client"

    company_name = clean_text(
        get_attr(
            client,
            "company_name",
            "",
        )
    )

    return company_name or "Unnamed Client"


def get_employee_name(employee):
    """
    Safely retrieve employee full name.
    """
    if not employee:
        return "Unknown Employee"

    first_name = clean_text(
        get_attr(
            employee,
            "first_name",
            "",
        )
    )

    last_name = clean_text(
        get_attr(
            employee,
            "last_name",
            "",
        )
    )

    full_name = f"{first_name} {last_name}".strip()

    return full_name or "Unnamed Employee"


def get_job_label(job):
    """
    Safely retrieve job label.
    """
    if not job:
        return "Unknown Job"

    position = clean_text(
        get_attr(
            job,
            "position",
            "",
        )
    )

    job_id = get_attr(
        job,
        "id",
        None,
    )

    if position and job_id:
        return f"{position} #{job_id}"

    return position or "Unnamed Job"


def get_candidate_label(candidate):
    """
    Safely retrieve candidate label.
    """
    if not candidate:
        return "Unknown Candidate"

    first_name = clean_text(
        get_attr(
            candidate,
            "first_name",
            "",
        )
    )

    last_name = clean_text(
        get_attr(
            candidate,
            "last_name",
            "",
        )
    )

    name = f"{first_name} {last_name}".strip()

    if not name:
        name = clean_text(
            get_attr(
                candidate,
                "name",
                "",
            )
        )

    candidate_id = get_attr(
        candidate,
        "id",
        None,
    )

    if name and candidate_id:
        return f"{name} #{candidate_id}"

    return name or "Unnamed Candidate"


def get_placement_label(placement):
    """
    Safely retrieve placement label.
    """
    if not placement:
        return "Unknown Placement"

    position = clean_text(
        get_attr(
            placement,
            "position",
            "",
        )
    )

    placement_id = get_attr(
        placement,
        "id",
        None,
    )

    if position and placement_id:
        return f"{position} #{placement_id}"

    return position or "Unnamed Placement"


def get_contract_label(contract):
    """
    Safely retrieve contract label.
    """
    if not contract:
        return "Unknown Contract"

    contract_number = clean_text(
        get_attr(
            contract,
            "contract_number",
            "",
        )
    )

    contract_id = get_attr(
        contract,
        "id",
        None,
    )

    if contract_number:
        return contract_number

    if contract_id:
        return f"Contract #{contract_id}"

    return "Unnamed Contract"


def get_invoice_label(invoice):
    """
    Safely retrieve invoice label.
    """
    if not invoice:
        return "Unknown Invoice"

    invoice_number = clean_text(
        get_attr(
            invoice,
            "invoice_number",
            "",
        )
    )

    invoice_id = get_attr(
        invoice,
        "id",
        None,
    )

    if invoice_number:
        return invoice_number

    if invoice_id:
        return f"Invoice #{invoice_id}"

    return "Unnamed Invoice"


# ============================================================
# CSV CORE FUNCTIONS
# ============================================================

def rows_to_csv(
    rows,
    headers=None,
):
    """
    Convert a list of dictionaries to CSV text.

    Returns UTF-8 compatible CSV text.
    """
    rows = rows or []

    if headers is None:

        if rows:
            headers = list(
                rows[0].keys()
            )

        else:
            headers = []

    output = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        output,
        fieldnames=headers,
        extrasaction="ignore",
    )

    writer.writeheader()

    for row in rows:
        clean_row = {}

        for header in headers:
            value = row.get(
                header,
                "",
            )

            if value is None:
                value = ""

            clean_row[header] = value

        writer.writerow(
            clean_row
        )

    return output.getvalue()


def records_to_csv(
    records,
    fields,
):
    """
    Generic SQLAlchemy record exporter.

    fields can be:
        ["id", "name", "status"]

    or:

        {
            "ID": "id",
            "Name": "name",
            "Status": "status",
        }
    """
    records = records or []

    if isinstance(fields, dict):
        headers = list(
            fields.keys()
        )

        field_names = list(
            fields.values()
        )

    else:
        headers = list(fields)
        field_names = list(fields)

    rows = []

    for record in records:

        row = {}

        for header, field_name in zip(
            headers,
            field_names,
        ):

            row[header] = get_attr(
                record,
                field_name,
                "",
            )

        rows.append(row)

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# CLIENT EXPORT
# ============================================================

def export_clients(clients):
    """
    Export clients to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Company Name",
        "Status",
        "Lead Source",
        "Industry",
        "Company Size",
        "Country",
        "Website",
        "Email",
        "Phone",
        "Address",
        "City",
        "Postcode",
        "Notes",
    ]

    for client in clients or []:

        rows.append(
            {
                "ID": get_attr(
                    client,
                    "id",
                    "",
                ),
                "Company Name": get_attr(
                    client,
                    "company_name",
                    "",
                ),
                "Status": get_attr(
                    client,
                    "status",
                    "",
                ),
                "Lead Source": get_attr(
                    client,
                    "lead_source",
                    "",
                ),
                "Industry": get_attr(
                    client,
                    "industry",
                    "",
                ),
                "Company Size": get_attr(
                    client,
                    "company_size",
                    "",
                ),
                "Country": get_attr(
                    client,
                    "country",
                    "",
                ),
                "Website": get_attr(
                    client,
                    "website",
                    "",
                ),
                "Email": get_attr(
                    client,
                    "email",
                    "",
                ),
                "Phone": get_attr(
                    client,
                    "phone",
                    "",
                ),
                "Address": get_attr(
                    client,
                    "address",
                    "",
                ),
                "City": get_attr(
                    client,
                    "city",
                    "",
                ),
                "Postcode": get_attr(
                    client,
                    "postcode",
                    "",
                ),
                "Notes": get_attr(
                    client,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# CLIENT CONTACT EXPORT
# ============================================================

def export_client_contacts(
    contacts,
):
    """
    Export client contacts to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Client",
        "First Name",
        "Last Name",
        "Job Title",
        "Email",
        "Phone",
        "LinkedIn",
        "Primary Contact",
        "Status",
        "Preferred Method",
        "Notes",
    ]

    for contact in contacts or []:

        client = get_attr(
            contact,
            "client",
            None,
        )

        rows.append(
            {
                "ID": get_attr(
                    contact,
                    "id",
                    "",
                ),
                "Client": get_client_name(
                    client
                ),
                "First Name": get_attr(
                    contact,
                    "first_name",
                    "",
                ),
                "Last Name": get_attr(
                    contact,
                    "last_name",
                    "",
                ),
                "Job Title": get_attr(
                    contact,
                    "job_title",
                    "",
                ),
                "Email": get_attr(
                    contact,
                    "email",
                    "",
                ),
                "Phone": get_attr(
                    contact,
                    "phone",
                    "",
                ),
                "LinkedIn": get_attr(
                    contact,
                    "linkedin",
                    "",
                ),
                "Primary Contact": get_attr(
                    contact,
                    "primary_contact",
                    "",
                ),
                "Status": get_attr(
                    contact,
                    "status",
                    "",
                ),
                "Preferred Method": get_attr(
                    contact,
                    "preferred_method",
                    "",
                ),
                "Notes": get_attr(
                    contact,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# EMPLOYEE EXPORT
# ============================================================

def export_employees(
    employees,
):
    """
    Export employees to CSV.
    """
    rows = []

    headers = [
        "ID",
        "First Name",
        "Last Name",
        "Email",
        "Phone",
        "Country",
        "City",
        "Job Title",
        "Department",
        "Employment Type",
        "Status",
        "Start Date",
        "End Date",
        "Salary",
        "Currency",
        "Notes",
    ]

    for employee in employees or []:

        rows.append(
            {
                "ID": get_attr(
                    employee,
                    "id",
                    "",
                ),
                "First Name": get_attr(
                    employee,
                    "first_name",
                    "",
                ),
                "Last Name": get_attr(
                    employee,
                    "last_name",
                    "",
                ),
                "Email": get_attr(
                    employee,
                    "email",
                    "",
                ),
                "Phone": get_attr(
                    employee,
                    "phone",
                    "",
                ),
                "Country": get_attr(
                    employee,
                    "country",
                    "",
                ),
                "City": get_attr(
                    employee,
                    "city",
                    "",
                ),
                "Job Title": get_attr(
                    employee,
                    "job_title",
                    "",
                ),
                "Department": get_attr(
                    employee,
                    "department",
                    "",
                ),
                "Employment Type": get_attr(
                    employee,
                    "employment_type",
                    "",
                ),
                "Status": get_attr(
                    employee,
                    "status",
                    "",
                ),
                "Start Date": format_date(
                    get_attr(
                        employee,
                        "start_date",
                        None,
                    )
                ),
                "End Date": format_date(
                    get_attr(
                        employee,
                        "end_date",
                        None,
                    )
                ),
                "Salary": get_attr(
                    employee,
                    "salary",
                    "",
                ),
                "Currency": get_attr(
                    employee,
                    "currency",
                    "",
                ),
                "Notes": get_attr(
                    employee,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# EMPLOYEE SKILLS EXPORT
# ============================================================

def export_employee_skills(
    skills,
):
    """
    Export employee skills to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Employee",
        "Category",
        "Skill",
        "Level",
        "Years Experience",
        "Notes",
    ]

    for skill in skills or []:

        employee = get_attr(
            skill,
            "employee",
            None,
        )

        rows.append(
            {
                "ID": get_attr(
                    skill,
                    "id",
                    "",
                ),
                "Employee": get_employee_name(
                    employee
                ),
                "Category": get_attr(
                    skill,
                    "category",
                    "",
                ),
                "Skill": get_attr(
                    skill,
                    "skill",
                    "",
                ),
                "Level": get_attr(
                    skill,
                    "level",
                    "",
                ),
                "Years Experience": get_attr(
                    skill,
                    "years_experience",
                    "",
                ),
                "Notes": get_attr(
                    skill,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# JOB EXPORT
# ============================================================

def export_jobs(jobs):
    """
    Export jobs to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Client",
        "Position",
        "Department",
        "Skills Required",
        "Experience Required",
        "Client Budget",
        "Currency",
        "Openings",
        "Work Pattern",
        "Remote Country",
        "Date Opened",
        "Closing Date",
        "Status",
        "Priority",
        "Notes",
    ]

    for job in jobs or []:

        client = get_attr(
            job,
            "client",
            None,
        )

        rows.append(
            {
                "ID": get_attr(
                    job,
                    "id",
                    "",
                ),
                "Client": get_client_name(
                    client
                ),
                "Position": get_attr(
                    job,
                    "position",
                    "",
                ),
                "Department": get_attr(
                    job,
                    "department",
                    "",
                ),
                "Skills Required": get_attr(
                    job,
                    "skills_required",
                    "",
                ),
                "Experience Required": get_attr(
                    job,
                    "experience_required",
                    "",
                ),
                "Client Budget": get_attr(
                    job,
                    "client_budget",
                    "",
                ),
                "Currency": get_attr(
                    job,
                    "currency",
                    "",
                ),
                "Openings": get_attr(
                    job,
                    "openings",
                    "",
                ),
                "Work Pattern": get_attr(
                    job,
                    "work_pattern",
                    "",
                ),
                "Remote Country": get_attr(
                    job,
                    "remote_country",
                    "",
                ),
                "Date Opened": format_date(
                    get_attr(
                        job,
                        "date_opened",
                        None,
                    )
                ),
                "Closing Date": format_date(
                    get_attr(
                        job,
                        "closing_date",
                        None,
                    )
                ),
                "Status": get_attr(
                    job,
                    "status",
                    "",
                ),
                "Priority": get_attr(
                    job,
                    "priority",
                    "",
                ),
                "Notes": get_attr(
                    job,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# CANDIDATE EXPORT
# ============================================================

def export_candidates(
    candidates,
):
    """
    Export candidates to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Candidate",
        "First Name",
        "Last Name",
        "Email",
        "Phone",
        "Job",
        "Client",
        "Status",
        "Interview Date",
        "Application Date",
        "Expected Salary",
        "Currency",
        "Notes",
    ]

    for candidate in candidates or []:

        job = get_attr(
            candidate,
            "job",
            None,
        )

        client = (
            get_attr(
                job,
                "client",
                None,
            )
            if job
            else None
        )

        rows.append(
            {
                "ID": get_attr(
                    candidate,
                    "id",
                    "",
                ),
                "Candidate": get_candidate_label(
                    candidate
                ),
                "First Name": get_attr(
                    candidate,
                    "first_name",
                    "",
                ),
                "Last Name": get_attr(
                    candidate,
                    "last_name",
                    "",
                ),
                "Email": get_attr(
                    candidate,
                    "email",
                    "",
                ),
                "Phone": get_attr(
                    candidate,
                    "phone",
                    "",
                ),
                "Job": get_job_label(
                    job
                ),
                "Client": get_client_name(
                    client
                ),
                "Status": get_attr(
                    candidate,
                    "status",
                    "",
                ),
                "Interview Date": format_date(
                    get_attr(
                        candidate,
                        "interview_date",
                        None,
                    )
                ),
                "Application Date": format_date(
                    get_attr(
                        candidate,
                        "application_date",
                        None,
                    )
                ),
                "Expected Salary": get_attr(
                    candidate,
                    "expected_salary",
                    "",
                ),
                "Currency": get_attr(
                    candidate,
                    "currency",
                    "",
                ),
                "Notes": get_attr(
                    candidate,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# PLACEMENT EXPORT
# ============================================================

def export_placements(
    placements,
):
    """
    Export placements to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Client",
        "Employee",
        "Job",
        "Position",
        "Start Date",
        "End Date",
        "Client Monthly Fee",
        "Worker Monthly Cost",
        "Gross Margin",
        "Margin %",
        "Currency",
        "Billing Frequency",
        "Status",
        "Notes",
    ]

    for placement in placements or []:

        client = get_attr(
            placement,
            "client",
            None,
        )

        employee = get_attr(
            placement,
            "employee",
            None,
        )

        job = get_attr(
            placement,
            "job",
            None,
        )

        fee = safe_float(
            get_attr(
                placement,
                "client_monthly_fee",
                0,
            )
        )

        cost = safe_float(
            get_attr(
                placement,
                "worker_monthly_cost",
                0,
            )
        )

        margin = fee - cost

        margin_percentage = (
            margin / fee * 100
            if fee
            else 0
        )

        currency = clean_text(
            get_attr(
                placement,
                "currency",
                "",
            )
        ).upper()

        rows.append(
            {
                "ID": get_attr(
                    placement,
                    "id",
                    "",
                ),
                "Client": get_client_name(
                    client
                ),
                "Employee": get_employee_name(
                    employee
                ),
                "Job": get_job_label(
                    job
                ),
                "Position": get_attr(
                    placement,
                    "position",
                    "",
                ),
                "Start Date": format_date(
                    get_attr(
                        placement,
                        "start_date",
                        None,
                    )
                ),
                "End Date": format_date(
                    get_attr(
                        placement,
                        "end_date",
                        None,
                    )
                ),
                "Client Monthly Fee": fee,
                "Worker Monthly Cost": cost,
                "Gross Margin": margin,
                "Margin %": round(
                    margin_percentage,
                    2,
                ),
                "Currency": currency,
                "Billing Frequency": get_attr(
                    placement,
                    "billing_frequency",
                    "",
                ),
                "Status": get_attr(
                    placement,
                    "status",
                    "",
                ),
                "Notes": get_attr(
                    placement,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# CONTRACT EXPORT
# ============================================================

def export_contracts(
    contracts,
):
    """
    Export contracts to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Contract Number",
        "Client",
        "Placement",
        "Contract Type",
        "Start Date",
        "End Date",
        "Contract Value",
        "Currency",
        "Status",
        "Signed Date",
        "Renewal Date",
        "Document Link",
        "Notes",
    ]

    for contract in contracts or []:

        client = get_attr(
            contract,
            "client",
            None,
        )

        placement = get_attr(
            contract,
            "placement",
            None,
        )

        rows.append(
            {
                "ID": get_attr(
                    contract,
                    "id",
                    "",
                ),
                "Contract Number": get_attr(
                    contract,
                    "contract_number",
                    "",
                ),
                "Client": get_client_name(
                    client
                ),
                "Placement": get_placement_label(
                    placement
                ),
                "Contract Type": get_attr(
                    contract,
                    "contract_type",
                    "",
                ),
                "Start Date": format_date(
                    get_attr(
                        contract,
                        "start_date",
                        None,
                    )
                ),
                "End Date": format_date(
                    get_attr(
                        contract,
                        "end_date",
                        None,
                    )
                ),
                "Contract Value": get_attr(
                    contract,
                    "contract_value",
                    "",
                ),
                "Currency": get_attr(
                    contract,
                    "currency",
                    "",
                ),
                "Status": get_attr(
                    contract,
                    "status",
                    "",
                ),
                "Signed Date": format_date(
                    get_attr(
                        contract,
                        "signed_date",
                        None,
                    )
                ),
                "Renewal Date": format_date(
                    get_attr(
                        contract,
                        "renewal_date",
                        None,
                    )
                ),
                "Document Link": get_attr(
                    contract,
                    "document_link",
                    "",
                ),
                "Notes": get_attr(
                    contract,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# INVOICE EXPORT
# ============================================================

def export_invoices(
    invoices,
    payments=None,
):
    """
    Export invoices to CSV.

    Payments are optional. If supplied, received payments
    can be calculated from the payment records.
    """
    payments = payments or []

    rows = []

    headers = [
        "ID",
        "Invoice Number",
        "Client",
        "Placement",
        "Description",
        "Issue Date",
        "Due Date",
        "Subtotal",
        "Tax",
        "Total Amount",
        "Amount Paid",
        "Outstanding",
        "Currency",
        "Status",
        "Document Link",
        "Notes",
    ]

    for invoice in invoices or []:

        client = get_attr(
            invoice,
            "client",
            None,
        )

        placement = get_attr(
            invoice,
            "placement",
            None,
        )

        total = safe_float(
            get_attr(
                invoice,
                "total_amount",
                0,
            )
        )

        stored_paid = safe_float(
            get_attr(
                invoice,
                "amount_paid",
                0,
            )
        )

        invoice_id = get_attr(
            invoice,
            "id",
            None,
        )

        related_payments = [
            payment
            for payment in payments
            if getattr(
                payment,
                "invoice_id",
                None,
            ) == invoice_id
        ]

        received_from_payments = 0.0

        for payment in related_payments:

            status = clean_text(
                get_attr(
                    payment,
                    "status",
                    "",
                )
            ).lower()

            if status in [
                "received",
                "paid",
                "completed",
                "successful",
            ]:

                received_from_payments += safe_float(
                    get_attr(
                        payment,
                        "amount",
                        0,
                    )
                )

        if stored_paid > 0:
            amount_paid = stored_paid

        else:
            amount_paid = received_from_payments

        outstanding = max(
            total - amount_paid,
            0.0,
        )

        rows.append(
            {
                "ID": invoice_id,
                "Invoice Number": get_attr(
                    invoice,
                    "invoice_number",
                    "",
                ),
                "Client": get_client_name(
                    client
                ),
                "Placement": get_placement_label(
                    placement
                ),
                "Description": get_attr(
                    invoice,
                    "description",
                    "",
                ),
                "Issue Date": format_date(
                    get_attr(
                        invoice,
                        "issue_date",
                        None,
                    )
                ),
                "Due Date": format_date(
                    get_attr(
                        invoice,
                        "due_date",
                        None,
                    )
                ),
                "Subtotal": get_attr(
                    invoice,
                    "subtotal",
                    "",
                ),
                "Tax": get_attr(
                    invoice,
                    "tax",
                    "",
                ),
                "Total Amount": total,
                "Amount Paid": amount_paid,
                "Outstanding": outstanding,
                "Currency": get_attr(
                    invoice,
                    "currency",
                    "",
                ),
                "Status": get_attr(
                    invoice,
                    "status",
                    "",
                ),
                "Document Link": get_attr(
                    invoice,
                    "document_link",
                    "",
                ),
                "Notes": get_attr(
                    invoice,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# PAYMENT EXPORT
# ============================================================

def export_payments(
    payments,
):
    """
    Export payments to CSV.
    """
    rows = []

    headers = [
        "ID",
        "Invoice",
        "Client",
        "Payment Date",
        "Amount",
        "Currency",
        "Status",
        "Payment Method",
        "Reference",
        "Notes",
    ]

    for payment in payments or []:

        invoice = get_attr(
            payment,
            "invoice",
            None,
        )

        currency = clean_text(
            get_attr(
                payment,
                "currency",
                "",
            )
        ).upper()

        if not currency and invoice:
            currency = clean_text(
                get_attr(
                    invoice,
                    "currency",
                    "",
                )
            ).upper()

        amount = safe_float(
            get_attr(
                payment,
                "amount",
                0,
            )
        )

        rows.append(
            {
                "ID": get_attr(
                    payment,
                    "id",
                    "",
                ),
                "Invoice": get_invoice_label(
                    invoice
                ),
                "Client": get_client_name(
                    get_attr(
                        invoice,
                        "client",
                        None,
                    )
                    if invoice
                    else None
                ),
                "Payment Date": format_date(
                    get_attr(
                        payment,
                        "payment_date",
                        None,
                    )
                ),
                "Amount": amount,
                "Currency": currency,
                "Status": get_attr(
                    payment,
                    "status",
                    "",
                ),
                "Payment Method": get_attr(
                    payment,
                    "payment_method",
                    "",
                ),
                "Reference": get_attr(
                    payment,
                    "reference",
                    "",
                ),
                "Notes": get_attr(
                    payment,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# ACTIVITY / GENERAL EXPORT
# ============================================================

def export_activities(
    activities,
):
    """
    Export activities to CSV.

    This function is intentionally flexible so it can work
    with the current Activity model even if additional fields
    are added later.
    """
    rows = []

    headers = [
        "ID",
        "Activity Type",
        "Subject",
        "Activity Date",
        "Due Date",
        "Status",
        "Priority",
        "Client",
        "Contact",
        "Assigned Employee",
        "Job",
        "Candidate",
        "Placement",
        "Contract",
        "Notes",
    ]

    for activity in activities or []:

        client = get_attr(
            activity,
            "client",
            None,
        )

        contact = get_attr(
            activity,
            "contact",
            None,
        )

        employee = get_attr(
            activity,
            "assigned_employee",
            None,
        )

        job = get_attr(
            activity,
            "job",
            None,
        )

        candidate = get_attr(
            activity,
            "candidate",
            None,
        )

        placement = get_attr(
            activity,
            "placement",
            None,
        )

        contract = get_attr(
            activity,
            "contract",
            None,
        )

        contact_first = clean_text(
            get_attr(
                contact,
                "first_name",
                "",
            )
        )

        contact_last = clean_text(
            get_attr(
                contact,
                "last_name",
                "",
            )
        )

        contact_name = (
            f"{contact_first} {contact_last}".strip()
        )

        if not contact_name:
            contact_name = "Unknown Contact"

        rows.append(
            {
                "ID": get_attr(
                    activity,
                    "id",
                    "",
                ),
                "Activity Type": get_attr(
                    activity,
                    "activity_type",
                    "",
                ),
                "Subject": get_attr(
                    activity,
                    "subject",
                    "",
                ),
                "Activity Date": format_datetime(
                    get_attr(
                        activity,
                        "activity_date",
                        None,
                    )
                ),
                "Due Date": format_date(
                    get_attr(
                        activity,
                        "due_date",
                        None,
                    )
                ),
                "Status": get_attr(
                    activity,
                    "status",
                    "",
                ),
                "Priority": get_attr(
                    activity,
                    "priority",
                    "",
                ),
                "Client": get_client_name(
                    client
                ),
                "Contact": contact_name,
                "Assigned Employee": get_employee_name(
                    employee
                ),
                "Job": get_job_label(
                    job
                ),
                "Candidate": get_candidate_label(
                    candidate
                ),
                "Placement": get_placement_label(
                    placement
                ),
                "Contract": get_contract_label(
                    contract
                ),
                "Notes": get_attr(
                    activity,
                    "notes",
                    "",
                ),
            }
        )

    return rows_to_csv(
        rows,
        headers,
    )


# ============================================================
# DASHBOARD SUMMARY EXPORT
# ============================================================

def export_dashboard_summary(
    clients=None,
    employees=None,
    jobs=None,
    candidates=None,
    placements=None,
    contracts=None,
    invoices=None,
    payments=None,
):
    """
    Export a high-level CRM dashboard summary.

    Financial values remain separated by currency.
    """
    clients = clients or []
    employees = employees or []
    jobs = jobs or []
    candidates = candidates or []
    placements = placements or []
    contracts = contracts or []
    invoices = invoices or []
    payments = payments or []

    active_clients = sum(
        1
        for client in clients
        if clean_text(
            get_attr(
                client,
                "status",
                "",
            )
        )
        in [
            "Active",
            "Won",
        ]
    )

    open_jobs = sum(
        1
        for job in jobs
        if clean_text(
            get_attr(
                job,
                "status",
                "",
            )
        )
        in [
            "Open",
            "On Hold",
        ]
    )

    active_placements = sum(
        1
        for placement in placements
        if clean_text(
            get_attr(
                placement,
                "status",
                "",
            )
        )
        == "Active"
    )

    overdue_invoices = sum(
        1
        for invoice in invoices
        if clean_text(
            get_attr(
                invoice,
                "status",
                "",
            )
        )
        == "Overdue"
    )

    received_payments = 0

    for payment in payments:

        status = clean_text(
            get_attr(
                payment,
                "status",
                "",
            )
        ).lower()

        if status in [
            "received",
            "paid",
            "completed",
            "successful",
        ]:
            received_payments += 1

    rows = [
        {
            "Metric": "Clients",
            "Value": len(clients),
        },
        {
            "Metric": "Active Clients",
            "Value": active_clients,
        },
        {
            "Metric": "Employees",
            "Value": len(employees),
        },
        {
            "Metric": "Open Jobs",
            "Value": open_jobs,
        },
        {
            "Metric": "Candidates",
            "Value": len(candidates),
        },
        {
            "Metric": "Active Placements",
            "Value": active_placements,
        },
        {
            "Metric": "Contracts",
            "Value": len(contracts),
        },
        {
            "Metric": "Invoices",
            "Value": len(invoices),
        },
        {
            "Metric": "Overdue Invoices",
            "Value": overdue_invoices,
        },
        {
            "Metric": "Payments",
            "Value": len(payments),
        },
        {
            "Metric": "Received Payments",
            "Value": received_payments,
        },
    ]

    return rows_to_csv(
        rows,
        [
            "Metric",
            "Value",
        ],
    )


# ============================================================
# COMBINED CRM EXPORT
# ============================================================

def export_all_data(
    clients=None,
    contacts=None,
    employees=None,
    skills=None,
    jobs=None,
    candidates=None,
    placements=None,
    contracts=None,
    invoices=None,
    payments=None,
    activities=None,
):
    """
    Return all major CRM exports as a dictionary.

    Example:

        exports = export_all_data(
            clients=clients,
            jobs=jobs,
            invoices=invoices,
        )

        clients_csv = exports["clients"]
    """
    return {
        "clients": export_clients(
            clients or []
        ),
        "client_contacts": export_client_contacts(
            contacts or []
        ),
        "employees": export_employees(
            employees or []
        ),
        "employee_skills": export_employee_skills(
            skills or []
        ),
        "jobs": export_jobs(
            jobs or []
        ),
        "candidates": export_candidates(
            candidates or []
        ),
        "placements": export_placements(
            placements or []
        ),
        "contracts": export_contracts(
            contracts or []
        ),
        "invoices": export_invoices(
            invoices or [],
            payments or [],
        ),
        "payments": export_payments(
            payments or []
        ),
        "activities": export_activities(
            activities or []
        ),
    }


# ============================================================
# STREAMLIT DOWNLOAD HELPER
# ============================================================

def csv_download_button(
    label,
    filename,
    csv_data,
    key=None,
):
    """
    Create a Streamlit CSV download button.

    This helper keeps download logic out of individual screens.
    """
    import streamlit as st

    if not csv_data:
        csv_data = ""

    return st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=key,
    )


# ============================================================
# EXPORT FILENAME HELPER
# ============================================================

def make_export_filename(
    name,
    extension="csv",
):
    """
    Create a consistent export filename.

    Example:
        make_export_filename("clients")

    Returns:
        clients_2026-10-01.csv
    """
    clean_name = clean_text(
        name
    )

    clean_name = (
        clean_name
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    if not clean_name:
        clean_name = "export"

    clean_extension = (
        clean_text(
            extension
        ).lstrip(".")
        or "csv"
    )

    today = date.today().isoformat()

    return (
        f"{clean_name}_{today}."
        f"{clean_extension}"
    )