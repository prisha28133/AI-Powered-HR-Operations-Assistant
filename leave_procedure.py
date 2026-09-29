from database import connect_db


def process_leave_request(
    message_id,
    employee_id,
    leave_type,
    start_date,
    end_date,
    reason,
    received_datetime
):

    conn = connect_db()
    cursor = conn.cursor()

    try:

        cursor.callproc(
            "sp_Process_Leave_Request",
            (
                message_id,
                employee_id,
                leave_type,
                start_date,
                end_date,
                reason,
                received_datetime
            )
        )

        procedure_status = None
        procedure_remarks = None

        # Read the result returned by the stored procedure
        for result in cursor.stored_results():

            rows = result.fetchall()

            if rows:
                print("📌 Stored Procedure Result:")
                print(rows)

                # Stored procedure returns:
                # Status, Remarks
                procedure_status = rows[0][0]
                procedure_remarks = rows[0][1]

        # The stored procedure itself handles COMMIT/ROLLBACK.
        # We do not need to perform another transaction here.

        if procedure_status == "Approved":

            print("✅ Leave Stored Procedure Executed Successfully")
            print(f"Status: {procedure_status}")
            print(f"Remarks: {procedure_remarks}")

            return True

        elif procedure_status == "Rejected":

            print("❌ Leave Request Rejected")
            print(f"Status: {procedure_status}")
            print(f"Remarks: {procedure_remarks}")

            return False

        elif procedure_status == "ERROR":

            print("❌ Leave Stored Procedure Failed")
            print(f"Status: {procedure_status}")
            print(f"Remarks: {procedure_remarks}")

            return False

        else:

            print("⚠️ No valid response received from Leave Stored Procedure")
            return False

    except Exception as e:

        conn.rollback()

        print("❌ Leave Stored Procedure Error:")
        print(e)

        return False

    finally:

        cursor.close()
        conn.close()