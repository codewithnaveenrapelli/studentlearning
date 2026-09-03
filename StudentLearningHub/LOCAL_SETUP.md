# Student Learning Hub: Local Setup

## Prerequisites

- Windows
- Python 3.12 or newer
- PowerShell

## 1. Open the project folder

```powershell
cd D:\studentlearning\StudentLearningHub
```

## 2. Create a virtual environment

Run this once:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
```

If the Python launcher is available, this shorter command also works:

```powershell
py -3.12 -m venv .venv
```

## 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. Start the application

```powershell
.\.venv\Scripts\python.exe app.py
```

Open this address in your browser:

<http://127.0.0.1:5000>

Keep the terminal open while using the application. Press `Ctrl+C` to stop the server.

## 5. Run the tests

Open another PowerShell window in the project folder and run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Registering an administrator account

The registration form creates a student account by default. This prevents anyone from granting themselves administrator access.

1. Start the application and register normally at <http://127.0.0.1:5000/auth>.
2. Close the browser session or log out.
3. In PowerShell, replace the email address in this command and run it:

```powershell
.\.venv\Scripts\python.exe -c "from app import app; from models import db, User; ctx=app.app_context(); ctx.push(); user=User.query.filter_by(email='your-email@example.com').first(); print('FOUND', bool(user)); user.role='admin' if user else None; db.session.commit() if user else None; print('ROLE', user.role if user else 'NOT_FOUND')"
```

4. Log in again. The **Admin** link will appear in the navigation bar.
5. Open <http://127.0.0.1:5000/admin> to view the admin dashboard.

## Resource previews

From a resource's **View Details** page, logged-in users can preview PDFs, images, and text files. Other file types can be downloaded.

## Local files

- SQLite database: `instance/student_learning_hub.db`
- Uploaded files: `static/uploads/`
- Environment settings: `.env`
