#!/bin/bash

echo "unavailable time"
curl -sS -X POST 'http://localhost:5005/api/booking-request' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Ada Lovelace",
    "email": "gbyts3+client@gmail.com",
    "startDateTimes": ["2025-10-03T15:00:00-07:00"],
    "durationHours": "1.5",
    "notes": "Algebra focus",
    "tutor": "apptest",
    "class": "physics i",
    "untilDate": "2025-12-03T15:00:00-07:00"
  }' | jq

echo ""
echo "available time"
curl -sS -X POST 'http://localhost:5005/api/booking-request' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Ada Lovelace",
    "email": "gbyts3+client@gmail.com",
    "startDateTimes": ["2025-10-05T21:30:00+00:00"],
    "durationHours": "1.5",
    "notes": "Algebra focus",
    "tutor": "gbits",
    "class": "physics i",
    "untilDate": "2025-12-03T15:00:00-07:00"
  }' | jq

