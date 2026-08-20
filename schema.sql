-- ============================================================
-- SCHEMA: Aplicație cazare tabără
-- Compatibil SQLite (dezvoltare locală) și PostgreSQL/Supabase (producție)
-- ============================================================

-- ---------- UTILIZATORI (recepție / administrator) ----------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('receptie', 'administrator')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- TARIFE (editabile din Setări, nu hardcodate) ----------
CREATE TABLE IF NOT EXISTS tariffs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    accommodation_type TEXT UNIQUE NOT NULL,  -- 'standard' | '1nivel' | '2nivele' | 'hotel'
    price_lei        REAL NOT NULL,
    price_eur        REAL NOT NULL,
    unit             TEXT NOT NULL,           -- 'persoana' | 'casa' | 'camera_noapte'
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- UNITĂȚI DE CAZARE (case, hotel) ----------
CREATE TABLE IF NOT EXISTS accommodation_units (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    code               TEXT UNIQUE NOT NULL,   -- ex: '1N-04', '2N-01', 'H-03'
    accommodation_type TEXT NOT NULL,          -- 'standard' | '1nivel' | '2nivele' | 'hotel'
    total_rooms        INTEGER NOT NULL DEFAULT 1,
    total_spots         INTEGER NOT NULL,       -- capacitate totală (locuri sau camere)
    whole_unit_only    INTEGER NOT NULL DEFAULT 0, -- 1 = se închiriază doar integral (2 nivele)
    notes              TEXT
);

-- ---------- CAMERE (în interiorul unei unități) ----------
CREATE TABLE IF NOT EXISTS rooms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id     INTEGER NOT NULL REFERENCES accommodation_units(id) ON DELETE CASCADE,
    room_number INTEGER NOT NULL,      -- 1, 2, 3...
    capacity    INTEGER NOT NULL DEFAULT 2,
    UNIQUE(unit_id, room_number)
);

-- ---------- PARTICIPANȚI ----------
CREATE TABLE IF NOT EXISTS participants (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    phone       TEXT,
    email       TEXT,
    country     TEXT,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- REZERVĂRI ----------
-- O rezervare = o "unitate de business": fie o persoană singură (standard/1 nivel/hotel),
-- fie un grup care închiriază o casă întreagă (2 nivele).
CREATE TABLE IF NOT EXISTS reservations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    accommodation_type TEXT NOT NULL,          -- 'standard' | '1nivel' | '2nivele' | 'hotel'
    check_in           DATE NOT NULL,
    check_out          DATE NOT NULL,
    num_persons        INTEGER NOT NULL DEFAULT 1,
    whole_unit         INTEGER NOT NULL DEFAULT 0,  -- 1 dacă e rezervare de unitate întreagă
    unit_id            INTEGER REFERENCES accommodation_units(id),
    price_total_lei    REAL,
    price_total_eur    REAL,
    status             TEXT NOT NULL DEFAULT 'activa' CHECK (status IN ('activa','anulata','finalizata')),
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- LEGĂTURA participant <-> rezervare <-> cameră/loc ----------
-- Permite mai mulți participanți pe aceeași rezervare (familie/grup),
-- fiecare atribuit (opțional) unei camere specifice.
CREATE TABLE IF NOT EXISTS reservation_occupants (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    room_id        INTEGER REFERENCES rooms(id),  -- NULL pentru cazare standard (fără cameră fixă)
    checked_in     INTEGER NOT NULL DEFAULT 0,
    checked_out    INTEGER NOT NULL DEFAULT 0
);

-- ---------- PLĂȚI ----------
CREATE TABLE IF NOT EXISTS payments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    amount         REAL NOT NULL,
    currency       TEXT NOT NULL DEFAULT 'MDL',  -- 'MDL' | 'EUR'
    payment_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    method         TEXT,                          -- 'numerar' | 'card' | 'transfer'
    note           TEXT
);

-- ---------- INDECȘI utili ----------
CREATE INDEX IF NOT EXISTS idx_reservations_dates ON reservations(check_in, check_out);
CREATE INDEX IF NOT EXISTS idx_reservations_unit ON reservations(unit_id);
CREATE INDEX IF NOT EXISTS idx_occupants_reservation ON reservation_occupants(reservation_id);
CREATE INDEX IF NOT EXISTS idx_rooms_unit ON rooms(unit_id);
CREATE INDEX IF NOT EXISTS idx_payments_reservation ON payments(reservation_id);
