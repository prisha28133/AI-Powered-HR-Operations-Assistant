from database import connect_db


def process_attendance_request(
    message_id,
    employee_id,
    attendance_date,
    correction_type,
    check_in_time,
    check_out_time,
    reason,
    received_date
):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.callproc(
        "sp_Process_Attendance_Correction",
        (
            message_id,
            employee_id,
            attendance_date,
            correction_type,
            check_in_time,
            check_out_time,
            reason,
            received_date
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    print("✅ Attendance Stored Procedure Executed Successfully")