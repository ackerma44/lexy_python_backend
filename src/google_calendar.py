# google_calendar.py
from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as SACredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from icecream import ic

load_dotenv()

CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

SYSTEM_MACHINE = platform.system()
IS_LINUX_MACHINE = SYSTEM_MACHINE == "Linux"
TOKEN_JSON_PATH = "." if not IS_LINUX_MACHINE else "/etc/lexy/secrets"


class gCalendar:
    def __init__(self, use_service_account: bool = False):
        if use_service_account:
            self._g_calendar = self._get_service_account_calendar()
        else:
            self._g_calendar = self._get_calendar_service()
    def _get_calendar_service(self):
        """Authenticate using environment variables (Render-safe)."""
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_info({
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
        })

        return build("calendar", "v3", credentials=creds)


# GREG'S OLD TOKEN LOGIC WHERE YOU HAVE TO LOG IN IN BROWSER THEN IT SAVES TOKEN. NA FOR DEPLOYED VERSION ON RENDER
    # def _get_calendar_service(self):
    #     """OAuth user auth with token caching to token.json."""
    #     TOKEN_JSON_FILE = "runtime_token.json"
    #     TOKEN_JSON = os.path.join(TOKEN_JSON_PATH, TOKEN_JSON_FILE)
    #     ic(TOKEN_JSON)
    #     keyfile = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    #     if keyfile == "":
    #         raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set")
    #     creds = None
    #     try:
    #         creds = Credentials.from_authorized_user_file(TOKEN_JSON, CALENDAR_SCOPE)
    #     except Exception:
    #         pass
    #     if not creds or not creds.valid:
    #         if creds and creds.expired and creds.refresh_token:
    #             creds.refresh(Request())
    #         else:
    #             # Must run this locally first to get runtime_token then use that token on the server
    #             flow = InstalledAppFlow.from_client_secrets_file(
    #                 keyfile, CALENDAR_SCOPE
    #             )

    #             creds = flow.run_local_server(port=8888)
    #         with open(TOKEN_JSON, "w+") as f:
    #             f.write(creds.to_json())
    #     return build("calendar", "v3", credentials=creds)

    def _get_service_account_calendar(self, user_email: str = "gbyts3@gmail.com"):
        keyfile = os.getenv("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS")
        if not keyfile:
            raise FileNotFoundError("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS is not set.")
        if not os.path.exists(keyfile):
            raise FileNotFoundError(
                "GOOGLE_SERVICE_ACCOUNT_CREDENTIALS file does not exist."
            )
        # creds = SACredentials.from_service_account_file( keyfile, scopes=CALENDAR_SCOPE).with_subject(user_email)
        creds = SACredentials.from_service_account_file(keyfile, scopes=CALENDAR_SCOPE)
        return build("calendar", "v3", credentials=creds)

    def get(self):
        return self._g_calendar

    def add_recurring_to_google_calendar(
        self,
        name: str,
        email: str,
        notes: str,
        startDateTime,
        durationHours: float,
        untilDate=None,
        attendees_extra: Optional[List[str]] = None,
    ) -> str:
        """
        Adds a recurring event to the authenticated user's primary calendar.
        Returns the event htmlLink.
        """
        start_dt = _ensure_dt(startDateTime)
        end_dt = start_dt + timedelta(hours=float(durationHours))

        until = _format_until(untilDate or (start_dt + timedelta(weeks=12)))

        recurrence_rule = f"RRULE:FREQ=WEEKLY;UNTIL={until}"

        attendees = [{"email": email}]
        if attendees_extra:
            for addr in attendees_extra:
                if addr:
                    attendees.append({"email": addr})
        # Optional: also invite NOTIFY_EMAIL if set
        notify_email = os.getenv("NOTIFY_EMAIL")
        if notify_email and notify_email not in [a["email"] for a in attendees]:
            attendees.append({"email": notify_email})

        event = {
            "summary": f"Booking with {name}",
            "description": f"Email: {email}\nNotes: {notes or ''}",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
            "attendees": attendees,
            "recurrence": [recurrence_rule],
        }

        try:
            created = (
                self._g_calendar.events()
                .insert(calendarId="primary", body=event, sendUpdates="all")
                .execute()
            )
            return created.get("htmlLink", "")
        except HttpError as e:
            raise RuntimeError(f"Error creating recurring event: {e}")


def _ensure_dt(value) -> datetime:
    """Accepts ISO string or datetime; returns timezone-aware datetime"""
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value)
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        # Assume provided time is in the configured TIMEZONE if naive
        import pytz  # type: ignore

        tz = pytz.timezone(TIMEZONE)
        dt = tz.localize(dt)
    return dt


def _format_until(date_like) -> str:
    """Format UNTIL for RRULE as YYYYMMDDT235959Z"""
    dt = _ensure_dt(date_like).astimezone(timezone.utc)
    # Use end-of-day in UTC
    dt = dt.replace(hour=23, minute=59, second=59, microsecond=0)
    return dt.strftime("%Y%m%dT%H%M%SZ")
