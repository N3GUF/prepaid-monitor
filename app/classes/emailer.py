from abc import ABC
from email.message import EmailMessage
import smtplib
from typing import Union


class IEmailer(ABC):
    """Provide basic email functionality"""

    def SendEmail(
        self,
        subject: str,
        message: str,
        attachments: list = [],
        emailFrom: str = "",
        emailTo: Union[str, list] = "",
        emailCc: list = [],
        emailBcc: list = [],
    ):
        pass


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
        attachments: list = [],
        emailFrom: str = "",
        emailTo: Union[str, list] = "",
        emailCc: list = [],
        emailBcc: list = [],
    ) -> None:
        """Create an email from the given data.

        Arguments:
            subject:    Subject
            message:    Message
            attachments: List of attachments
            emailFrom:  Email from address
            emailTo:    Email to address List
            emailCc:    Email cc address List
            emailBcc    Email bcc address List

        """

        if emailFrom == "":
            emailFrom = self.__emailFrom

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = emailFrom
            msg["To"] = emailTo
            msg["Cc"] = ",".join(emailCc)
            msg["Bcc"] = ",".join(emailBcc)
            msg.set_content(message)

            if attachments:
                for file in attachments:
                    with open(file, "rb") as f:
                        msg.add_attachment(
                            f.read(),
                            maintype="application",
                            subtype="octet-stream",
                            filename=f.name,
                        )

            if self.__logger is not None:
                self.__logger.debug("Email from: \t{}".format(msg["From"]))
                self.__logger.debug("Email to: \t{}".format(msg["To"]))
                self.__logger.debug("Email cc: \t{}".format(msg["Cc"]))
                self.__logger.debug("Email subject: \t{}".format(msg["Subject"]))
                self.__logger.debug("Email message: \t{}".format(message))

            with smtplib.SMTP(self.__mailhost, self.__mailport) as smtp:
                smtp.send_message(msg)

        except Exception as ex:
            self.__logger.error("Unable to send email.")

            for arg in ex.args:
                self.__logger.error(arg)
