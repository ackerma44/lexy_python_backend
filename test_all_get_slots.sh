#!/bin/bash

echo "Physics I given for class"
curl -sS -G 'http://localhost:5005/api/slots' \
    --data-urlencode 'class=physics i' \
    --data-urlencode 'sessionDurationHours=1.0' | jq

echo "Chem 1 given for class"
curl -sS -G 'http://localhost:5005/api/slots' \
    --data-urlencode 'class=chemistry i' \
    --data-urlencode 'sessionDurationHours=1.0' | jq

echo "No class given"
curl -sS -G 'http://localhost:5005/api/slots' \
    --data-urlencode 'class=' \
    --data-urlencode 'sessionDurationHours=1.0' | jq

