import email


def parse_email(msg_data):

    raw_email = msg_data[0][1]

    email_message = email.message_from_bytes(raw_email)

    subject = email_message["Subject"]
    sender = email_message["From"]
    date = email_message["Date"]

    body = ""

    if email_message.is_multipart():

        for part in email_message.walk():

            if part.get_content_type() == "text/plain":

                body = part.get_payload(decode=True).decode()

                break

    else:

        body = email_message.get_payload(decode=True).decode()

    return sender, subject, date, body