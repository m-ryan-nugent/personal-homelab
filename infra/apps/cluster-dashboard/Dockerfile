FROM nginx:alpine

LABEL org.opencontainers.image.title="cluster-dashboard" \
	org.opencontainers.image.description="Static Raspberry Pi homelab cluster dashboard" \
	org.opencontainers.image.source="https://github.com/m-ryan-nugent/personal-homelab"

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/ /usr/share/nginx/html/frontend/

EXPOSE 80