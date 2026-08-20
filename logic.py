"""Reguli de business: disponibilitate, rezervări, mutări, dashboard."""
from datetime import date
from db import query, execute


# ---------------------------------------------------------------- TARIFE ---
def get_tariffs():
    return {t["accommodation_type"]: t for t in query("SELECT * FROM tariffs")}


def calc_price(accommodation_type, num_persons, num_nights, whole_unit=False):
    t = get_tariffs().get(accommodation_type)
    if not t:
        return 0, 0
    if t["unit"] == "casa":
        lei, eur = t["price_lei"], t["price_eur"]
    elif t["unit"] == "camera_noapte":
        lei, eur = t["price_lei"] * num_nights, t["price_eur"] * num_nights
    else:  # persoana
        lei, eur = t["price_lei"] * num_persons, t["price_eur"] * num_persons
    return lei, eur


# ------------------------------------------------------------ OCUPARE -----
def spots_occupied(unit_id, check_in, check_out):
    """Câte locuri sunt ocupate în unitatea dată, într-o perioadă care se suprapune."""
    rows = query(
        """
        SELECT COALESCE(SUM(r.num_persons), 0) AS total
        FROM reservations r
        WHERE r.unit_id = ?
          AND r.status = 'activa'
          AND r.check_in < ?
          AND r.check_out > ?
        """,
        (unit_id, check_out, check_in),
    )
    return rows[0]["total"] if rows else 0


def find_available_units(accommodation_type, num_persons, check_in, check_out):
    """Returnează unitățile de acest tip cu suficiente locuri libere în perioadă."""
    units = query(
        "SELECT * FROM accommodation_units WHERE accommodation_type = ? ORDER BY code",
        (accommodation_type,),
    )
    results = []
    for u in units:
        occupied = spots_occupied(u["id"], check_in, check_out)
        free = u["total_spots"] - occupied
        if u["whole_unit_only"]:
            if occupied == 0:  # complet liberă
                results.append({**u, "free_spots": u["total_spots"]})
        elif free >= num_persons:
            results.append({**u, "free_spots": free})
    return results


def unit_occupancy_today(unit):
    today = date.today()
    tomorrow = (today.toordinal() + 1)
    from datetime import date as _date
    occupied = spots_occupied(unit["id"], today.isoformat(), _date.fromordinal(tomorrow).isoformat())
    return occupied, unit["total_spots"]


# --------------------------------------------------------- REZERVĂRI ------
def create_reservation(accommodation_type, check_in, check_out, participants,
                        unit_id=None, whole_unit=False):
    """
    participants: listă de dict-uri {first_name, last_name, phone, email, country}
    Creează participanții (dacă nu există deja), rezervarea, și le leagă.
    """
    num_persons = len(participants)
    nights = (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days
    price_lei, price_eur = calc_price(accommodation_type, num_persons, nights, whole_unit)

    reservation_id = execute(
        """INSERT INTO reservations
           (accommodation_type, check_in, check_out, num_persons, whole_unit,
            unit_id, price_total_lei, price_total_eur)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (accommodation_type, check_in, check_out, num_persons, int(whole_unit),
         unit_id, price_lei, price_eur),
    )

    # camere disponibile în unitate (dacă e cazul), pentru atribuire automată
    available_rooms = []
    if unit_id and accommodation_type != "standard":
        rooms = query("SELECT * FROM rooms WHERE unit_id = ? ORDER BY room_number", (unit_id,))
        for r in rooms:
            taken = query(
                """SELECT COUNT(*) AS c FROM reservation_occupants ro
                   JOIN reservations res ON res.id = ro.reservation_id
                   WHERE ro.room_id = ? AND res.status = 'activa'
                     AND res.check_in < ? AND res.check_out > ?""",
                (r["id"], check_out, check_in),
            )[0]["c"]
            free_in_room = r["capacity"] - taken
            for _ in range(free_in_room):
                available_rooms.append(r["id"])

    for i, p in enumerate(participants):
        existing = query(
            "SELECT id FROM participants WHERE first_name = ? AND last_name = ? AND phone = ?",
            (p["first_name"], p["last_name"], p.get("phone", "")),
        )
        if existing:
            participant_id = existing[0]["id"]
        else:
            participant_id = execute(
                """INSERT INTO participants (first_name, last_name, phone, email, country)
                   VALUES (?, ?, ?, ?, ?)""",
                (p["first_name"], p["last_name"], p.get("phone", ""), p.get("email", ""), p.get("country", "")),
            )
        room_id = available_rooms[i] if i < len(available_rooms) else None
        execute(
            "INSERT INTO reservation_occupants (reservation_id, participant_id, room_id) VALUES (?, ?, ?)",
            (reservation_id, participant_id, room_id),
        )

    return reservation_id


def move_occupant(occupant_id, new_room_id):
    execute("UPDATE reservation_occupants SET room_id = ? WHERE id = ?", (new_room_id, occupant_id))


# ---------------------------------------------------------- DASHBOARD -----
def today_arrivals():
    today = date.today().isoformat()
    return query(
        """SELECT p.first_name, p.last_name, r.accommodation_type, au.code AS unit_code,
                  rm.room_number
           FROM reservations r
           JOIN reservation_occupants ro ON ro.reservation_id = r.id
           JOIN participants p ON p.id = ro.participant_id
           LEFT JOIN accommodation_units au ON au.id = r.unit_id
           LEFT JOIN rooms rm ON rm.id = ro.room_id
           WHERE r.check_in = ? AND r.status = 'activa'""",
        (today,),
    )


def today_departures():
    today = date.today().isoformat()
    return query(
        """SELECT p.first_name, p.last_name, r.accommodation_type, au.code AS unit_code
           FROM reservations r
           JOIN reservation_occupants ro ON ro.reservation_id = r.id
           JOIN participants p ON p.id = ro.participant_id
           LEFT JOIN accommodation_units au ON au.id = r.unit_id
           WHERE r.check_out = ? AND r.status = 'activa'""",
        (today,),
    )


def occupancy_summary():
    units = query("SELECT * FROM accommodation_units")
    summary = {}
    for u in units:
        occ, total = unit_occupancy_today(u)
        t = u["accommodation_type"]
        s = summary.setdefault(t, {"occupied": 0, "total": 0, "units": 0})
        s["occupied"] += occ
        s["total"] += total
        s["units"] += 1
    return summary


def payment_status(reservation_id):
    res = query("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
    if not res:
        return None
    res = res[0]
    paid = query(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE reservation_id = ? AND currency = 'MDL'",
        (reservation_id,),
    )[0]["total"]
    return {"total_due": res["price_total_lei"], "paid": paid, "remaining": (res["price_total_lei"] or 0) - paid}
