# TaskFlow — Task Management & Productivity Dashboard

TaskFlow is a full-stack task management application built with **Python and Django**. It gives authenticated users one workspace to create and organize tasks, track progress, manage deadlines, and review productivity insights.

**Live demo:** https://taskflow-django-t8y8.onrender.com  
**Source code:** https://github.com/zafar12450/taskflow-django

---

## Overview

TaskFlow brings everyday task planning into a focused workspace. Users can manage tasks from a dashboard, move work through a Kanban board, view due dates on a monthly calendar, and monitor progress through analytics.

The application is deployed on Render and uses a Supabase PostgreSQL database in production. SQLite is used for local development by default.

## Features

- **Authentication:** User registration, login, and logout
- **Personal workspaces:** Users can access and manage their own tasks
- **Task management:** Create, view, update, and delete tasks
- **Priorities and statuses:** Organize tasks by priority and workflow status
- **Search and filters:** Find tasks and filter by status or priority
- **Dashboard:** View task totals and status summaries
- **Kanban board:** Visualize workflow stages and update task status with drag-and-drop
- **Monthly calendar:** View tasks by due date
- **Productivity analytics:** Review completion rate, status distribution, priority breakdown, and overdue tasks
- **Account settings:** Update account details and change password
- **Django Admin:** Manage users, groups, and tasks
- **Automated tests:** 51 Django tests passed in the development environment

## Screenshots

The live application includes four key views: Dashboard, Kanban board, Monthly calendar, and Productivity analytics.

To display screenshots directly in this README on GitHub, add image files to `docs/screenshots/` and embed them with relative Markdown image links. This README does not reference screenshot files that are not yet in the repository.

## Technology stack

| Area | Technologies |
|---|---|
| Backend | Python 3.14, Django 6.1 |
| Frontend | HTML, CSS, Django Templates, JavaScript |
| Local database | SQLite |
| Production database | PostgreSQL on Supabase |
| Static files | WhiteNoise |
| Production server | Gunicorn |
| Hosting | Render |
| Version control | Git and GitHub |

## Application architecture

```text
Browser
   |
   v
Render Web Service
Django application (Gunicorn)
   |
   +---- Django authentication and task-management views
   |
   +---- WhiteNoise (static files)
   |
   v
Supabase PostgreSQL (production)

Local development:
Browser -> Django development server -> SQLite
```

The application selects the database using the `DATABASE_URL` environment variable. When it is not set, the local configuration uses SQLite.

## Project structure

```text
task-management/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── tasks/
│   ├── migrations/
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── tests.py
├── manage.py
├── requirements.txt
├── build.sh
├── .env.example
├── .gitignore
└── README.md
```

## Run locally

### 1. Clone the repository

```powershell
git clone https://github.com/zafar12450/taskflow-django.git
cd task-management
```

If the cloned repository directory has a different name on your computer, change into that directory instead.

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Apply migrations

```powershell
python manage.py migrate
```

### 5. Create a local administrator (optional)

```powershell
python manage.py createsuperuser
```

### 6. Run the development server

```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Run tests

```powershell
python manage.py check
python manage.py test tasks
```

**Current test result:** 51 automated tests passed in the development environment. Run the commands above against your own checkout to verify its current state.

## Production deployment

TaskFlow's production setup uses **Render** for the Django web service, **Supabase** for PostgreSQL, and **GitHub** for source control and deployment.

### Render service commands

**Build command**

```bash
./build.sh
```

**Start command**

```bash
gunicorn config.wsgi:application
```

### Required Render environment variables

Set these in the Render service's Environment settings. Do not commit their values to GitHub.

| Variable | Value |
|---|---|
| `DEBUG` | `False` |
| `SECRET_KEY` | A newly generated, private Django secret key |
| `DATABASE_URL` | The Supabase PostgreSQL Session Pooler URI |

The Supabase Session Pooler is used for this deployment because it provides an IPv4 connection path. Keep the database password private. If it contains reserved URL characters, URL-encode those characters in the connection URI.

The project's production settings handle the Render-provided external hostname. A custom domain may require additional host and CSRF-origin configuration.

### Deployment steps

1. Push the project to the GitHub repository.
2. Create a Supabase project and obtain its PostgreSQL Session Pooler URI.
3. Create a Render Web Service connected to the GitHub repository.
4. Select the `main` branch and the Free instance if using the no-monthly-cost setup.
5. Set the build and start commands shown above.
6. Add the required environment variables.
7. Deploy and review the Render logs.
8. Open the live site and verify registration, login, task creation, task updates, calendar, analytics, and data persistence.

The production deployment was live-tested with task creation, editing, status changes, calendar and analytics display, logout/login, and persistence after logging back in.

### Create a production administrator

Render Free instances do not provide the usual interactive Shell workflow. A production superuser was created by running Django's `createsuperuser` command locally while the local process was temporarily configured with the production `DATABASE_URL`.

To create another production administrator, use a secure local terminal, temporarily set the production database connection environment variable, and run:

```powershell
python manage.py createsuperuser
```

Do not paste database credentials into source files, commit them, or share them in screenshots or chat. Remove temporary environment variables from the terminal when finished.

Django admin: https://taskflow-django-t8y8.onrender.com/admin/

## Security and operational notes

- Keep `DEBUG=False` in production.
- Use a unique, strong production `SECRET_KEY`.
- Store database credentials and secrets only in environment variables.
- Never commit `.env` files, database passwords, or production secret keys.
- Use HTTPS for the deployed application.
- The local SQLite database is not automatically copied to the production PostgreSQL database.
- Free hosting tiers have availability limitations: Render services may sleep after inactivity, and Supabase free projects may pause after periods of low activity. The first request after a Render service sleeps can take longer.
- Supabase Free does not provide the same backup guarantees as a paid database plan. Keep independent backups of important production data.

## Project status

- Core Django application: complete
- Automated test suite: 51 tests passed locally
- GitHub repository: published
- Supabase PostgreSQL: connected
- Render deployment: live
- Production workflows: tested
- Django Admin: accessible
- Portfolio presentation: completed

## Author

**Zafar Khan**

Built as a full-stack Django portfolio project to demonstrate backend development, authentication, database integration, deployment, and practical application workflows.
