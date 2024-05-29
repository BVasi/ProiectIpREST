import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from constants import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    EMAIL_SUBJECT,
    FROM,
    TO,
    SUBJECT,
    PLAIN,
    GMAIL_SERVER,
    PORT
)

class Email():
    def __init__(self, receiver, message_content):
        self.sender = ADMIN_EMAIL
        self.receiver = receiver
        self.subject = EMAIL_SUBJECT
        self.message = message_content

    def send(self):
        email = MIMEMultipart()
        email[FROM] = self.sender
        email[TO] = self.receiver
        email[SUBJECT] = self.subject
        email.attach(MIMEText(self.message, PLAIN))
        with smtplib.SMTP(GMAIL_SERVER, PORT) as server:
            server.starttls()
            server.login(self.sender, ADMIN_PASSWORD)
            server.sendmail(self.sender, self.receiver, email.as_string())