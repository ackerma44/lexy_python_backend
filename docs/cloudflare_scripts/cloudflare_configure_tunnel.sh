#!/bin/bash

if [ -z "$ACCOUNT_ID" ] || [ -z "$TUNNEL_ID" ] || [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "All environmental variables must be set: ACCOUNT_ID, TUNNEL_ID and CLOUDFLARE_API_TOKEN"
    exit 1
fi

curl "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" \
  --request PUT \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{
    "config": {
        "ingress": [
            {
                "hostname": "lexApp.gbits.xyz",
                "service": "http://localhost:3000",
                "originRequest": {}
            },
            {
                "service": "http_status:404"
            }
        ]
    }
  }'
