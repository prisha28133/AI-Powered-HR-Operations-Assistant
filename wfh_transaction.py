from database import connect_db

def insert_wfh_transaction(
    message_id,
    employee_id,
    from_date,
    to_date,
    reason,
    applied_date
):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT IFNULL(
            MAX(CAST(SUBSTRING(WFH_Transaction_ID,4) AS UNSIGNED)),
            0
        )
        FROM WFH_Transaction
    """)

    last_id = int(cursor.fetchone()[0] or 0)

    new_id = f"WFH{last_id+1:03d}"

    cursor.execute("""
        INSERT INTO WFH_Transaction
        (
            WFH_Transaction_ID,
            Message_ID,
            Employee_ID,
            From_Date,
            To_Date,
            Reason,
            Applied_Date,
            Status,
            Remarks
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,
            'Pending',
            'Awaiting AI Review'
        )
    """,
    (
        new_id,
        message_id,
        employee_id,
        from_date,
        to_date,
        reason,
        applied_date
    ))

    conn.commit()

    cursor.close()
    conn.close()

    print(f"✅ WFH Transaction inserted : {new_id}")