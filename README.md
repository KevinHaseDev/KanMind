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

## Local Setup

1. Open the repository and switch to the project directory.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Create a `.env` file (at least `SECRET_KEY`).
5. Run migrations.
6. Start the development server.

Example (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` in the project root:

```env
SECRET_KEY=your-long-secret-development-key
```

Run database migrations and start the server:

```powershell
python manage.py migrate
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

## API Endpoints

### Auth

- `POST /api/registration/`
- `POST /api/login/`

### Boards

- `GET /api/boards/`
- `POST /api/boards/`
- `GET /api/boards/{board_id}/`
- `PATCH /api/boards/{board_id}/`
- `DELETE /api/boards/{board_id}/`
- `GET /api/email-check/?email=user@example.com`

### Tasks

- `GET /api/tasks/`
- `POST /api/tasks/`
- `GET /api/tasks/assigned-to-me/`
- `GET /api/tasks/reviewing/`
- `GET /api/tasks/{task_id}/`
- `PATCH /api/tasks/{task_id}/`
- `DELETE /api/tasks/{task_id}/`
- `GET /api/tasks/{task_id}/comments/`
- `POST /api/tasks/{task_id}/comments/`
- `DELETE /api/tasks/{task_id}/comments/{comment_id}/`

## Request/Response Examples

### Registration

Request:

```json
{
  "fullname": "Max Mustermann",
  "email": "max@example.com",
  "password": "strongpass123",
  "repeated_password": "strongpass123"
}
```

Response (201):

```json
{
  "token": "<token>",
  "fullname": "Max Mustermann",
  "email": "max@example.com",
  "user_id": 1
}
```

### Login

Request:

```json
{
  "email": "max@example.com",
  "password": "strongpass123"
}
```

Response (200):

```json
{
  "token": "<token>",
  "fullname": "Max Mustermann",
  "email": "max@example.com",
  "user_id": 1
}
```

### Create Board

Request:

```json
{
  "title": "Sprint Board",
  "members": [1, 2]
}
```

Note: The owner is set server-side and always remains a member.

### Create Task

Request:

```json
{
  "board": 1,
  "title": "Document API",
  "description": "Finalize backend README",
  "status": "to-do",
  "priority": "high",
  "assignee_id": 2,
  "reviewer_id": 3,
  "due_date": "2026-03-31"
}
```

Notes:

- Allowed `status` values: `to-do`, `in-progress`, `review`, `done`
- Allowed `priority` values: `low`, `medium`, `high`
- `assignee_id` and `reviewer_id` must be board members.

### Update Task Status

Request:

```json
{
  "status": "in-progress"
}
```

Notes:

- Alias values such as `todo` or `to do` are normalized to `to-do`.
- Changing the `board` field via PATCH is not allowed.

## Useful Management Commands

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py test
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

## Current Test Status

`python manage.py test` currently runs without errors, but there are no tests implemented yet (`Found 0 test(s)`).
