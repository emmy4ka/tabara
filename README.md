# Aplicație cazare — Tabăra de Muzică Merești

## 1. Rulează pe calculatorul tău (5 minute)

```bash
pip install -r requirements.txt
python seed_data.py       # o singură dată — creează baza de date + tarifele + cele 9+6 căsuțe + hotel
streamlit run app.py
```

Se deschide în browser. Gata — poți testa imediat: adaugă un participant, fă o rezervare, vezi dashboard-ul de administrator.

Verifică în `seed_data.py` (sus, secțiunea CONFIGURARE) că numerele sunt corecte:
numărul de căsuțe, camere/casă, locuri/cameră, capacitatea zonei standard, numărul de camere de hotel.
Modifici acolo, ștergi fișierul `tabara.db` și rulezi din nou `python seed_data.py`.

## 2. Ce face aplicația acum

- **Recepție**: caută/adaugă participanți, creează rezervări (cu găsire automată a unei căsuțe cu locuri libere), înregistrează plăți.
- **Administrator**: dashboard cu ocupare pe tip de cazare, sosiri/plecări de azi, listă case cu ocupare pe cameră, mutare persoană dintr-o cameră în alta.

Ce **nu** are încă (le adăugăm quando ai timp): parole/conturi separate pe utilizator, export/rapoarte, editare tarife din interfață, ștergere/anulare rezervări.

## 3. Cum o pui online, gratuit, ca s-o vadă toată lumea în timp real

Pas cu pas:

1. **Creează cont gratuit pe [supabase.com](https://supabase.com)** → New Project → alegi o parolă pentru baza de date (o notezi undeva sigur).
2. În Supabase, mergi la **SQL Editor** → lipești tot conținutul din `schema_postgres.sql` (NU `schema.sql` — acela e doar pentru testarea locală) → Run. Asta creează tabelele.
3. Rulează local, o singură dată, `python seed_data.py` **conectat la Supabase** (vezi pasul 4) ca să populeze căsuțele și tarifele.
4. În Supabase → **Project Settings → Database** găsești: Host, Port, Database name, User, Password. Le pui ca variabile de mediu:
   ```bash
   export SUPABASE_URL=1          # doar ca să activeze modul online
   export SUPABASE_DB_HOST=...
   export SUPABASE_DB_PASSWORD=...
   ```
5. **Pune codul pe GitHub** (repo nou, privat sau public).
6. Mergi pe **share.streamlit.io** (Streamlit Community Cloud, gratuit) → conectezi contul de GitHub → alegi repo-ul → în **Settings → Secrets** adaugi aceleași variabile (SUPABASE_URL, SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD etc.) → Deploy.

Gata — primești un link de tipul `tabara2026.streamlit.app` pe care îl deschide oricine, de pe orice telefon/laptop, și toți văd aceleași date, live.

Dacă vrei, te ajut la pasul cu Supabase/Streamlit Cloud direct când ajungi acolo — spune-mi doar unde te-ai blocat.

## 4. Fișiere

- `schema.sql` — structura bazei de date
- `db.py` — conexiunea (local SQLite sau Supabase, automat)
- `logic.py` — reguli: calcul preț, căutare loc liber, ocupare, mutare
- `seed_data.py` — populează căsuțele/tarifele
- `app.py` — toată interfața (Streamlit)
