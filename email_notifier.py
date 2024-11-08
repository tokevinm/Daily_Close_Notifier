import aiosmtplib
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from validators import GoogleDriveData
from config import Settings
settings = Settings()


class EmailNotifier:
    """Handles API request to receive user data from Sheety API/Google Docs and
    sends requested data to users via email SMTP"""

    def __init__(self):
        self._smtp_username = settings.smtp_username
        self._smtp_password = settings.smtp_password
        self._sheety_endpoint = settings.sheety_users_endpoint
        self._sheety_header = {"Authorization": settings.sheety_bearer}
        self.users_data = GoogleDriveData()

    async def get_emails_data(self) -> None:
        """API request to get all stored user data"""

        try:
            print("Getting user data from Sheety API...")
            async with httpx.AsyncClient() as client:
                users_response = await client.get(
                    url=self._sheety_endpoint,
                    headers=self._sheety_header
                )
            users_response.raise_for_status()
            data = users_response.json()["users"]
        except Exception as e:
            print(f"Failed to retrieve user preferences from Sheety API", e)
        else:
            print("Storing user preferences")
            self.users_data = GoogleDriveData(data=data)

    async def send_emails(self, user_email: str, subject: str, html_text: str) -> None:
        """Emails requested data to users via MIME multipart and SMTP and checks for successful delivery"""

        print(f"Emailing {user_email}...")
        message = MIMEMultipart()
        message["From"] = self._smtp_username
        message["To"] = user_email
        message["Subject"] = subject
        message.attach(MIMEText(html_text, "html"))

        try:
            async with aiosmtplib.SMTP(
                    hostname=settings.smtp_hostname,
                    port=settings.smtp_port,
                    start_tls=True
            ) as connection:
                await connection.login(self._smtp_username, self._smtp_password)
                result = await connection.send_message(message)
                print(f"Emailed {user_email} successfully!", result)
        except aiosmtplib.SMTPException as e:
            print(f"Failed to send email to {user_email}:", e)
