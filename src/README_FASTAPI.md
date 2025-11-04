# FastAPI Migration for Tutoring Booking Backend

This is the **FastAPI + Uvicorn** version of your service. It keeps the same routes and behavior:
- **GET `/api/slots`** — checks Google Calendar availability via **Service Account** and returns hourly slots with a 5‑minute buffer
- **POST `/api/booking-request`** — creates a **recurring** event on a real user's calendar (OAuth **refresh token**) and sends a notification email

## Files
- `main.py` — FastAPI app with CORS and Pydantic models
- `google_calendar.py` — Recurring event creation using OAuth refresh token
- `email_sender.py` — Notification email via Gmail App Password
- `requirements.txt` — Python dependencies
- `.env.example` — Environment variables template (same as before)

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```
Docs:
- Swagger UI → `http://localhost:3000/docs`
- ReDoc → `http://localhost:3000/redoc`

## Environment variables
Same as before plus optional CORS origins:
```
# CORS (comma-separated origins; default '*')
FRONTEND_ORIGINS=https://your-frontend.example.com,https://other.app
```
