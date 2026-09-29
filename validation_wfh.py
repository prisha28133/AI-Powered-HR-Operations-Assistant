from database import connect_db


def validate_wfh(employee_id, from_date, to_date):

    conn = connect_db()
    cursor = conn.cursor()

    validation = {}

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
    # WFH Used This Month
    # ---------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM WFH_Transaction
        WHERE Employee_ID = %s
        AND MONTH(From_Date) = MONTH(%s)
        AND YEAR(From_Date) = YEAR(%s)
        AND Status = 'Approved'
    """, (
        employee_id,
        from_date,
        from_date
    ))

    used = cursor.fetchone()[0]

    validation["wfh_used"] = used
    validation["wfh_remaining"] = 5 - used

    # ---------------------------------------
    # Duplicate WFH
    # ---------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM WFH_Transaction
        WHERE Employee_ID = %s
        AND From_Date = %s
        AND To_Date = %s
        AND Status = 'Approved'
    """, (
        employee_id,
        from_date,
        to_date
    ))

    validation["duplicate"] = cursor.fetchone()[0] > 0

    cursor.close()
    conn.close()

    return validation