from database import connect_db


def process_wfh_request(
    message_id,
    employee_id,
    from_date,
    to_date,
    reason,
    received_datetime
):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.callproc(
        "sp_Process_WFH_Request",
        (
            message_id,
            employee_id,
            from_date,
            to_date,
            reason,
            received_datetime
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    print("✅ WFH Stored Procedure Executed Successfully")