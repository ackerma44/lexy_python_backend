#!/bin/bash

echo "Physics I given for class"
curl -sS -G 'http://localhost:5005/api/slots' \
    --data-urlencode 'class=PHYSICS I' \
    --data-urlencode 'sessionDurationHours=1' | jq

