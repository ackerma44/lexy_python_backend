import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]


def list_viewable_calendars(service):
    """Return [(id, summary, accessRole)] for calendars on the user's calendar list."""
    items, page_token = [], None
    while True:
        resp = (
            service.calendarList()
            .list(
                minAccessRole="freeBusyReader",  # freeBusyReader / reader / writer / owner
                showHidden=True,
                pageToken=page_token,
                maxResults=250,
            )
            .execute()
        )
        for it in resp.get("items", []):
            items.append((it["id"], it.get("summary", it["id"]), it["accessRole"]))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def print_all_cals(service):
    cal_list = service.calendarList().list({}).execute()


def _client_from_refresh_token() -> any:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError(
            "Missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN"
        )
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=CALENDAR_SCOPE,
    )
    return build("calendar", "v3", credentials=creds)
