import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def send_reply_email(
    employee_email,
    subject,
    employee_name,
    request_type,
    decision,
    reason
):

    sender_email = os.getenv("EMAIL")
    app_password = os.getenv("APP_PASSWORD")

    if not sender_email or not app_password:
        print("❌ Email credentials not found in .env")
        return False

    # ---------------------------------------
    # Email Subject
    # ---------------------------------------

    reply_subject = f"Re: {subject}"

    # ---------------------------------------
    # Email Body
    # ---------------------------------------

    if decision == "Approved":

        body = f"""Dear {employee_name},

Your {request_type} request has been approved successfully.

Reason:
{reason}

The relevant records have been updated in the HR system.

Regards,
HR Operations
"""

    elif decision == "Rejected":

        body = f"""Dear {employee_name},

Your {request_type} request has been rejected.

Reason:
{reason}

If you have any questions regarding this decision, please contact HR.

Regards,
HR Operations
"""

    elif decision == "Needs Human Review":

        body = f"""Dear {employee_name},

Your {request_type} request has been forwarded for Human Review.

Reason:
{reason}

The HR team will review your request and take the necessary action.

Regards,
HR Operations
"""

    else:

        body = f"""Dear {employee_name},

Your {request_type} request could not be processed automatically.

Reason:
{reason}

Please contact HR for further assistance.

Regards,
HR Operations
"""

    # ---------------------------------------
    # Create Email
    # ---------------------------------------

    message = MIMEMultipart()

    message["From"] = sender_email
    message["To"] = employee_email
    message["Subject"] = reply_subject

    message.attach(MIMEText(body, "plain"))

    # ---------------------------------------
    # Send Email
    # ---------------------------------------

    try:

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

            server.login(
                sender_email,
                app_password
            )

            server.sendmail(
                sender_email,
                employee_email,
                message.as_string()
            )

        print(f"📧 Reply email sent to {employee_email}")

        return True

    except Exception as e:

        print("❌ Failed to send reply email:")
        print(e)

        return False