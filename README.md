# Healthcare Backend (Django + DRF + PostgreSQL + JWT)

Backend for managing patients, doctors, and patient-doctor assignments with JWT auth.

## Stack
- Django 4.2, Django REST Framework, `djangorestframework-simplejwt`
- PostgreSQL via `psycopg2-binary` (config through `.env`)
- Django ORM, consistent error shape `{"error": ...}`

## Project layout
```
config/        # settings, urls, wsgi/asgi, exception handler, validators
accounts/      # custom User (email login), register/login/refresh
patients/      # Patient model + CRUD (scoped to created_by user)
doctors/       # Doctor model + CRUD
mappings/      # PatientDoctorMapping + assign/list/remove
manage.py
requirements.txt
.env / .env.example
```

## Setup

1. Install deps:
```bash
pip install -r requirements.txt
```

2. Start PostgreSQL and create the DB:
```sql
CREATE DATABASE healthcare_db;
-- defaults in .env: user=postgres password=postgres host=localhost port=5432
```

3. Configure `.env` (copy from `.env.example`, set `SECRET_KEY`, DB creds).
   - PostgreSQL is the default. Only for quick local testing without Postgres:
     `USE_SQLITE=True`.

4. Migrate and run:
```bash
python manage.py migrate
python manage.py runserver
```

## API endpoints

Auth (public):
- `POST /api/auth/register/` — `{name, email, password}` → 201 (email stored lowercase)
- `POST /api/auth/login/` — `{email, password}` → `{refresh, access}`
- `POST /api/auth/refresh/` — `{refresh}` → `{access}`

Use `Authorization: Bearer <access>` for everything below.

Patients (only records created by the logged-in user; other users get 404):
- `POST /api/patients/` · `GET /api/patients/`
- `GET /api/patients/<id>/` · `PUT /api/patients/<id>/` · `DELETE /api/patients/<id>/`
- Patient fields: `name, age (1-150), gender (M/F/O), address, phone, disease`

Doctors (authenticated; list is global per spec):
- `POST /api/doctors/` · `GET /api/doctors/`
- `GET /api/doctors/<id>/` · `PUT /api/doctors/<id>/` · `DELETE /api/doctors/<id>/`
- Doctor fields: `name, specialization, phone, email`

Mappings (authenticated, scoped to your own patients):
- `POST /api/mappings/` — `{patient, doctor}` → 201 (rejects duplicates and
  other users' patients)
- `GET /api/mappings/` — your mappings
- `GET /api/mappings/<patient_id>/` — doctors assigned to one of your patients
  (`{patient_id, doctors, mappings}`; empty `doctors` if none yet, 404 if the
  patient isn't yours or doesn't exist)
  - explicit alias: `GET /api/mappings/patient/<patient_id>/`
- `DELETE /api/mappings/<id>/` — remove by mapping id (404 if not yours)

Errors: all failures return `{"error": ...}` — a message string for
auth/not-found errors, or `{"error": {"field": ["msg"]}}` for validation.

## Tests
```bash
USE_SQLITE=True python manage.py test        # SQLite (no Postgres needed)
python manage.py test                        # against PostgreSQL from .env
```
39 tests cover auth, patient/doctor CRUD + validation, ownership scoping,
mapping uniqueness, and both mapping lookup routes.

## Postman quick test
1. Register → Login → copy `access` token.
2. Set collection auth: Bearer Token = `<access>`.
3. Create patient, create doctor, `POST /api/mappings/` with their ids,
   then `GET /api/mappings/<patient_id>/`, then DELETE mapping/patient/doctor.
4. Unauthenticated `GET /api/patients/` → 401 (expected).
