import os
import aiosmtplib
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


class EmailNotifier:
    """Handles API request to receive user data from Sheety API/Google Docs and
    sends requested data to users via email SMTP"""

    def __init__(self):
        self._smtp_username = os.environ["SMTP_USERNAME"]
        self._smtp_password = os.environ["SMTP_PASSWORD"]
        self._sheety_endpoint = os.environ["SHEETY_USERS_ENDPOINT"]
        self._sheety_header = {"Authorization": os.environ["SHEETY_BEARER"]}
        self.users_data = []

    async def get_emails_data(self):
        """API request to get all stored user data"""
        print("Getting user data from Sheety API...")
        async with httpx.AsyncClient() as client:
            users_response = await client.get(
                url=self._sheety_endpoint,
                headers=self._sheety_header
            )
        users_response.raise_for_status()
        print("Storing user preferences")
        self.users_data = users_response.json()["users"]
        return self.users_data

    async def send_emails(self, user_email, subject, html_text):
        """Emails requested data to users via MIME multipart and SMTP and checks for successful delivery"""

        print(f"Emailing {user_email}...")
        message = MIMEMultipart()
        message["From"] = self._smtp_username
        message["To"] = user_email
        message["Subject"] = subject
        message.attach(MIMEText(html_text, "html"))

        try:
            async with aiosmtplib.SMTP(
                    hostname="smtp.gmail.com",
                    port=587,
                    start_tls=True
            ) as connection:
                await connection.login(self._smtp_username, self._smtp_password)
                result = await connection.send_message(message)
                print(f"Emailed {user_email} successfully!", result)
        except aiosmtplib.SMTPException as e:
            print(f"Failed to send email to {user_email}:", e)
