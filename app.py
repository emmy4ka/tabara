"""
Aplicație cazare tabără — versiune simplă, un singur fișier.

Pornire:
    pip install -r requirements.txt
    python seed_data.py      (o singură dată, ca să creeze baza de date)
    streamlit run app.py
"""
from datetime import date
import streamlit as st
from db import query, execute, SQLITE_PATH, USE_SUPABASE
import logic

st.set_page_config(page_title="Tabăra 2026 — Cazare", page_icon="🏕️", layout="wide")

if not USE_SUPABASE and not SQLITE_PATH.exists():
    st.error("Baza de date nu există încă. Rulează în terminal: `python seed_data.py`")
    st.stop()

st.title("🏕️ Tabăra de Muzică Merești — Cazare")

role = st.sidebar.radio("Rol", ["Recepție", "Administrator"])
sectiune = st.sidebar.radio(
    "Secțiune",
    ["👥 Participanți", "📅 Rezervare nouă", "💰 Plăți"] if role == "Recepție"
    else ["📊 Dashboard", "🏠 Case", "↔️ Mută persoană"],
)

ACC_TYPES = {"standard": "Cazare standard", "1nivel": "Căsuță 1 nivel",
             "2nivele": "Căsuță 2 nivele", "hotel": "Cameră hotel"}

# ============================================================ RECEPȚIE ====

if sectiune == "👥 Participanți":
    tab_search, tab_add = st.tabs(["🔎 Caută", "➕ Adaugă"])
    with tab_search:
        q = st.text_input("Caută după nume sau telefon")
        rows = query(
            "SELECT * FROM participants WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? ORDER BY last_name",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ) if q else query("SELECT * FROM participants ORDER BY last_name LIMIT 100")
        if rows:
            st.dataframe([{"Nume": f"{r['last_name']} {r['first_name']}", "Telefon": r["phone"],
                            "Email": r["email"], "Țară": r["country"]} for r in rows], use_container_width=True)
        else:
            st.info("Niciun participant găsit.")
    with tab_add:
        with st.form("add_p"):
            c1, c2 = st.columns(2)
            fn, ln = c1.text_input("Prenume"), c2.text_input("Nume")
            phone, email = c1.text_input("Telefon"), c2.text_input("Email")
            country = st.text_input("Țară", value="Moldova")
            if st.form_submit_button("Salvează"):
                if fn and ln:
                    execute("INSERT INTO participants (first_name,last_name,phone,email,country) VALUES (?,?,?,?,?)",
                            (fn, ln, phone, email, country))
                    st.success(f"✅ {fn} {ln} adăugat(ă).")
                else:
                    st.error("Prenume și nume obligatorii.")

elif sectiune == "📅 Rezervare nouă":
    st.subheader("Rezervare nouă")
    acc_type = st.selectbox("Tip cazare", list(ACC_TYPES.keys()), format_func=lambda x: ACC_TYPES[x])
    c1, c2, c3 = st.columns(3)
    check_in = c1.date_input("Sosire", value=date.today())
    check_out = c2.date_input("Plecare", value=date.today())
    num_persons = c3.number_input("Nr. persoane", min_value=1, value=1)
    whole_unit = acc_type == "2nivele"

    st.markdown("**Participanți** (unul pe linie: Prenume, Nume, Telefon)")
    text_p = st.text_area("Ex: Ion, Popescu, 069123456", height=100)

    if st.button("🔎 Găsește loc disponibil"):
        available = logic.find_available_units(acc_type, int(num_persons), str(check_in), str(check_out))
        st.session_state["available_units"] = available

    available = st.session_state.get("available_units", [])
    if available:
        options = [f"{u['code']} — {u['free_spots']} locuri libere" for u in available]
        choice = st.selectbox("Alege unitatea", options)
        chosen_unit = available[options.index(choice)]

        price_lei, price_eur = logic.calc_price(acc_type, int(num_persons),
                                                   (check_out - check_in).days, whole_unit)
        st.info(f"💰 Preț total: **{price_lei:.0f} lei** / {price_eur:.0f} €")

        if st.button("✅ Confirmă rezervarea"):
            participants = []
            for line in text_p.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    participants.append({"first_name": parts[0], "last_name": parts[1],
                                          "phone": parts[2] if len(parts) > 2 else ""})
            if not participants:
                st.error("Adaugă cel puțin un participant.")
            else:
                logic.create_reservation(acc_type, str(check_in), str(check_out), participants,
                                          unit_id=chosen_unit["id"], whole_unit=whole_unit)
                st.success("✅ Rezervare creată!")
                st.session_state["available_units"] = []
    elif "available_units" in st.session_state:
        st.warning("Nicio unitate disponibilă pentru aceste criterii.")

elif sectiune == "💰 Plăți":
    st.subheader("Plăți")
    rid = st.number_input("ID rezervare", min_value=1, step=1)
    if rid:
        status = logic.payment_status(int(rid))
        if status:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total de plată", f"{status['total_due'] or 0:.0f} lei")
            c2.metric("Achitat", f"{status['paid']:.0f} lei")
            c3.metric("Rest de plată", f"{status['remaining']:.0f} lei")
            with st.form("add_payment"):
                amount = st.number_input("Sumă (lei)", min_value=0.0, step=50.0)
                method = st.selectbox("Metodă", ["numerar", "card", "transfer"])
                if st.form_submit_button("Înregistrează plata"):
                    execute("INSERT INTO payments (reservation_id, amount, currency, method) VALUES (?,?,?,?)",
                            (int(rid), amount, "MDL", method))
                    st.success("✅ Plată înregistrată.")
                    st.rerun()
        else:
            st.error("Rezervare inexistentă.")

# ======================================================== ADMINISTRATOR ===

elif sectiune == "📊 Dashboard":
    summary = logic.occupancy_summary()
    items = list(summary.items())
    for i in range(0, len(items), 2):
        cols = st.columns(2)
        for col, (acc_type, s) in zip(cols, items[i:i + 2]):
            col.metric(ACC_TYPES.get(acc_type, acc_type), f"{s['occupied']} / {s['total']}",
                       help=f"{s['units']} unități")

    st.markdown("### 🟡 Sosiri astăzi")
    arr = logic.today_arrivals()
    if arr:
        st.dataframe([{"Nume": f"{a['first_name']} {a['last_name']}",
                        "Cazare": f"{a['unit_code'] or ACC_TYPES.get(a['accommodation_type'])}"
                                  f"{' / R' + str(a['room_number']) if a['room_number'] else ''}"}
                       for a in arr], use_container_width=True, hide_index=True)
    else:
        st.caption("Nimeni.")

    st.markdown("### 🔴 Plecări astăzi")
    dep = logic.today_departures()
    if dep:
        st.dataframe([{"Nume": f"{d['first_name']} {d['last_name']}",
                        "Cazare": d['unit_code'] or ACC_TYPES.get(d['accommodation_type'])} for d in dep],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("Nimeni.")

elif sectiune == "🏠 Case":
    acc_type = st.selectbox("Tip", list(ACC_TYPES.keys()), format_func=lambda x: ACC_TYPES[x])
    units = query("SELECT * FROM accommodation_units WHERE accommodation_type = ? ORDER BY code", (acc_type,))
    for u in units:
        occ, total = logic.unit_occupancy_today(u)
        icon = "🔴" if occ >= total else ("🟡" if occ > 0 else "🟢")
        with st.expander(f"{icon} {u['code']} — {occ}/{total}"):
            rooms = query("SELECT * FROM rooms WHERE unit_id = ? ORDER BY room_number", (u["id"],))
            for r in rooms:
                occs = query(
                    """SELECT p.first_name, p.last_name FROM reservation_occupants ro
                       JOIN participants p ON p.id = ro.participant_id
                       JOIN reservations res ON res.id = ro.reservation_id
                       WHERE ro.room_id = ? AND res.status = 'activa'
                         AND res.check_in <= ? AND res.check_out > ?""",
                    (r["id"], str(date.today()), str(date.today())),
                )
                names = ", ".join(f"{o['first_name']} {o['last_name']}" for o in occs) or "— liberă —"
                st.write(f"**Camera {r['room_number']}** ({r['capacity']} locuri): {names}")

elif sectiune == "↔️ Mută persoană":
    q = st.text_input("Caută persoana de mutat (nume)")
    if q:
        rows = query(
            """SELECT ro.id AS occ_id, p.first_name, p.last_name, au.code, rm.room_number
               FROM reservation_occupants ro
               JOIN participants p ON p.id = ro.participant_id
               JOIN reservations res ON res.id = ro.reservation_id
               LEFT JOIN accommodation_units au ON au.id = res.unit_id
               LEFT JOIN rooms rm ON rm.id = ro.room_id
               WHERE res.status = 'activa' AND (p.first_name LIKE ? OR p.last_name LIKE ?)""",
            (f"%{q}%", f"%{q}%"),
        )
        all_units = query("SELECT * FROM accommodation_units ORDER BY code")
        for r in rows:
            st.write(f"**{r['first_name']} {r['last_name']}** — acum: {r['code']} / Camera {r['room_number']}")
            unit_codes = [u["code"] for u in all_units]
            default_idx = unit_codes.index(r["code"]) if r["code"] in unit_codes else 0
            new_unit_code = st.selectbox("Unitate nouă", unit_codes, index=default_idx, key=f"unit_{r['occ_id']}")
            chosen_unit = next(u for u in all_units if u["code"] == new_unit_code)
            unit_rooms = query("SELECT * FROM rooms WHERE unit_id = ? ORDER BY room_number", (chosen_unit["id"],))
            room_numbers = [rm["room_number"] for rm in unit_rooms]
            if room_numbers:
                new_room_num = st.selectbox("Cameră nouă", room_numbers, key=f"room_{r['occ_id']}")
                if st.button("✅ Confirmă mutarea", key=f"btn_{r['occ_id']}", use_container_width=True):
                    new_room = next(rm for rm in unit_rooms if rm["room_number"] == new_room_num)
                    logic.move_occupant(r["occ_id"], new_room["id"])
                    st.success("✅ Mutat!")
                    st.rerun()
            else:
                st.caption("Această unitate nu are camere definite.")
            st.divider()
