#!/bin/bash

if [ -z "$ZONE_ID" ] || [ -z "$TUNNEL_ID" ] || [ -z "$CLOUDFLARE_EMAIL" ] || [ -z "$CLOUDFLARE_API_KEY" ]; then
    echo "All environmental variables must be set: ZONE_ID, TUNNEL_ID, CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY"
    exit 1
fi

curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  --request POST \
  --header "X-Auth-Email: $CLOUDFLARE_EMAIL" \
  --header "X-Auth-Key: $CLOUDFLARE_API_KEY" \
  --json "{
    \"type\": \"CNAME\",
    \"proxied\": true,
    \"name\": \"lexApp.gbits.xyz\",
    \"content\": \"$TUNNEL_ID.cfargotunnel.com\"
  }"

