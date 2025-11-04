# email_sender.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from icecream import ic

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

gmail_user = os.getenv("GMAIL_USER")
gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
notify_email = os.getenv("NOTIFY_EMAIL")

ic(gmail_user, gmail_app_password, notify_email)

if gmail_user is None or gmail_app_password is None or notify_email is None:
    raise RuntimeError(
        f"Missing env var GMAIL_USER ({gmail_user}) or GMAIL_APP_PASSWORD ({gmail_app_password}) or NOTIFY_EMAIL ({notify_email})"
    )


def send_email(
    *, name: str, email: str, datetime: str, meeting_link: str, notes: str = ""
) -> None:
    """
    Sends a simple HTML email to NOTIFY_EMAIL using your Gmail App Password.
    """
    global gmail_user, gmail_app_password, notify_email

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "BOOKING REQUEST"
    msg["From"] = gmail_user
    msg["To"] = notify_email

    html = f"""
        <h2>New Booking Request</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Date &amp; Time:</strong> {datetime}</p>
        <p><strong>Meeting link:</strong> {meeting_link}</p>
        <p><strong>Notes:</strong> {notes}</p>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, [notify_email], msg.as_string())
