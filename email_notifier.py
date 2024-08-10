import os
import smtplib
import requests
from dotenv import load_dotenv
load_dotenv()


class EmailNotifier:
    """Handles API request to receive user data from Google Docs and sends requested data to users via email SMTP"""
    def __init__(self):
        self._smtp_username = os.environ["SMTP_USERNAME"]
        self._smtp_password = os.environ["SMTP_PASSWORD"]
        self._sheety_endpoint = os.environ["SHEETY_USERS_ENDPOINT"]
        self.sheety_header = {"Authorization": os.environ["SHEETY_BEARER"]}
        self.users_data = []

    def get_emails_data(self):
        """API request to get stored user data"""
        users_response = requests.get(
            self._sheety_endpoint,
            headers=self.sheety_header
        )
        users_response.raise_for_status()
        self.users_data = users_response.json()["users"]
        return self.users_data

    def send_emails(self, user_email, message):
        """Sends requested data to user emails via SMTP and checks for successful delivery"""
        try:
            with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
                connection.starttls()
                connection.login(user=self._smtp_username, password=self._smtp_password)
                result = connection.sendmail(
                    from_addr=self._smtp_username,
                    to_addrs=user_email,
                    msg=message
                )
            if not result:
                print(f"Emailed {user_email} successfully!")
            else:
                print(f"Failed to send email to {user_email}")
        except smtplib.SMTPException as e:
            print("Failed to send email:", e)
