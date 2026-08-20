"""
Populează baza de date cu:
- tarifele 2026
- cele 9 căsuțe cu 1 nivel (3 camere x 2 locuri = 6 locuri/casă)
- cele 6 căsuțe cu 2 nivele (5 camere x 2 locuri = 10 locuri/casă, doar integral)
- o unitate "standard" (fără camere fixe, capacitate mare)
- camerele de hotel (exemplu: 12 camere)

Rulează o singură dată: python seed_data.py
Poți edita numerele de mai jos (număr de case, capacități) înainte să rulezi.
"""
from db import init_db, execute, query, USE_SUPABASE

# ---------- CONFIGURARE (editează aici dacă numerele reale diferă) ----------
NUM_CASUTE_1_NIVEL = 9
CAMERE_PE_CASUTA_1_NIVEL = 3
LOCURI_PE_CAMERA_1_NIVEL = 2  # => 6 locuri/casă

NUM_CASUTE_2_NIVELE = 6
CAMERE_PE_CASUTA_2_NIVELE = 5
LOCURI_PE_CAMERA_2_NIVELE = 2  # => 10 locuri/casă

CAPACITATE_STANDARD = 250  # persoane, aproximativ — ajustează după nevoie
NUM_CAMERE_HOTEL = 12


def seed():
    if not USE_SUPABASE:
        init_db()
    # Dacă ești conectat la Supabase, tabelele trebuie deja create
    # (Pasul 2 din README: rulează schema.sql în SQL Editor) — aici doar populăm datele.

    # --- Tarife 2026 ---
    tarife = [
        ("standard", 2000, 100, "persoana"),
        ("1nivel", 2750, 138, "persoana"),
        ("2nivele", 15000, 750, "casa"),
        ("hotel", 900, 45, "camera_noapte"),
    ]
    for acc_type, lei, eur, unit in tarife:
        existing = query("SELECT id FROM tariffs WHERE accommodation_type = ?", (acc_type,))
        if not existing:
            execute(
                "INSERT INTO tariffs (accommodation_type, price_lei, price_eur, unit) VALUES (?, ?, ?, ?)",
                (acc_type, lei, eur, unit),
            )

    # --- Căsuțe 1 nivel ---
    for i in range(1, NUM_CASUTE_1_NIVEL + 1):
        code = f"1N-{i:02d}"
        existing = query("SELECT id FROM accommodation_units WHERE code = ?", (code,))
        if existing:
            continue
        unit_id = execute(
            "INSERT INTO accommodation_units (code, accommodation_type, total_rooms, total_spots, whole_unit_only) "
            "VALUES (?, '1nivel', ?, ?, 0)",
            (code, CAMERE_PE_CASUTA_1_NIVEL, CAMERE_PE_CASUTA_1_NIVEL * LOCURI_PE_CAMERA_1_NIVEL),
        )
        for r in range(1, CAMERE_PE_CASUTA_1_NIVEL + 1):
            execute(
                "INSERT INTO rooms (unit_id, room_number, capacity) VALUES (?, ?, ?)",
                (unit_id, r, LOCURI_PE_CAMERA_1_NIVEL),
            )

    # --- Căsuțe 2 nivele (doar integral) ---
    for i in range(1, NUM_CASUTE_2_NIVELE + 1):
        code = f"2N-{i:02d}"
        existing = query("SELECT id FROM accommodation_units WHERE code = ?", (code,))
        if existing:
            continue
        unit_id = execute(
            "INSERT INTO accommodation_units (code, accommodation_type, total_rooms, total_spots, whole_unit_only) "
            "VALUES (?, '2nivele', ?, ?, 1)",
            (code, CAMERE_PE_CASUTA_2_NIVELE, CAMERE_PE_CASUTA_2_NIVELE * LOCURI_PE_CAMERA_2_NIVELE),
        )
        for r in range(1, CAMERE_PE_CASUTA_2_NIVELE + 1):
            execute(
                "INSERT INTO rooms (unit_id, room_number, capacity) VALUES (?, ?, ?)",
                (unit_id, r, LOCURI_PE_CAMERA_2_NIVELE),
            )

    # --- Standard (o singură "unitate" fără camere fixe) ---
    existing = query("SELECT id FROM accommodation_units WHERE code = 'STD'")
    if not existing:
        execute(
            "INSERT INTO accommodation_units (code, accommodation_type, total_rooms, total_spots, whole_unit_only) "
            "VALUES ('STD', 'standard', 0, ?, 0)",
            (CAPACITATE_STANDARD,),
        )

    # --- Camere hotel ---
    for i in range(1, NUM_CAMERE_HOTEL + 1):
        code = f"H-{i:02d}"
        existing = query("SELECT id FROM accommodation_units WHERE code = ?", (code,))
        if existing:
            continue
        unit_id = execute(
            "INSERT INTO accommodation_units (code, accommodation_type, total_rooms, total_spots, whole_unit_only) "
            "VALUES (?, 'hotel', 1, 2, 0)",
            (code,),
        )
        execute(
            "INSERT INTO rooms (unit_id, room_number, capacity) VALUES (?, 1, 2)",
            (unit_id,),
        )

    print("✅ Date inițiale create cu succes.")
    print(f"   - {NUM_CASUTE_1_NIVEL} căsuțe 1 nivel")
    print(f"   - {NUM_CASUTE_2_NIVELE} căsuțe 2 nivele")
    print(f"   - 1 unitate standard ({CAPACITATE_STANDARD} locuri)")
    print(f"   - {NUM_CAMERE_HOTEL} camere hotel")


if __name__ == "__main__":
    seed()
