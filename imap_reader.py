import imaplib

from config import EMAIL, APP_PASSWORD, IMAP_SERVER

mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(EMAIL, APP_PASSWORD)

mail.select("INBOX")

status, messages = mail.search(None, "UNSEEN")

email_ids = messages[0].split()