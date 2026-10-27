FROM node:26-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime
USER root
RUN apk --no-cache upgrade
COPY nginx.conf /etc/nginx/conf.d/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
CMD ["/bin/sh", "-ec", "NGINX_RESOLVER=$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf); export NGINX_RESOLVER; envsubst '$BACKEND_HOST $NGINX_RESOLVER' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf; exec nginx -g 'daemon off;'"]
