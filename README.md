# TaskFlow — Task Management Dashboard

TaskFlow is a Django-based task management application built as a full-stack portfolio project. It helps authenticated users organize tasks, monitor progress, and manage deadlines through a clean dashboard.

## Features

- User registration, login, and logout
- Account settings and password change
- Create, view, update, and delete tasks
- Task priority and status management
- Search and filtering
- Dashboard statistics
- Kanban board with status updates
- Monthly task calendar
- Productivity analytics and overdue-task tracking
- Per-user task ownership and access protection
- Django admin integration
- Automated Django tests

## Technology

- Python 3.14
- Django 6.1
- SQLite for local development
- PostgreSQL for Render deployment
- HTML, CSS, and Django templates
- WhiteNoise for production static files

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
└── README.md
```

## Run locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd task-management
```

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

### 4. Apply migrations and create an admin user

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run the development server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Run tests

```powershell
python manage.py check
python manage.py test tasks
```

The project currently has 51 automated tests passing in the development environment. Run the commands above after pulling changes to verify your checkout.

## Deployment on Render

The project is prepared for Render using PostgreSQL, environment-based configuration, WhiteNoise, and a build script.

1. Push the project to a GitHub repository.
2. Create a PostgreSQL database in Render.
3. Create a Render Web Service connected to the repository.
4. Set the build command to `./build.sh`.
5. Set the start command to `gunicorn config.wsgi:application`.
6. Add the following environment variables in Render:
   - `DEBUG` = `False`
   - `SECRET_KEY` = generate a new private value in Render
   - `DATABASE_URL` = the database's internal connection string
7. Add your deployed hostname to `ALLOWED_HOSTS` only if you use a custom domain. Render's `RENDER_EXTERNAL_HOSTNAME` is handled automatically by the settings.

After deployment, create a production administrator from the Render Shell:

```bash
python manage.py createsuperuser
```

Do not commit `.env` files, database credentials, or production secret keys.

## Security notes

- `DEBUG` must be disabled in production.
- Production secrets belong in Render environment variables, not source control.
- Use HTTPS for the deployed site.
- Back up the production PostgreSQL database regularly.
- The local SQLite database is not copied to Render automatically. If you need existing local task data in production, plan a separate data migration.

## Project status

Core application features and 51 automated tests are complete. Render deployment configuration and live deployment are the next steps.
