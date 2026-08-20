-- ============================================================
-- SCHEMA (versiune PostgreSQL / Supabase)
-- Rulează acest fișier în Supabase → SQL Editor.
-- Pentru dezvoltare locală (SQLite) folosește schema.sql, nu pe acesta.
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('receptie', 'administrator')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tariffs (
    id                  SERIAL PRIMARY KEY,
    accommodation_type  TEXT UNIQUE NOT NULL,
    price_lei           REAL NOT NULL,
    price_eur           REAL NOT NULL,
    unit                TEXT NOT NULL,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accommodation_units (
    id                  SERIAL PRIMARY KEY,
    code                TEXT UNIQUE NOT NULL,
    accommodation_type  TEXT NOT NULL,
    total_rooms         INTEGER NOT NULL DEFAULT 1,
    total_spots         INTEGER NOT NULL,
    whole_unit_only     INTEGER NOT NULL DEFAULT 0,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS rooms (
    id          SERIAL PRIMARY KEY,
    unit_id     INTEGER NOT NULL REFERENCES accommodation_units(id) ON DELETE CASCADE,
    room_number INTEGER NOT NULL,
    capacity    INTEGER NOT NULL DEFAULT 2,
    UNIQUE(unit_id, room_number)
);

CREATE TABLE IF NOT EXISTS participants (
    id          SERIAL PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    phone       TEXT,
    email       TEXT,
    country     TEXT,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reservations (
    id                  SERIAL PRIMARY KEY,
    accommodation_type  TEXT NOT NULL,
    check_in            DATE NOT NULL,
    check_out           DATE NOT NULL,
    num_persons         INTEGER NOT NULL DEFAULT 1,
    whole_unit          INTEGER NOT NULL DEFAULT 0,
    unit_id             INTEGER REFERENCES accommodation_units(id),
    price_total_lei     REAL,
    price_total_eur     REAL,
    status              TEXT NOT NULL DEFAULT 'activa' CHECK (status IN ('activa','anulata','finalizata')),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reservation_occupants (
    id             SERIAL PRIMARY KEY,
    reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    room_id        INTEGER REFERENCES rooms(id),
    checked_in     INTEGER NOT NULL DEFAULT 0,
    checked_out    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS payments (
    id             SERIAL PRIMARY KEY,
    reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    amount         REAL NOT NULL,
    currency       TEXT NOT NULL DEFAULT 'MDL',
    payment_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    method         TEXT,
    note           TEXT
);

CREATE INDEX IF NOT EXISTS idx_reservations_dates ON reservations(check_in, check_out);
CREATE INDEX IF NOT EXISTS idx_reservations_unit ON reservations(unit_id);
CREATE INDEX IF NOT EXISTS idx_occupants_reservation ON reservation_occupants(reservation_id);
CREATE INDEX IF NOT EXISTS idx_rooms_unit ON rooms(unit_id);
CREATE INDEX IF NOT EXISTS idx_payments_reservation ON payments(reservation_id);
