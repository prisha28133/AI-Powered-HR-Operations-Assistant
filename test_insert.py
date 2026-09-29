from database import insert_email_transaction

message_id = insert_email_transaction(
    employee_id="EMP001",
    subject="Testing Email",
    body="This is a test email inserted from Python.",
    received_datetime="2026-08-10 17:30:00"
)

print("Inserted Successfully!")
print("Message ID:", message_id)
