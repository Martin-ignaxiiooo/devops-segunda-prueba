-- Esquema del microservicio Empresas de EP1. Los registros se crean mediante la API.
CREATE TABLE IF NOT EXISTS empresas (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    industria VARCHAR(255),
    plan VARCHAR(255)
);
