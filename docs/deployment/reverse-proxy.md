<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

# Real client IP behind a reverse proxy

If your app logs `172.18.0.1` (the Docker gateway) for every visitor, rate
limits go global, view/interaction dedup collapses, and event logs are useless.
Find your topology below and apply the few lines that matter.

> **TL;DR:** `npm run setup-host-proxy` does cases 1 and 3 for you (writes nginx,
> patches `.env`, validates, reloads).

## 1. Cloudflare → nginx → app

```mermaid
flowchart LR
  V[Visitor] --> CF[Cloudflare]
  CF -->|CF-Connecting-IP| N[nginx]
  N -->|X-Client-IP| T[Traefik]
  T -->|X-Client-IP| A[app]
```

```bash
# .env
PUBLIC_BIND_HOST=127.0.0.1     # Traefik unreachable except via nginx
TRUSTED_IP_HEADER=X-Client-IP
```

```nginx
# /etc/nginx/conf.d/cloudflare-realip.conf  — http context (global, no block)
set_real_ip_from 173.245.48.0/20;
[..] # one set_real_ip_from line per Cloudflare CIDR (see their /ips list)

real_ip_header CF-Connecting-IP;    # $remote_addr now becomes the visitor
```

```nginx
# /etc/nginx/sites-available/<domain>  — inside the server { } block
location / {
    proxy_pass http://127.0.0.1:${PUBLIC_PORT};
    proxy_set_header X-Client-IP $remote_addr;
}
```

→ `npm run setup-host-proxy`, answer **yes** to Cloudflare.

## 2. Cloudflare → app

Cloudflare connects straight to Traefik, no nginx.

```mermaid
flowchart LR
  V[Visitor] --> CF[Cloudflare]
  CF -->|CF-Connecting-IP| T[Traefik]
  T -->|CF-Connecting-IP| A[app]
```

```bash
# .env
TRUSTED_IP_HEADER=CF-Connecting-IP
# PUBLIC_BIND_HOST stays 0.0.0.0 — Cloudflare reaches Traefik directly
```

Traefik forwards `CF-Connecting-IP` untouched. **Firewall the port to
[Cloudflare's ranges](https://www.cloudflare.com/ips/)** — otherwise anyone can
hit Traefik directly and spoof that header.

## 3. nginx → app

nginx is the edge, no Cloudflare.

```mermaid
flowchart LR
  V[Visitor] -->|TCP| N[nginx]
  N -->|X-Client-IP| T[Traefik]
  T -->|X-Client-IP| A[app]
```

```bash
# .env
PUBLIC_BIND_HOST=127.0.0.1
TRUSTED_IP_HEADER=X-Client-IP
```

```nginx
# /etc/nginx/sites-available/<domain>  — inside the server { } block
location / {
    proxy_pass http://127.0.0.1:${PUBLIC_PORT};
    proxy_set_header X-Client-IP $remote_addr;   # $remote_addr is the real TCP peer
}
```

→ `npm run setup-host-proxy`, answer **no** to Cloudflare. TLS: `sudo certbot --nginx -d <domain>`.

## 4. app

Traefik is public, nothing in front.

```mermaid
flowchart LR
  V[Visitor] -->|TCP| T[Traefik]
  T --> A[app]
```

```bash
# .env
TRUSTED_IP_HEADER=        # empty — app uses the direct connection
```

Heads up: behind Docker's published port the app usually sees the gateway
(`172.18.0.1`), not the visitor. Need real IPs? Put nginx in front (case 3).

## Why not just `X-Forwarded-For`?

Behind a Docker published port, Traefik overwrites `X-Forwarded-For` and
`X-Real-IP` with the Docker gateway IP, so they never carry the real client.
Traefik passes *other* headers (`X-Client-IP`, `CF-Connecting-IP`) through
untouched — that is what these setups rely on. The resolver lives in
`app/backend/src/helpers/real_ip.py` and reads whatever `TRUSTED_IP_HEADER`
names.
