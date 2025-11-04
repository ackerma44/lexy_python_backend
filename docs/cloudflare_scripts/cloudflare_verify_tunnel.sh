#!/bin/bash

if [ -z "$ACCOUNT_ID" ] || [ -z "$TUNNEL_ID" ] || [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "All environmental variables must be set: ACCOUNT_ID, TUNNEL_ID and CLOUDFLARE_API_TOKEN"
    exit 1
fi

curl "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID" \
  --request GET \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

