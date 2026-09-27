from pathlib import Path
from datetime import datetime
import csv


# ============================================================
# EXPORT FOLDER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

EXPORT_DIR = BASE_DIR / "data" / "exports"

EXPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    """
    Convert a value into a CSV-friendly format.
    """

    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def generate_filename(
    prefix,
    extension="csv",
):
    """
    Generate a timestamped export filename.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        f"{prefix}_{timestamp}.{extension}"
    )


def get_export_path(
    filename,
):
    """
    Return the full path inside the exports folder.
    """

    return EXPORT_DIR / filename


# ============================================================
# CSV EXPORT
# ============================================================

def export_to_csv(
    records,
    filename=None,
    fieldnames=None,
):
    """
    Export records to CSV.

    records can be:
    - dictionaries
    - SQLAlchemy model objects
    """

    records = list(records or [])

    if filename is None:
        filename = generate_filename(
            "averra_export"
        )

    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    output_path = get_export_path(filename)

    # --------------------------------------------------------
    # No records
    # --------------------------------------------------------

    if not records:

        if fieldnames is None:
            fieldnames = []

        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

        return output_path

    # --------------------------------------------------------
    # Dictionary records
    # --------------------------------------------------------

    if isinstance(records[0], dict):

        if fieldnames is None:
            fieldnames = list(
                records[0].keys()
            )

        rows = records

    # --------------------------------------------------------
    # SQLAlchemy / object records
    # --------------------------------------------------------

    else:

        if fieldnames is None:

            fieldnames = [
                column.name
                for column in records[0].__table__.columns
            ]

        rows = []

        for record in records:

            row = {}

            for field in fieldnames:

                row[field] = getattr(
                    record,
                    field,
                    "",
                )

            rows.append(row)

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:

            cleaned_row = {
                field: clean_value(
                    row.get(field, "")
                )
                for field in fieldnames
            }

            writer.writerow(
                cleaned_row
            )

    return output_path


# ============================================================
# CSV BY DICTIONARY DATA
# ============================================================

def export_dicts_to_csv(
    rows,
    filename,
):
    """
    Export a list of dictionaries to CSV.
    """

    rows = list(rows or [])

    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    output_path = get_export_path(filename)

    if not rows:

        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ):
            pass

        return output_path

    fieldnames = list(
        rows[0].keys()
    )

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:

            writer.writerow(
                {
                    key: clean_value(
                        row.get(key, "")
                    )
                    for key in fieldnames
                }
            )

    return output_path


# ============================================================
# CSV BY SQLALCHEMY OBJECTS
# ============================================================

def export_models_to_csv(
    records,
    filename,
    fields=None,
):
    """
    Export SQLAlchemy model records to CSV.
    """

    records = list(records or [])

    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    output_path = get_export_path(filename)

    if fields is None:

        if records:

            fields = [
                column.name
                for column in records[0].__table__.columns
            ]

        else:

            fields = []

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()

        for record in records:

            row = {}

            for field in fields:

                row[field] = clean_value(
                    getattr(
                        record,
                        field,
                        "",
                    )
                )

            writer.writerow(row)

    return output_path


# ============================================================
# EXPORT TEXT / CSV DATA FOR STREAMLIT
# ============================================================

def csv_bytes(
    rows,
    fieldnames=None,
):
    """
    Return CSV content as bytes.

    Useful with Streamlit st.download_button().
    """

    rows = list(rows or [])

    if not rows:

        if fieldnames is None:
            fieldnames = []

    elif isinstance(rows[0], dict):

        if fieldnames is None:
            fieldnames = list(
                rows[0].keys()
            )

    else:

        if fieldnames is None:
            fieldnames = [
                column.name
                for column in rows[0].__table__.columns
            ]

    output = []

    # --------------------------------------------------------
    # Build CSV using an in-memory list
    # --------------------------------------------------------

    import io

    buffer = io.StringIO()

    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    for record in rows:

        if isinstance(record, dict):

            row = {
                field: clean_value(
                    record.get(field, "")
                )
                for field in fieldnames
            }

        else:

            row = {
                field: clean_value(
                    getattr(
                        record,
                        field,
                        "",
                    )
                )
                for field in fieldnames
            }

        writer.writerow(row)

    return buffer.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# EXPORT SUMMARY
# ============================================================

def get_export_folder():
    """
    Return the AVERRA CRM export folder.
    """

    return EXPORT_DIR


def list_export_files():
    """
    Return all files currently in the export folder.
    """

    if not EXPORT_DIR.exists():
        return []

    return sorted(
        EXPORT_DIR.iterdir(),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )