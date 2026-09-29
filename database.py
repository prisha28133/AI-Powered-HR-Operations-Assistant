import mysql.connector

from config import (
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    HR_EMAIL
)


def connect_db():

    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# -------------------------------------------------
# Generate Message ID
# -------------------------------------------------

def generate_message_id():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Message_ID
        FROM Email_Transaction
        ORDER BY Message_ID DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return "MSG001"

    last_id = row[0]
    number = int(last_id.replace("MSG", "")) + 1

    return f"MSG{number:03d}"


# -------------------------------------------------
# Generate Review ID
# -------------------------------------------------

def generate_review_id():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Review_ID
        FROM Human_Review
        ORDER BY Review_ID DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return "REV001"

    last_id = row[0]
    number = int(last_id.replace("REV", "")) + 1

    return f"REV{number:03d}"


# -------------------------------------------------
# Insert Email Transaction
# -------------------------------------------------

def insert_email_transaction(
    employee_id,
    subject,
    body,
    received_datetime
):

    conn = connect_db()
    cursor = conn.cursor()

    message_id = generate_message_id()

    query = """
    INSERT INTO Email_Transaction
    (
        Message_ID,
        Employee_ID,
        To_Email,
        Subject,
        Email_Body,
        Received_Datetime,
        Processing_Status
    )
    VALUES
    (%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        message_id,
        employee_id,
        HR_EMAIL,
        subject,
        body,
        received_datetime,
        "Pending"
    )

    cursor.execute(query, values)

    conn.commit()

    cursor.close()
    conn.close()

    return message_id