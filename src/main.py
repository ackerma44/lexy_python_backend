# main.py

from __future__ import annotations
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------------------
# Force load .env before anything else (fixes uvicorn reload)
# --------------------------------------------------------
import os
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
os.chdir(project_root)
load_dotenv(dotenv_path=project_root / ".env")

print("✅ Preloaded .env for Uvicorn reload:", os.getenv("GMAIL_USER"))
# Force override TUTOR_EXCEL_PATH to your Windows path
import os
os.environ["TUTOR_EXCEL_PATH"] = "C:\\Users\\lexyg\\OneDrive\\Documents\\COLLEGIATE TUTORS\\Software Stuff\\lexy_python_backend\\tutor_course_list_bk.xlsx"
print("🔧 Overridden TUTOR_EXCEL_PATH ->", os.environ["TUTOR_EXCEL_PATH"])


# --------------------------------------------------------




"""
FastAPI backend for recurring tutoring bookings.
See README_FASTAPI.md for details.
"""
import os
import platform
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Tuple
from warnings import warn
from zoneinfo import ZoneInfo

from dateutil.parser import isoparse
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from googleapiclient.errors import HttpError
from icecream import ic
from pydantic import BaseModel, EmailStr, Field, field_validator

from src.data_loading import get_available_classes, get_tutor_emails, get_tutors_for_class
from src.email_sender import send_email
from src.google_calendar import gCalendar


SYSTEM_MACHINE = platform.system()
IS_LINUX_MACHINE = SYSTEM_MACHINE == "Linux"


from pathlib import Path
from dotenv import load_dotenv

from pathlib import Path
from dotenv import load_dotenv
import os

# Force working directory to project root (so Uvicorn always finds .env)
os.chdir(Path(__file__).resolve().parent.parent)
print(f"💡 Current working dir: {os.getcwd()}")

# Load .env file from project root
load_dotenv()
print("✅ ENV TEST ->", os.getenv("GMAIL_USER"))
print("✅ ENV PATH TEST ->", os.getenv("TUTOR_EXCEL_PATH"))


SYSTEM_MACHINE = platform.system()
IS_LINUX_MACHINE = SYSTEM_MACHINE == "Linux"
ic(SYSTEM_MACHINE, IS_LINUX_MACHINE)

TIMEZONE = os.getenv("TIMEZONE", "America/New_York")
ALLOWED_BOOK_TIME_INCREMENT = 5
SESSION_BUFFER_MIN = 5
LEXY_EMAIL = "lexy@thecollegiatetutors.com"

# calendar setup
g_calendar = gCalendar()


AllowedDurations = Literal["1", "1.0", "1.5", "2.0", "2"]

app = FastAPI(title="Tutoring Booking API", version="1.0.0")
@app.get("/")
def root():
    return {"message": "Backend is running!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.thecollegiatetutors.com",  # your live Wix domain
        "https://editor.wix.com",               # for preview testing
        "https://*.wixsite.com"                 # sometimes Wix uses this subdomain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORS
origins_env = os.getenv("FRONTEND_ORIGINS", "*")
allow_origins = [o.strip() for o in origins_env.split(",")] if origins_env else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    class_: str = Field(alias="class")
    tutor: str
    startDateTimes: List[datetime]
    durationHours: AllowedDurations = "1"
    notes: Optional[str] = ""
    untilDate: Optional[datetime] = None

    @field_validator("untilDate", mode="before")
    @classmethod
    def normalize_untilDate_datetime_string(cls, v):
        if isinstance(v, str):
            v = v.strip().replace(" ", "T")
        return v

    @field_validator("untilDate", mode="after")
    @classmethod
    def untilDate_must_be_timezone_aware(
        cls, v: Optional[datetime]
    ) -> Optional[datetime]:
        if v is None:
            return v

        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError(
                "All untilDate must include a timezone offset (e.g., 2025-10-01T15:00:00-07:00)."
            )

        return v

    @field_validator("startDateTimes", mode="before")
    @classmethod
    def normalize_datetime_string(cls, v):
        ret = []
        for vv in v:
            if isinstance(vv, str):
                vv = vv.strip().replace(" ", "T")
            ret.append(vv)
        return ret

    @field_validator("startDateTimes", mode="after")
    @classmethod
    def must_be_timezone_aware_and_24hrs_in_advance(
        cls, v: List[datetime]
    ) -> List[datetime]:
        if len(v) == 0:
            raise ValueError("At least one startDateTime must be given.")
        now_plus_24hrs = datetime.now(timezone.utc) + timedelta(days=1)
        days_of_week_booked = set()
        for vv in v:
            if vv.tzinfo is None or vv.utcoffset() is None:
                raise ValueError(
                    "All startDateTime(s) must include a timezone offset (e.g., 2025-10-01T15:00:00-07:00)."
                )

            if vv.astimezone(timezone.utc) <= now_plus_24hrs:
                raise ValueError(
                    "All startDateTime(s) must be more than 24hrs in advance."
                )
            if vv.astimezone(ZoneInfo(TIMEZONE)).weekday in days_of_week_booked:
                raise ValueError("Cannot book two sessions in the same day.")
        return v


def _parse_iso(dt_like) -> datetime:
    if isinstance(dt_like, datetime):
        dt = dt_like
    else:
        s = str(dt_like)
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _nearest_start(t: datetime):
    t = t.replace(second=0, microsecond=0)
    if t.minute % ALLOWED_BOOK_TIME_INCREMENT == 0:
        return t
    inc = (t.minute // ALLOWED_BOOK_TIME_INCREMENT) + 1
    inc *= ALLOWED_BOOK_TIME_INCREMENT
    if inc >= 60:
        t += timedelta(hours=1)
        inc = 0
    return t.replace(minute=inc)


def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def freebusy(
    service,
    calendar_ids: Iterable,
    start_dt: datetime,
    end_dt: datetime,
    tz="UTC",
):
    """
    Query FreeBusy for one or more calendars between start_dt and end_dt (tz-aware datetimes).
    Returns {calendar_id: [(start_datetime, end_datetime), ...]} in the requested timezone.
    """
    if start_dt.tzinfo is None or end_dt.tzinfo is None:
        raise ValueError("start_dt and end_dt must be timezone-aware datetimes")
    ic(start_dt, end_dt)
    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "timeZone": tz,
        "items": [{"id": cid} for cid in calendar_ids],
    }
    fb = service.freebusy()
    resp = fb.query(body=body).execute()

    # params = { "singleEvents": True, "orderBy": "startTime", "timeMin": start_dt.isoformat(), "timeMax": end_dt.isoformat(), "timeZone": tz, "maxResults": 10000, "fields": "items(summary),nextPageToken", }

    out = {}
    for cid, payload in resp.get("calendars", {}).items():
        if "errors" in payload:
            warn(
                f"freebusy: Error occurred getting tutor calendar '{cid}', skipping... payload: '{payload}'"
            )
            continue
        intervals = []
        for b in payload.get("busy", []):
            s = isoparse(b["start"])
            e = isoparse(b["end"])
            # Normalize to requested tz for convenience
            s = s.astimezone(ZoneInfo(tz))
            e = e.astimezone(ZoneInfo(tz))
            intervals.append((s, e))
        out[cid] = merge_intervals(intervals)
        # params["calendarId"] = cid
        # events = service.event.list(**params).execute()
        # ic(events)
    return out


def merge_intervals(intervals):
    """Merge overlapping/adjacent intervals: [(s1,e1), (s2,e2), ...] → merged list."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]
    for cur_s, cur_e in intervals[1:]:
        last_s, last_e = merged[-1]
        if cur_s <= last_e:  # overlap or touch
            merged[-1] = (last_s, max(last_e, cur_e))
        else:
            merged.append((cur_s, cur_e))
    return merged


def _get_availablility(
    busy_schedule: List[Tuple[datetime, datetime]],
    start: datetime,
    end: datetime,
) -> deque:
    availability = deque()
    if len(busy_schedule) == 0:
        availability.append([start, end])
        return availability

    if start < busy_schedule[0][0]:
        availability.append([start, busy_schedule[0][0]])

    last_end = busy_schedule[0][1]
    for bs, be in busy_schedule[1:]:
        availability.append([last_end, bs])
        last_end = be

    if last_end < end:
        availability.append([last_end, end])
    return availability


def get_session_slots(
    busy_schedule: List[Tuple[datetime, datetime]],
    start: datetime,
    end: datetime,
    session_duration: str,
) -> List[Tuple[str, str]]:
    slot_step_duration = 1.0  # always do 1 hour time steps for slots - regardless of 1, 1.5, 2 hour sessions
    td_step = timedelta(hours=float(slot_step_duration), minutes=SESSION_BUFFER_MIN)
    td_session = timedelta(hours=float(session_duration))

    # should already be merged from freebusy() but just in case something changes
    busy_schedule = merge_intervals(busy_schedule)
    availability = _get_availablility(busy_schedule, start, end)
    ic(availability)

    if len(availability) == 0:
        return []

    # add 1 day to give tutor buffer so they see the new event
    # add 1 hour so that the client has 1 hour to book the session (book session api will fail if its w/in 24 hours)
    start += timedelta(days=1, hours=1)

    sessions = []
    while availability:
        next_avail = availability.popleft()
        s = next_avail[0]
        while s < next_avail[1]:
            if s < start:
                # within 24 hour window
                s += td_step
                continue
            e = s + td_session
            if e > next_avail[1]:
                # session would run over
                break
            sessions.append((s.isoformat(), e.isoformat()))
            s += td_step
    return sessions


@app.get("/api/slots", response_model=Dict[str, List[Tuple[str, str]]])
def get_slots(
    class_: str = Query(
        ..., description="Class the client is inquiring about", alias="class"
    ),
    sessionDurationHours: AllowedDurations = Query(
        1.0, description="Allowed values: 1, 1.5, or 2 hours"
    ),
):
    global g_calendar
    class_ = class_.strip().lower()
    if class_ not in get_available_classes():
        raise HTTPException(400, f"Invalid class given: '{class_}'")

    try:
        if g_calendar is None:
            raise HTTPException(504, f"Server error: 'calendar not initialized'")

        # dont add 24 hours to start here - we will look for the last busy slot later on to correctly calculate the first opening available
        start = datetime.now(timezone.utc)
        start = _nearest_start(start)
        # 3 hours bc 2 hour time slots plus 1 hour for client to book time
        end = start + timedelta(weeks=1, days=1, hours=3)
        tutors = get_tutors_for_class(class_)
        tutor_emails = get_tutor_emails(tutors)
        tutor_email_rev_map = {v: k for k, v in tutor_emails.items()}
        # ic(tutors, tutor_emails, tutor_email_rev_map)
        tutor_email_list = tutor_emails.values()
        fb = freebusy(
            g_calendar.get(),
            tutor_email_list,
            start,
            end,
        )

        if len(fb) == 0:
            return {}

        ic(fb)
        slots = {k: [] for k in tutor_emails.keys()}
        for tutor_email, schedule in fb.items():
            session_slots = get_session_slots(
                schedule, start, end, sessionDurationHours
            )
            slots[tutor_email_rev_map[tutor_email]] = session_slots
        ic(slots)
        return slots

    except HttpError as e:
        raise HTTPException(500, {"error": "Error fetching slots", "details": e.reason})
    except FileNotFoundError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, {"error": "Unexpected error", "details": str(e)})


@app.post("/api/booking-request")
def booking_request(req: BookingRequest):
    # start=2025-09-28T00:50:00-07:00
    tutor = get_tutor_emails([req.tutor])
    if len(tutor) == 0:
        # TODO should report this because requester is prob not using front end (programmatic access)
        warn(f"Potential bot use! invalid tutor given: '{req.tutor}'")
        time.sleep(1)
        raise HTTPException(400, f"Unkown tutor given: '{tutor}'")
    tutor_email = tutor[req.tutor]

    valid_slots = get_slots(req.class_, req.durationHours)
    if req.tutor not in valid_slots:
        # TODO should report this because requester is prob not using front end (programmatic access)
        warn(
            f"Potential bot use! invalid tutor/class combo given: '{req.tutor}:{req.class_}'"
        )
        time.sleep(1)
        raise HTTPException(
            400, f"Invalid tutor/class combo: '{req.tutor}:{req.class_}'"
        )

    set_valid_slots = set()
    for s, e in valid_slots[req.tutor]:
        set_valid_slots.add(s)

    # clean startDateTimes (UTC + no seconds/microseconds)
    start_times = set()
    if req.untilDate is not None:
        req.untilDate = req.untilDate.astimezone(ZoneInfo(TIMEZONE))
        req.untilDate = req.untilDate.replace(hour=23, minute=59)  # midnight
        req.untilDate = req.untilDate.astimezone(timezone.utc)

    for start in req.startDateTimes:
        start = start.replace(second=0, microsecond=0)
        start = start.astimezone(timezone.utc)
        start_times.add(start)

        start_iso = start.isoformat()
        if start_iso not in set_valid_slots:
            ic(start_iso, set_valid_slots)
            raise HTTPException(
                400,
                "One or more of the times requested is no longer available. Please make a new request.",
            )
        if req.untilDate is not None and req.untilDate < start:
            # todo test that if the end date is on the same day that a session is booked, the booking will still schedule that days session
            raise HTTPException(
                400,
                "Recurring session end date must be after all booked sessions. Please make a new request.",
            )

    start_times = list(start_times)
    start_times.sort()
    ic(start_times)

    links = {}
    # may need to rethink this approach
    for start in start_times:
        links[start] = {"errors_booking": [], "errors_email": []}
        ic(start)
        try:
            html_link = g_calendar.add_recurring_to_google_calendar(
                name=req.name,
                email=str(req.email),
                notes=req.notes or "",
                startDateTime=start,
                durationHours=float(req.durationHours),
                untilDate=req.untilDate,
                attendees_extra=[tutor_email, LEXY_EMAIL],
            )
            links[start]["meeting_link"] = html_link
            try:
                send_email(
                    name=req.name,
                    email=str(req.email),
                    datetime=start.isoformat(),
                    meeting_link=html_link,
                    notes=req.notes or "",
                )
            except Exception as mail_err:
                print(f"send_email failed: '{mail_err}'")
                links[start]["errors_email"].append(str(mail_err))

        except Exception as e:
            print(f"add_recurring_to_google_calendar failed: '{e}'")
            links[start]["errors_booking"].append(str(e))

    ic(req.startDateTimes, start_times, links)
    errors_booking = 0
    errors_email = 0
    for start in start_times:
        if len(links[start]["errors_booking"]) != 0:
            errors_booking += 1
        if len(links[start]["errors_email"]) != 0:
            errors_email += 1

    if errors_booking == len(links):
        print(f"Failed to create ALL bookings: ({links})")
        raise HTTPException(
            500,
            {
                "error": "Failed to create bookings.",
                "details": "Please try again. If this happens again please contact us via email.",
            },
        )
    if errors_booking > 0 and errors_email == 0:
        print(f"Failed to create some bookings: ({links})")
        return {
            "message": "Failed to book some sessions",
            "details": str(
                {k: v["meeting_link"] for k, v in links.items() if "meeting_link" in v}
            ),
            "failed": str([k for k, v in links.items() if "meeting_link" not in v]),
        }

    if errors_booking > 0:
        print(f"Failed to create some bookings and send some emails: ({links})")
        return {
            "message": "Failed to book some sessions. Some emails failed to send. Please notify us via email with this error.",
            "details": str(
                {k: v["meeting_link"] for k, v in links.items() if "meeting_link" in v}
            ),
            "failed": str([k for k, v in links.items() if "meeting_link" not in v]),
        }
    if errors_email > 0:
        print(f"Failed to EMAIL some bookings: ({links})")
        return {
            "message": "Successfully booked all sessions. However, some emails did not get sent properly. Please send us an email notifying us of this error. Your meeting links are given below!",
            "details": str({k: v["meeting_link"] for k, v in links.items()}),
        }
    return {
        "message": "Successfully booked all sessions. Your meeting links are given below and have been emailed to you for your convenience.",
        "details": str({k: v["meeting_link"] for k, v in links.items()}),
    }


@app.get("/")
def health():
    return "Server is up and running!"


@app.get("/api/classes", response_model=List[str])
def get_classes():
    return get_available_classes()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "5005"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
