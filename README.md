# Smart Health Management System (SHMS)

SHMS is a Django web application for managing patients, doctors, appointments, prescriptions, reception, and billing in a clinic. It provides role-specific workflows for administrators, doctors, receptionists, and patients.

## Current features

### Accounts and access control

- Custom Django user model with email-based authentication, profile details, and `ADMIN`, `DOCTOR`, `RECEPTIONIST`, and `PATIENT` roles.
- Login and logout views; role-based routing sends signed-in users to the dashboard for their role.
- Administrative account directory with search, role and active-status filters, pagination, and account activation/deactivation.
- Protected views restrict access to the roles that need each workflow.

### Patient records

- Admins and receptionists can register, search, view, update, and delete patient records.
- Patient IDs are generated automatically. Patient records include contact details, date of birth, gender, blood group, allergies, and medical history.
- Patients can view and edit their own profile and review their own appointments, prescriptions, bills, and receipts.

### Doctor management and schedules

- Admins can register, view, search, update, and delete doctors and change doctor availability.
- Doctor profiles include specialization, qualifications, experience, consultation fee, and availability.
- Doctors manage recurring weekday schedules. Active doctor leave entries are excluded from booking availability; leave records are available in Django admin.
- Doctors have a dashboard with appointment and prescription counts, and can review their patients' clinical summaries.

### Appointments and reception

- Patients can book appointments and view, reschedule, or cancel their own appointments.
- Staff can create and manage appointments, search and filter appointments by text, status, and date, and review appointment details.
- Appointment booking uses a schedule-based availability flow: 30-minute slots, no bookings during recorded doctor leave, and a booking window from today through 60 days ahead.
- Authenticated availability endpoints provide available dates and times for the booking form.
- Receptionists can view appointment and check-in summaries, search and filter appointments, and record patient check-ins.
- Appointment status transitions are validated by the appointment service; active doctor time slots cannot be double-booked.

### Prescriptions

- Doctors can create and update a prescription for an appointment, including diagnosis, remarks, and prescribed medicines with dosage, frequency, duration, and instructions.
- Each appointment can have at most one prescription.
- Patients have read-only views of their prescriptions and prescription details.

### Billing and payments

- Bills can be created for completed appointments, with tax type and calculated total.
- Payments record amount, method, payment type, and optional transaction reference; the bill tracks pending, partial, or paid status.
- Admins, receptionists, and doctors can view billing details; doctors and admins can record payments. Patients can view their own bills and receipts. The PDF receipt endpoint applies role-based record scoping.
- Payment recording is part of the application; no external payment gateway is configured.

## Roles at a glance

| Role | Main workflows |
| --- | --- |
| `ADMIN` | Dashboard, account management, patient and doctor management, appointments, prescription review, and billing access |
| `DOCTOR` | Doctor dashboard, own appointments, patient clinical summaries, schedules, prescriptions, and permitted billing workflows |
| `RECEPTIONIST` | Reception dashboard, patient and doctor lookup/management, appointment management, and patient check-in |
| `PATIENT` | Own profile, appointment booking and history, prescriptions, bills, and payment receipts |

## Technology

- Python 3.12+
- Django 6.0.8
- SQLite by default for local development; PostgreSQL is supported through `DATABASE_URL`
- `dj-database-url`, `python-decouple`, `psycopg2-binary`, Pillow, and ReportLab (see [`requirements.txt`](./requirements.txt))
- Django templates, Tailwind CSS via CDN, project CSS in `static/css/style.css`, Inter, and Material Symbols

## Project layout

```text
config/          Django settings, root URLs, ASGI and WSGI
accounts/        Custom user model, authentication and roles
core/            Shared decorators, permissions and utilities
dashboard/       Role-based landing page and admin account management
patients/        Patient profiles and management
doctors/         Doctor profiles, schedules, leave and clinical views
appointments/    Booking, availability, appointment lifecycle and check-in support
prescriptions/   Prescriptions and medicine records
billing/         Bills, payments and receipts
receptionist/    Receptionist accounts, appointment desk and check-in
templates/       Shared layout and app templates
static/          CSS and static assets
manage.py        Django management entry point
```

## Run locally

Use Python 3.12 or newer and run the following from the project directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the project directory for local settings. `.env` is ignored by Git:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=True
# Optional: omit DATABASE_URL to use the local SQLite database.
# For PostgreSQL, set DATABASE_URL to your database connection URL.
```

Password-reset emails are printed to the console in development. In production,
configure an SMTP provider using environment variables (never commit credentials):

```dotenv
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=SHMS Support <noreply@example.com>
```

With `DEBUG=False`, SHMS uses Django's SMTP email backend by default. You can
override it with `EMAIL_BACKEND` if your deployment uses another Django email
backend.

Apply migrations and start the development server:

```powershell
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Create an administrator account with `python manage.py createsuperuser`; administrator-created accounts are used for the other staff and patient roles.

The project uses Django's configured custom user model (`accounts.User`). Set environment variables before the first migration if you use a non-default database. For PostgreSQL, provide a valid `DATABASE_URL` and ensure the database is available.

## Tests and useful commands

Run the full Django test suite:

```powershell
python manage.py test
```

Run a module's tests, for example:

```powershell
python manage.py test appointments
```

Other useful commands:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

## Configuration and deployment notes

- `SECRET_KEY`, `DEBUG`, and `DATABASE_URL` are read from the environment (or a local `.env` file). Always set a private `SECRET_KEY`; do not use Django's insecure development fallback in production.
- With `DEBUG=False`, the settings enable HTTPS redirection and secure cookies. Use HTTPS in deployment; set `DEBUG=True` only for local development.
- `VERCEL_URL` can extend the configured allowed hosts and CSRF trusted origins.
- [`vercel.json`](./vercel.json) currently declares a Python 3.9 runtime, while the dependency list uses Django 6.0.8. Align the deployment runtime with the Python version supported by the installed Django release before deploying.

## Data and privacy

The application handles personal and medical information. Use role-restricted accounts, protect production credentials, and use appropriately secured databases and HTTPS for deployed environments.

## Maintainer

Ritesh Tiwari
