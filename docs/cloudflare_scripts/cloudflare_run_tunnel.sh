#!/bin/bash

if [ -z "$TUNNEL_TOKEN" ]; then
  echo "Env var TUNNEL_TOKEN must be set!"
  exit 1
fi

sudo cloudflared service install $TUNNEL_TOKEN

