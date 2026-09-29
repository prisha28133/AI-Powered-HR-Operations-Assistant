from database import connect_db
from datetime import datetime, timedelta, date


# =========================================================
# DATE CONVERSION
# =========================================================

def convert_to_date(value):

    # Blank / missing date
    if value is None or str(value).strip() == "":
        return None

    # Already datetime
    if isinstance(value, datetime):
        return value.date()

    # Already date
    if isinstance(value, date):
        return value

    # String date
    if isinstance(value, str):

        value = value.strip()

        # -------------------------------------------------
        # Format: 2026-09-04
        # -------------------------------------------------

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            pass

        # -------------------------------------------------
        # Format: 4 September 2026
        # -------------------------------------------------

        try:
            return datetime.strptime(
                value,
                "%d %B %Y"
            ).date()

        except ValueError:
            pass

        # -------------------------------------------------
        # Format: 04 September 2026
        # -------------------------------------------------

        try:
            return datetime.strptime(
                value,
                "%d %B %Y"
            ).date()

        except ValueError:
            pass

        # -------------------------------------------------
        # Format: 4 September, 2026
        # -------------------------------------------------

        try:
            return datetime.strptime(
                value,
                "%d %B, %Y"
            ).date()

        except ValueError:
            pass

        # -------------------------------------------------
        # Format: 04/09/2026
        # -------------------------------------------------

        try:
            return datetime.strptime(
                value,
                "%d/%m/%Y"
            ).date()

        except ValueError:
            pass

        # -------------------------------------------------
        # Format: 04-09-2026
        # -------------------------------------------------

        try:
            return datetime.strptime(
                value,
                "%d-%m-%Y"
            ).date()

        except ValueError:
            pass

    raise ValueError(
        f"Unsupported date format: {value}"
    )


# =========================================================
# CALCULATE WORKING DAYS
# Saturday and Sunday are NOT counted
# =========================================================

def calculate_working_days(start_date, end_date):

    start_date = convert_to_date(start_date)
    end_date = convert_to_date(end_date)

    # If either date is missing
    if start_date is None or end_date is None:
        return 0

    working_days = 0

    current_date = start_date

    while current_date <= end_date:

        # Monday = 0
        # Tuesday = 1
        # Wednesday = 2
        # Thursday = 3
        # Friday = 4
        # Saturday = 5
        # Sunday = 6

        if current_date.weekday() < 5:
            working_days += 1

        current_date += timedelta(days=1)

    return working_days


# =========================================================
# VALIDATE LEAVE
# =========================================================

def validate_leave(
    employee_id,
    leave_type,
    start_date,
    end_date
):

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    validation = {}

    # =====================================================
    # CONVERT DATES
    # =====================================================

    start_date = convert_to_date(start_date)

    if end_date is not None and str(end_date).strip() != "":
        end_date = convert_to_date(end_date)

    else:
        end_date = None


    # =====================================================
    # INVALID DATE RANGE
    # =====================================================

    if start_date is None:

        validation["invalid_dates"] = True
        validation["leave_days"] = 0

    # =====================================================
    # MATERNITY LEAVE
    # =====================================================

    elif leave_type == "Maternity Leave":

        # Maternity Leave only requires a start date
        validation["invalid_dates"] = False

        validation["leave_days"] = None


    # =====================================================
    # NORMAL LEAVE
    # =====================================================

    elif end_date is None:

        validation["invalid_dates"] = True

        validation["leave_days"] = 0


    elif start_date > end_date:

        validation["invalid_dates"] = True

        validation["leave_days"] = 0


    else:

        validation["invalid_dates"] = False

        # Calculate only working days
        leave_days = calculate_working_days(
            start_date,
            end_date
        )

        validation["leave_days"] = leave_days


    # =====================================================
    # EMPLOYEE EXISTS
    # =====================================================

    cursor.execute("""
        SELECT Employee_ID
        FROM Employee_Master
        WHERE Employee_ID = %s
    """, (employee_id,))

    validation["employee_exists"] = (
        cursor.fetchone() is not None
    )


    # =====================================================
    # LEAVE BALANCE
    # =====================================================

    leave_column_map = {

        "Paid Leave":
            "Paid_Leave",

        "Floater Leave":
            "Floater_Leave",

        "Bereavement Leave":
            "Bereavement_Leave",

        "Unpaid Leave":
            "Unpaid_Leave",

        "Leave Without Pay":
            "Unpaid_Leave",

        "LWP":
            "Unpaid_Leave",

        "Compensatory Off":
            "Compensatory_Off",

        "Maternity Leave":
            "Maternity_Leave",

        "Paternity Leave":
            "Paternity_Leave",

        "Birthday Leave":
            "Birthday_Leave",

        "Anniversary Leave":
            "Anniversary_Leave",

        "Marriage Anniversary Leave":
            "Anniversary_Leave"
    }


    leave_column = leave_column_map.get(
        leave_type
    )


    if leave_column:

        cursor.execute(
            f"""
            SELECT `{leave_column}`
            FROM Leave_Balance
            WHERE Employee_ID = %s
            """,
            (employee_id,)
        )

        row = cursor.fetchone()


        if row:

            validation["leave_balance"] = (
                row[leave_column]
            )

        else:

            validation["leave_balance"] = None


    else:

        validation["leave_balance"] = None


    # =====================================================
    # DUPLICATE LEAVE
    # =====================================================

    # Only perform duplicate check when dates exist
    if start_date is not None and end_date is not None:

        cursor.execute("""
            SELECT *
            FROM Leave_Transaction
            WHERE Employee_ID = %s
            AND Start_Date = %s
            AND End_Date = %s
        """, (
            employee_id,
            start_date,
            end_date
        ))

        validation["duplicate"] = (
            cursor.fetchone() is not None
        )

    else:

        validation["duplicate"] = False


    # =====================================================
    # CLOSE DATABASE CONNECTION
    # =====================================================

    cursor.close()
    conn.close()


    # =====================================================
    # RETURN VALIDATION
    # =====================================================

    return validation