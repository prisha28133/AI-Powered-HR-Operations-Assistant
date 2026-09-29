from database import connect_db

def insert_leave_transaction(
    message_id,
    employee_id,
    leave_type,
    start_date,
    end_date,
    reason,
    applied_date
):

    conn = connect_db()
    cursor = conn.cursor()

    # Get next Leave Transaction ID
    cursor.execute("""
        SELECT IFNULL(
            MAX(CAST(SUBSTRING(Leave_Transaction_ID,4) AS UNSIGNED)),
            0
        )
        FROM Leave_Transaction
    """)

    last_id = int(cursor.fetchone()[0] or 0)
    new_id = f"LTX{last_id+1:03d}"

    cursor.execute("""
        INSERT INTO Leave_Transaction
        (
            Leave_Transaction_ID,
            Message_ID,
            Employee_ID,
            Leave_Type,
            Start_Date,
            End_Date,
            Reason,
            Applied_Date,
            Status,
            Remarks
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,
            'Pending',
            'Awaiting AI Review'
        )
    """,
    (
        new_id,
        message_id,
        employee_id,
        leave_type,
        start_date,
        end_date,
        reason,
        applied_date
    ))

    conn.commit()

    cursor.close()
    conn.close()

    print("✅ Leave Transaction inserted:", new_id)