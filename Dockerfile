# The site is plain static files; Caddy just serves them.
FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY . /usr/share/caddy
