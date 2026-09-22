# SHMS - Smart Health Management System

## Project
Django-based Smart Health Management System for IGNOU MCA project.

## Stack
- Python
- Django
- PostgreSQL
- HTML
- Tailwind-style utility classes used by the existing UI
- JavaScript only where required

## User Roles
- ADMIN
- DOCTOR
- PATIENT
- RECEPTIONIST

## Current Architecture
- Custom User model
- Patient profile
- Doctor profile
- Appointment module
- Prescription module
- Billing/Payment planned

## Security Rules
- Never bypass role-based access control.
- Use existing @role_required decorator.
- Never expose another user's private medical data.
- Validate all POST requests.
- Use Django forms for server-side validation.
- Never trust client-side validation.
- Use ORM instead of raw SQL unless explicitly required.
- Do not hardcode database IDs.

## UI Rules
- Preserve existing Stitch UI classes.
- Do not redesign existing pages unless explicitly requested.
- Use existing base.html/navbar/sidebar/footer.
- Keep UI responsive.
- Do not introduce unnecessary dependencies.

## Git Rules
- Never modify main directly.
- Work on the current feature branch.
- Do not commit unless explicitly asked.
- Before finishing, show changed files and explain changes.