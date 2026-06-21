# HealthLink Sierra Leone

A desktop hospital management system built with Python and Tkinter, designed for healthcare facilities in Sierra Leone. It provides patient record management, visit tracking, statistical charts, and PDF report generation — all stored locally in a SQLite database.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Default Login Credentials](#default-login-credentials)
- [User Roles](#user-roles)
- [Application Pages](#application-pages)
- [Database](#database)
- [Optional Dependencies](#optional-dependencies)
- [Project Structure](#project-structure)
- [License](#license)

---

## Features

- Role-based login system (admin, doctor, nurse)
- Full patient CRUD: add, update, delete, and view patient records
- Patient fields: name, gender, date of birth, blood type, status, contact, emergency contact, and allergies
- Visit history tracking per patient (date, doctor, diagnosis, treatment)
- Advanced search and filtering by name, ID, status, gender, blood type, and registration date range
- Paginated patient table (20 records per page)
- Statistical charts: gender distribution, status breakdown, age groups, daily registrations with trend line, and visits per day
- PDF report generation for weekly, monthly, yearly, or custom date ranges
- CSV export of the current patient list
- Light and dark theme support
- Calendar date picker for birth dates and report ranges
- Database reset with sample data (admin only)
- Sample data auto-seeded on first run (30 patients with Sierra Leonean names)

---

## Requirements

- Python 3.8 or higher
- Tkinter (included with most Python installations)

Optional but recommended:

- matplotlib
- numpy
- reportlab

---

## Installation

1. Clone or download this repository.

2. Install the optional packages for charts and PDF reports:

```bash
pip install matplotlib numpy reportlab
```

---

## Running the Application

```bash
python healthlink_final.py
```

The application window will open with a login screen. On the first run, the database is created automatically and populated with 30 sample patient records.

---

## Default Login Credentials

| Username | Password  | Role   |
|----------|-----------|--------|
| admin    | admin123  | Admin  |
| doctor   | doctor123 | Doctor |
| nurse    | nurse123  | Nurse  |

It is strongly recommended to change these credentials before deploying in a real environment.

---

## User Roles

**Admin** — Full access to all pages including Settings, database reset, and theme management.

**Doctor** — Access to Home, Patients, Charts, and Reports.

**Nurse** — Access to Home, Charts, and Reports. Cannot add, edit, or delete patients.

---

## Application Pages

**Home** — Dashboard showing live stats (total patients, active, pending, days active) and a list of recently registered patients. Stats update automatically when patient records change.

**Patients** — Full patient management table with CRUD form, search bar, blood type filter, date range filter, and pagination. Double-click any row to open a detailed view including visit history.

**Charts** — Eight embedded matplotlib charts covering gender, status, age distribution, pie breakdowns, daily registration trend, and visits per day.

**Reports** — Generates a PDF report for a selected time period (weekly, monthly, yearly, or custom range). Reports include a summary table, gender chart, and full patient list.

**Settings** (admin only) — Toggle between light and dark themes, reset the database, and view system information.

---

## Database

The application uses SQLite and stores all data in a file named `healthlink.db` in the same directory as the script. No external database server is required.

Tables:

- `users` — Login accounts and roles
- `patients` — Patient records
- `visits` — Visit history linked to patients

Generated PDF reports are saved in a `reports/` folder created automatically in the working directory.

---

## Optional Dependencies

| Package    | Purpose                         |
|------------|---------------------------------|
| matplotlib | Charts page and PDF chart image |
| numpy      | Trend line calculation on charts |
| reportlab  | PDF report generation           |

If these packages are not installed, the application still runs. The Charts page will show an installation prompt, and the Reports page will warn that reportlab is missing.

---

## Project Structure