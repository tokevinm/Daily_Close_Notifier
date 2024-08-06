import os
import smtplib
import requests
from dotenv import load_dotenv


class EmailNotifier:

    def __init__(self):
        self._smtp_username = os.environ["SMTP_USERNAME"]
        self._smtp_password = os.environ["SMTP_PASSWORD"]
        self._sheety_users_endpoint = os.environ["SHEETY_USERS_EP"]
        self.sheety_header = {"Authorization": os.environ["SHEETY_BEARER"]}
        self.users_data = []

    def get_emails_data(self):

        users_response = requests.get(self._sheety_users_endpoint, headers=self.sheety_header)
        users_response.raise_for_status()
        self.users_data = users_response.json()["users"]
        return self.users_data

    def send_emails(self, user_email, message_body):

        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=self._smtp_username, password=self._smtp_password)
            connection.sendmail(
                from_addr=self._smtp_username,
                to_addrs=user_email,
                msg=message_body
            )
