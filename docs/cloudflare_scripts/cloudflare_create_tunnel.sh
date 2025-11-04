#!/bin/bash

if [ -z "$ACCOUNT_ID" ] || [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "All environmental variables must be set: ACCOUNT_ID and CLOUDFLARE_API_TOKEN"
    exit 1
fi

curl "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" \
  --request POST \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{
    "name": "api-tunnel",
    "config_src": "cloudflare"
  }'

