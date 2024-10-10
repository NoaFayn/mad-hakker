"""
Module to simplify the process of sending emails.

It handles the template and the contacts files.
"""

import madhac.app as mapp

import smtplib
import jinja2 as ji

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from madhac.text import pluralise


# Host of the SMTP server to connect to
PROP_MAILER_HOST = 'mailer.host'
DEFAULT_MAILER_HOST = 'localhost'
# Port of the SMTP server to connect to
PROP_MAILER_PORT = 'mailer.port'
DEFAULT_MAILER_PORT = 25
# Email address used to send mails
PROP_MAILER_EMAIL = 'mailer.email'
DEFAULT_MAILER_EMAIL = 'madhac@localhost'
# Name used to send mails
PROP_MAILER_NAME = 'mailer.name'
DEFAULT_MAILER_NAME = 'Madhac'
# Type of the mail content body (plain or html)
PROP_MAILER_CONTENT_TYPE = 'mailer.content.type'
DEFAULT_MAILER_CONTENT_TYPE = 'html'


def create_attachment(filepath: str, attachmentName='') -> MIMEBase:
    """Create an attachment for an email.

    The file to attach must exist!

    Args:
        filepath (string): Path of the file to attach
        attachmentName (string): Name to display for the attachment
    """
    if not attachmentName:
        attachmentName = filepath
    attachment = open(filepath, 'rb')
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', 'attachment; filename= {}'.format(attachmentName))
    return p


class NullUndefined(ji.Undefined):
    """Silentily handles undefined attributes when generating HTML report from jinja
    """
    undefinedVariables = {}

    def log(self):
        """Increments the number of undefined variables.
        """
        if self._undefined_name in NullUndefined.undefinedVariables:
            NullUndefined.undefinedVariables[self._undefined_name] += 1
        else:
            NullUndefined.undefinedVariables[self._undefined_name] = 1

    def __int__(self):
        self.log()
        return 0

    def __fload__(self):
        self.log()
        return 0

    def __nonzero__(self):
        self.log()
        return False

    def __bool__(self):
        self.log()
        return False

    def __getattr__(self, name):
        self.log()
        return 'N/A'

    def __str__(self):
        self.log()
        return 'N/A'


class Contact:
    """Represents a contact which can be sent an email.

    This class can be improved and extended, as long as the base for the name and the email still
    remain.
    """
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email


class Mailer:
    """Class in charge of handling the mailing process.
    """
    def __init__(self):
        self.template = None
        self.server = None
        self.env = None

    def __create_env(self):
        """Creates the template environment.
        """
        self.env = ji.Environment(loader=ji.FileSystemLoader('./'), undefined=NullUndefined)
        # Add custom filters
        self.env.filters['pluralise'] = pluralise
        # Reduce spaces
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True

    def connect(self, with_tls=True):
        """Connect to the SMTP server.

        Args:
            with_tls {bool} -- TRUE if the connection with the server should be encrypted
        """
        self.server = smtplib.SMTP(
            host=mapp.properties.get(PROP_MAILER_HOST, DEFAULT_MAILER_HOST),
            port=mapp.properties.get(PROP_MAILER_PORT, DEFAULT_MAILER_PORT)
        )
        if with_tls:
            self.server.starttls()

    def close(self):
        """Closes the connexion to the SMTP server.
        """
        if self.server:
            self.server.quit()

    def load_template(self, path_template: str):
        """Loads the mail template.
        """
        if self.env is None:
            self.__create_env()
        self.template = self.env.get_template(path_template)

    def send(self, contact: Contact, attachments=None, dry_run=False, mail_subject='mail', substitutes=dict()):
        """Sends the mail through the server.

        If the dry-run option is enabled, then this function doesn't actually send the mail.

        Args:
            contact (Contact): Contact to send the mail to
            attachments (list): Attachments to send with the email
            dry_run (bool): TRUE will not actually send the mails
            mail_subject (string): Subject of the mail
            substitutes (dict): Substitutes to provide to the template
        """
        assert self.template is not None

        substitutes['USER_NAME'] = contact.name

        # Create mail
        mail = MIMEMultipart()
        mail['To'] = contact.email
        mail['From'] = (
            mapp.properties.get(PROP_MAILER_NAME, DEFAULT_MAILER_NAME) +
            ' <' + mapp.properties.get(PROP_MAILER_EMAIL, DEFAULT_MAILER_EMAIL) + '>'
        )
        mail['Subject'] = mail_subject

        # Include each data of every config subscribed to
        if attachments:
            for attach in attachments:
                mail.attach(attach)

        # Mail content
        message = self.template.render(substitutes)
        mail.attach(MIMEText(
            message,
            mapp.properties.get(PROP_MAILER_CONTENT_TYPE, DEFAULT_MAILER_CONTENT_TYPE))
        )

        # Send mail
        if not dry_run and self.server is not None:
            self.server.send_message(mail)
