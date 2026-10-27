FROM postgres:16-alpine
# El arranque es directamente como postgres; no necesita el ejecutable gosu.
RUN apk --no-cache upgrade && rm /usr/local/bin/gosu
USER 70:70
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql
EXPOSE 5432
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
