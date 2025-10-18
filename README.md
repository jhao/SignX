# SignX

SignX is a lightweight digital signature service built with Flask. It provides a multi-tenant ready envelope workflow with role based access control, PDF conversion, scheduled background jobs, and audit trails suitable for electronic signing flows.

## Features

- Modular Flask application with blueprints for authentication, envelope lifecycle, signing workflow, and administrative tooling.
- SQLAlchemy ORM models with Alembic migrations implementing the SRS entities (User, Envelope, Document, Signer, Field, Signature, CryptoRecord, AuditEvent, Notification).
- REST APIs covering authentication, envelope creation and sending, signer validation, signing submission, PDF download, and audit retrieval.
- File upload and conversion pipeline backed by LibreOffice, with APScheduler jobs for conversion, expiration handling, and storage cleanup.
- Signature rendering with canvas capture support, PDF overlay using PikePDF/ReportLab, and optional PAdES signing via pyHanko.
- SMTP integration through Flask-Mail for invitations, reminders, and completion notices.
- Bootstrap-based front-end templates with a sender dashboard and signer ceremony UI.
- Dockerfile and docker-compose configuration for local development.

## Getting Started

### Requirements

- Docker and docker-compose *(recommended)*, or Python 3.11 with LibreOffice installed locally.

### Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

```bash
cp .env.example .env
```

### Running with Docker Compose

```bash
docker-compose up --build
```

The application will be available at `http://localhost:5000`, with MailHog UI at `http://localhost:8025`.

### Database Migrations

Use Flask-Migrate/Alembic to manage schema changes:

```bash
flask db upgrade
```

### Running Locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app wsgi.py --debug run
```

## Project Structure

```
app/
  auth/              # Authentication blueprint
  envelopes/         # Envelope creation and delivery
  signing/           # Signing ceremony endpoints
  admin/             # Administrative APIs
  models.py          # ORM models and state machine helpers
  pdf.py             # PDF overlay and PAdES integration
  storage.py         # File persistence and conversion helpers
  templates/         # Jinja templates for dashboard and signing
  static/            # Bootstrap-friendly assets
migrations/          # Alembic migrations
```

## Testing the Workflow

1. Register a user via `POST /api/auth/register`.
2. Authenticate with `POST /api/auth/login`.
3. Create an envelope through `POST /api/envelopes/` with document uploads and signer list.
4. Send the envelope with `POST /api/envelopes/<id>/send` to issue invitations.
5. Signers follow the `/api/signing/validate/<token>` link to review documents and submit signatures.
6. Download completed documents via `/api/signing/documents/<id>/download` and review audit history under `/api/admin/audits`.

## License

MIT
