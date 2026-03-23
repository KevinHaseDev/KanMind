# KanMind Backend

Django REST API for KanMind (boards, tasks, comments, authentication).

## Tech Stack

- Python 3.14
- Django 6.0.3
- Django REST Framework 3.16.1
- Token Authentication (DRF Authtoken)
- SQLite (local)

## Project Structure

- `core/` Central Django configuration (`settings.py`, `urls.py`)
- `auth_app/` Custom user, registration, login
- `board_app/` Board management
- `task_app/` Task and comment management

## Requirements

- Python 3.14+
- `pip`
- `git`

## Local Setup

### Clone the repository

```powershell
git clone <your-repository-url>
cd KanMind_backend
```

### Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
pip install -r requirements.txt
```

### Create `.env` in the project root

```env
SECRET_KEY=your-long-secret-development-key
```

### Run database migrations

```powershell
python manage.py migrate
```

### Create a superuser for Django Admin

```powershell
python manage.py createsuperuser
```

### Start the development server

```powershell
python manage.py runserver
```

The API is then available at:

- `http://127.0.0.1:8000/api/`
- Admin: `http://127.0.0.1:8000/admin/`

## Authentication

This project uses token authentication.

- Public endpoints:
- `POST /api/registration/`
- `POST /api/login/`
- All other endpoints require by default:
- Header `Authorization: Token <your_token>`

Example header:

```http
Authorization: Token 0123456789abcdef0123456789abcdef01234567
```

## Useful Management Commands

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
```

## CORS (Development)

`CORS_ALLOW_ALL_ORIGINS = True` is currently enabled in settings. This is practical for local development, but should be restricted in production.

## Production (Quick Notes)

Before deploying, at minimum:

- `DEBUG = False`
- Set `ALLOWED_HOSTS`
- Use a secure `SECRET_KEY`
- Restrict CORS configuration
- Use a production database instead of SQLite

