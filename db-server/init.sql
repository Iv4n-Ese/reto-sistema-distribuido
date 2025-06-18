-- Base de datos: personas registradas
CREATE DATABASE IF NOT EXISTS Personas_Registradas;

-- Tabla: personas
CREATE TABLE IF NOT EXISTS personas (
    id SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    sexo CHAR(1) CHECK (sexo IN ('M', 'F', 'O')),
    nacionalidad VARCHAR(50),
    estado_civil VARCHAR(50),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: domicilios
CREATE TABLE IF NOT EXISTS domicilios (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER REFERENCES personas(id) ON DELETE CASCADE,
    direccion VARCHAR(250),
    ciudad VARCHAR(100),
    estado VARCHAR(100),
    codigo_postal VARCHAR(20)
);

-- Tabla: movimientos
CREATE TABLE IF NOT EXISTS movimientos (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER REFERENCES personas(id) ON DELETE CASCADE,
    tipo_movimiento VARCHAR(100),
    fecha_movimiento DATE,
    observaciones TEXT
);


?

CREATE TABLE IF NOT EXISTS resumen_movimientos (
    id INTEGER PRIMARY KEY,
    nombre_completo TEXT,
    total_movimientos INTEGER,
    ultimo_movimiento DATE
);

?
DELETE FROM resumen_movimientos;

INSERT INTO resumen_movimientos (id, nombre_completo, total_movimientos, ultimo_movimiento)
SELECT
    p.id,
    p.nombre_completo,
    COUNT(m.id),
    MAX(m.fecha_movimiento)
FROM personas p
LEFT JOIN movimientos m ON p.id = m.persona_id
GROUP BY p.id, p.nombre_completo;


-- Vista materializada: resumen de movimientos
CREATE MATERIALIZED VIEW IF NOT EXISTS resumen_movimientos AS
SELECT
    p.id,
    p.nombre_completo,
    COUNT(m.id) AS total_movimientos,
    MAX(m.fecha_movimiento) AS ultimo_movimiento
FROM personas p
LEFT JOIN movimientos m ON p.id = m.persona_id
GROUP BY p.id, p.nombre_completo;
