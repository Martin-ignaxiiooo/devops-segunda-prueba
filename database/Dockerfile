FROM postgres:16-alpine
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql
EXPOSE 5432
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
