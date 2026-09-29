from database import connect_db
from datetime import datetime, date


def validate_attendance(
    employee_id,
    attendance_date,
    correction_type,
    message_id
):

    conn = connect_db()
    cursor = conn.cursor()

    validation = {}


    # ---------------------------------------
    # Validate Attendance Date
    # ---------------------------------------

    if not attendance_date:
        validation["attendance_exists"] = False
        validation["within_limit"] = False
        validation["duplicate"] = False
        validation["invalid_date"] = True

        print(" Attendance date was not extracted from email.")

        cursor.close()
        conn.close()

        return validation

    validation["invalid_date"] = False

    # ---------------------------------------
    # Employee Exists
    # ---------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM Employee_Master
        WHERE Employee_ID = %s
    """, (employee_id,))

    validation["employee_exists"] = cursor.fetchone()[0] > 0

    # ---------------------------------------
    # Attendance Exists
    # ---------------------------------------

    cursor.execute("""
        SELECT
            Check_In_Time,
            Check_Out_Time,
            Status
        FROM Attendance_Transaction
        WHERE Employee_ID = %s
        AND Attendance_Date = %s
    """, (
        employee_id,
        attendance_date
    ))

    attendance_row = cursor.fetchone()

    validation["attendance_exists"] = attendance_row is not None

    # ---------------------------------------
    # Within 3 Days
    # ---------------------------------------

    cursor.execute("""
        SELECT DATEDIFF(CURDATE(), %s)
    """, (attendance_date,))

    days = cursor.fetchone()[0]

    validation["within_limit"] = 0 <= days <= 3

    # ---------------------------------------
    # Get Current Attendance Details
    # ---------------------------------------

    check_in = None
    check_out = None
    status = None

    if attendance_row:

        check_in = attendance_row[0]
        check_out = attendance_row[1]
        status = attendance_row[2]

    validation["check_in"] = check_in
    validation["check_out"] = check_out
    validation["attendance_status"] = status

    # ---------------------------------------
    # Duplicate / Already Corrected Check
    # ---------------------------------------

    duplicate = False

    if attendance_row:

        # Missing Check-In
        if correction_type == "Missing Check-In":

            # If check-in is already present,
            # this correction has already been completed.
            if check_in is not None:
                duplicate = True

        # Missing Check-Out
        elif correction_type == "Missing Check-Out":

            # If check-out is already present,
            # this correction has already been completed.
            if check_out is not None:
                duplicate = True

    validation["duplicate"] = duplicate

    # ---------------------------------------
    # Duplicate Check Output
    # ---------------------------------------

    print(" DUPLICATE CHECK")
    print("Employee ID:", employee_id)
    print("Attendance Date:", attendance_date)
    print("Correction Type:", correction_type)
    print("Message ID:", message_id)
    print("Current Check-In:", check_in)
    print("Current Check-Out:", check_out)
    print("Attendance Status:", status)
    print("Duplicate Result:", validation["duplicate"])

    # ---------------------------------------
    # Close Connection
    # ---------------------------------------

    cursor.close()
    conn.close()

    return validation