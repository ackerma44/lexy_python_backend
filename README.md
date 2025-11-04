# Collegiate Frontend
## Setup
### Files go here
`/var/www/collegiate/index.html`
`/etc/nginx/sites-available/collegiate_booking_nginx.conf`

### Enable site
```
ln -s /etc/nginx/sites-available/collegiate_booking_nginx.conf /etc/nginx/sites-enabled
```

### Reload Nginx
```
nginx -t
systemctl reload nginx
```

### Add HTTPS with Certbot
```
sudo certbot --nginx d example.com
```

## Local Testing
### Create tunnel
```
ssh -L 9999:192.168.10.20:80 192.168.10.20
```

## GCP
go to gcp console:
Api & services > Oauth consent screen
- under "Data Access"
- click "Add or remove scopes" 
- then select/enable the calendar apis 

For the credentials you must add a redirect_uri:
- got to: 'Api & Services > Credentials'
- select the credential you want to update
- under "Authorized redirect uris" add `http://localhost:8888/` and `http://127.0.0.1:8888/`

## certs with cloudflare tunnel
1. Install the Cloudflare DNS plugin:
```
sudo apt update
sudo apt install -y python3-certbot-dns-cloudflare
```

2. In Cloudflare, create an API Token with Zone → DNS:Edit for gbits.xyz.
3. Save the token on the server (permissions matter):
```
sudo mkdir -p /root/.secrets
sudo sh -c 'printf "dns_cloudflare_api_token = %s\n" "<YOUR_TOKEN>" > /root/.secrets/cf.ini'
sudo chmod 600 /root/.secrets/cf.ini
```

4. Issue the cert via DNS-01:
```
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cf.ini \
  --dns-cloudflare-propagation-seconds 60 \
  -d gbits.xyz -d lexapp.gbits.xyz
```

5. Point Nginx (/etc/nginx/sites-available/collegiate_booking_nginx.conf) at the new certs (/etc/letsencrypt/live/gbits.xyz/fullchain.pem and privkey.pem) and reload:
```
sudo nginx -t && sudo systemctl reload nginx
```

## Server
put all python files here
```
/srv/lexy_backend/
```

put client_secret AND runtime_token.json (run locally to get token first then copy it to the server)
```
/etc/lexy/secrets
```

add service file
```
/etc/systemd/system/lexy_backend.service
sudo chown root:root /etc/systemd/system/lexy_backend.service
sudo chmod 600 /etc/systemd/system/lexy_backend.service
```

create new group `lexapp`
```
sudo groupadd lexapp
```

change perms of everything
```
sudo -R chown root:lexapp /etc/lexy/secrets
sudo chmod 750 /etc/lexy/secrets
sudo chmod 640 /etc/lexy/secrets/*
sudo chmod 660 /etc/lexy/secrets/runtime_token.json

sudo -R chown root:lexapp /srv/lexy_backend
sudo chmod 770 /srv/lexy_backend
sudo chmod 640 /srv/lexy_backend/*
```

