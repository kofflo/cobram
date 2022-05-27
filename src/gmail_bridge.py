import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from base_error import BaseError
from utils import to_boolean


class GMailBridge:

    SERVER_URL = 'smtp.gmail.com'
    SERVER_PORT = 465
    GMAIL_ADDRESS = '@gmail.com'
    INVALID_USERNAME = "Invalid username"
    INVALID_PASSWORD = "Invalid password"

    def __init__(self):
        self._username = None
        self._password = None
        self._is_active = True

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        if not isinstance(username, str) or len(username) == 0:
            raise GMailMessageError(GMailBridge.INVALID_USERNAME)
        self._username = username

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if not isinstance(password, str) or len(password) == 0:
            raise GMailMessageError(GMailBridge.INVALID_PASSWORD)
        self._password = password

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, is_active):
        self._is_active = to_boolean(is_active)

    def get_info(self):
        return {'username': self.username, 'is_active': self.is_active}

    def send_gmail(self, *, to, subject, message_text, message_html=None):
        if not self.is_active or self.username is None or self.password is None:
            return

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.username + GMailBridge.GMAIL_ADDRESS
        msg['To'] = ", ".join(to)

        # Record the MIME types of both parts - text/plain and text/html and attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, is best and preferred.
        part_text = MIMEText(message_text, 'plain')
        msg.attach(part_text)
        if message_html is not None:
            part_html = MIMEText(message_html, 'html')
            msg.attach(part_html)

        try:
            server = smtplib.SMTP_SSL(GMailBridge.SERVER_URL, GMailBridge.SERVER_PORT)
            server.login(self.username, self.password)
            server.sendmail(self.username + GMailBridge.GMAIL_ADDRESS, to, msg.as_string())
            server.close()
        except smtplib.SMTPException as e:
            raise GMailMessageError(e)


class GMailMessageError(BaseError):
    _reference_class = GMailBridge
