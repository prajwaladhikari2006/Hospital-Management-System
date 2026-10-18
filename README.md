# 🏥 Smart Healthcare System — MySQL Edition

## What's New (v2 — Unified Auth)
- **Single front page login/register** — no more separate auth per module
- **Patients** can Login or Register
- **Doctors & Receptionists** can only Login (no self-registration)
- **Logout button** always visible in sidebar for all roles
- **Role-based routing**: after login each role sees only their allowed screens

## Default Credentials

| Role         | Username        | Password      |
|--------------|-----------------|---------------|
| Patient      | (register new)  | —             |
| Doctor       | `doctor1`       | `doctor123`   |
| Receptionist | `receptionist1` | `recept123`   |
| Admin        | `admin`         | `admin123`    |

## Run
```bash
streamlit run app.py
```

## Module Access
| Role         | Heart Disease Predictor | Hospital PMS           |
|--------------|------------------------|------------------------|
| Patient      | ✅ Full access          | ❌                     |
| Doctor       | ❌                      | ✅ Appointments, Diagnosis, Rx |
| Receptionist | ❌                      | ✅ Register, Book, Admit, Bill |
| Admin        | ✅ Full + Admin Panel   | ✅ All portals          |
