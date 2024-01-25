import logging
import smtplib
import traceback
import pathlib

from dataclasses import dataclass, field
from functools import partialmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication


logger = logging.getLogger()


class Attachment:
    def __init__(self, filename: pathlib.Path, subtype: str) -> None:
        if not filename.exists():
            logger.exception(FileNotFoundError(f"FileNotFound: {str(filename)}"))
            raise FileNotFoundError
        else:
            self.filename = filename
            self.mime_type = self.get_mime(subtype)
            self.subtype = subtype

    def get_mime(self, mime_type: str) -> MIMEAudio | MIMEApplication:
        if mime_type == "mp3":
            logger.debug(f"Using MIMEaudio")
            return MIMEAudio
        elif mime_type == "xlsx":
            logger.debug(f"Using MIMEApplication")
            return MIMEApplication
        else:
            logger.exception(NotImplementedError(f"NotImplemented - Attempted mime_type {mime_type}"))
            raise NotImplementedError


@dataclass
class RadMail:
    sender: str
    subject: str
    reply_to: str
    recipient: list | str

    server: str
    port: int
    username: str
    password: str

    message: str = ""
    attachments: list = field(default_factory=list)

    header: str = None
    footer: str = None
    body_style: str = "\"margin: 20px\""

    @property
    def footer(self) -> str:
        return self._footer

    @footer.setter
    def footer(self, footer: str) -> None:
        """Overwrite this method for a custom footer"""
        self._footer = f"<div style=\"text-align: center\"><hr width=\"90%\" size=\"5px\" color=\"gray\"><p><b>{footer}</b></p></div>"

    @property
    def header(self) -> str:
        return self._header

    @header.setter
    def header(self, header: str) -> None:
        """Overwrite this method for a custom header"""
        self._header = f"<div class=\"header\"><p>{header}</p></div>"

    def prepare(self) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["Subject"] = self.subject
        msg["From"] = self.sender
        if type(self.recipient) == list:
            msg["To"] = ", ".join(self.recipient)
        else:
            msg["To"] = self.recipient
        msg["reply-to"] = self.reply_to

        if self.header:
            self.message = self.header + self.message

        if self.footer:
            self.message = self.message + self.footer

        self.message = f"<div style={self.body_style}>{self.message}</div>"

        message_text = MIMEText(self.message, 'html')
        msg.attach(message_text)

        for f in self.attachments:
            attachment = open(f.filename, 'rb')
            filename = f.filename.name
            part = f.mime_type(attachment.read(), _subtype=f.subtype)
            part.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(part)

        return msg

    def send_mail(self, alt_sender: str = None, alt_subject: str = None) -> None:
        if alt_sender is not None:
            self.sender = alt_sender
            logger.info(f"sender overwritten at send - {alt_sender}")

        if alt_subject is not None:
            self.subject = alt_subject
            logger.info(f"subject overwritten at send - {alt_subject}")

        msg = self.prepare()
        logger.debug(f'server:port = {self.server}:{self.port}')

        try:
            with smtplib.SMTP_SSL(self.server, int(self.port)) as smtp:
                smtp.ehlo()
                smtp.login(self.username, self.password)
                smtp.sendmail(self.sender, self.recipient, msg.as_string())
        except Exception as e:
            logger.exception(e)

    def validate(self) -> None:
        print('~~ Mail Settings ~~')
        print(f'server:port: {self.server}:{self.port}')
        print(f'username: {self.username}')
        print(f'password: {self.password}')
        print(f'reply-to: {self.reply_to}')
        print(f'recipient: {self.recipient}')
        self.message = "Test successful!"
        try:
            self.send_mail("Mailer Test", "Mailer Test Successful")
            print('~~ Email sent successfully ~~')
        except:
            print('~~ Email failed! ~~')

    def add_attachment(self, filename: pathlib.Path, subtype: str) -> None:
        self.attachments.append(Attachment(filename, subtype))

    def concat_message(self, tag: str, message: str) -> None:
        logger.info(message)
        self.message += f"<{tag}>{message}</{tag}>\n"

    h1 = partialmethod(concat_message, "h1")
    h2 = partialmethod(concat_message, "h2")
    h3 = partialmethod(concat_message, "h3")
    h4 = partialmethod(concat_message, "h4")
    h5 = partialmethod(concat_message, "h5")
    p = partialmethod(concat_message, "p")

