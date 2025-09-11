import os
import smtplib
from email.message import EmailMessage
from typing import Protocol, Union


class IEmailer(Protocol):
    """Provide basic email functionality"""

    def SendEmail(
        self,
        subject: str,
        message: str,
        attachments: list = None,
        emailFrom: str = "",
        emailTo: Union[str, list[str]] = "",
        emailCc: Union[str, list[str]] = "",
        emailBcc: Union[str, list[str]] = "",
    ) -> None: ...


class Emailer:
    """Provide basic email functionality"""

    def __init__(
        self,
        logger,
        emailFrom: str = "",
        mailHost: str = "mail.fleetcor.com",
        mailPort: int = 25,
    ):
        self.__logger = logger
        self.__mailhost = mailHost
        self.__mailport = mailPort
        self.__emailFrom = emailFrom

    def SendEmail(
        self,
        subject: str,
        message: str,
        attachments: list = None,
        emailFrom: str = "",
        emailTo: Union[str, list[str]] = "",
        emailCc: Union[str, list[str]] = "",
        emailBcc: Union[str, list[str]] = "",
    ) -> None:
        """Create and send an email with optional attachments and recipients"""

        if not emailFrom:
            emailFrom = self.__emailFrom

        if attachments is None:
            attachments = []

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = emailFrom

            # Helper to format recipient fields
            def format_recipients(field_name, value):
                if value:
                    if isinstance(value, str):
                        msg[field_name] = value
                    elif isinstance(value, list):
                        msg[field_name] = ",".join(value)
                    else:
                        raise TypeError(
                            f"{field_name} must be a string or a list of strings"
                        )

            format_recipients("To", emailTo)
            format_recipients("Cc", emailCc)
            format_recipients("Bcc", emailBcc)

            msg.set_content(message)

            # Attach files
            for file_path in attachments:
                with open(file_path, "rb") as f:
                    msg.add_attachment(
                        f.read(),
                        maintype="application",
                        subtype="octet-stream",
                        filename=os.path.basename(file_path),
                    )

            # Logging
            if self.__logger:
                self.__logger.debug(f"Email from: \t{msg['From']}")
                self.__logger.debug(f"Email to: \t{msg.get('To', '')}")
                self.__logger.debug(f"Email cc: \t{msg.get('Cc', '')}")
                self.__logger.debug(f"Email bcc: \t{msg.get('Bcc', '')}")
                self.__logger.debug(f"Email subject: \t{msg['Subject']}")
                self.__logger.debug(f"Email message: \t{message}")

            # Send email
            with smtplib.SMTP(self.__mailhost, self.__mailport) as smtp:
                smtp.send_message(msg)

        except Exception as e:
            if self.__logger:
                self.__logger.warning("Unable to send email.")
                self.__logger.warning(str(e))
        else:
            if self.__logger:
                self.__logger.info("Sent email")

