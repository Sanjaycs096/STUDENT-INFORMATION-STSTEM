<div align="center">

# 🎓 Student Information System (StudentDB)

A modern, full-stack Student Information System built with Flask and Supabase.

Manage student records, attendance, academic performance, and faculty operations — all through a clean, responsive web interface.

[🚀 Live Demo](#demo) · [📖 Documentation](#api-documentation) · [💻 Repository](#) · [🐛 Report Bug](#) · [✨ Request Feature](#)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **Hero Screenshot**
> *(Hero screenshot goes here - docs/screenshots/hero.png)*

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Demo](#demo)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security](#security)
- [Performance](#performance)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [Known Limitations](#known-limitations)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)
- [Acknowledgements](#acknowledgements)

---

## Overview

The Student Information System (StudentDB) is a comprehensive web-based platform tailored for educational institutions. It solves the problem of decentralized data management by providing a unified portal where students can track their academic progress and attendance, while faculty can seamlessly manage records, grading, and reports. It was built to streamline administrative workflows and empower students with real-time access to their academic standing.

## Key Features

**🎓 Student Portal**
- **Personal Dashboard:** View & update profile details.
- **Performance Charts:** Visual CGPA trends across all semesters.
- **Attendance Tracker:** Semester-wise attendance percentage.
- **Secure Account:** Change password with strength validation.
- **Notifications:** Real-time alerts for marks & attendance.
- **PDF Reports:** Download full academic report cards.

**👨‍🏫 Faculty Portal**
- **Student Management:** Full registration with document upload, edit and safely delete records.
- **Attendance Management:** Mark present/absent by department & semester.
- **Marks Entry:** CGPA & backlog entry for each semester.
- **Student List:** Searchable, paginated student directory.

## Demo

Live demo is not currently available.

## Screenshots

> **TODO:** Add screenshots to `docs/screenshots/`
> - `login.png`
> - `dashboard.png`
> - `main-feature.png`

## Architecture

The system uses a standard client-server architecture with Flask handling routing, templating, and security, while Supabase provides managed PostgreSQL and Row-Level Security (RLS).

```text
Browser ──► Flask (api/app.py) ──► Supabase (PostgreSQL)
                │
                ├── RBAC + Session Auth
                ├── CSRF Validation
                ├── Input Sanitisation
                └── Jinja2 Templates
```

## Tech Stack

**Frontend:** Vanilla HTML/CSS/JS + Jinja2 templates
**Backend:** Python 3.10, Flask 3.0, Werkzeug 3.0
**Database:** Supabase (PostgreSQL)
**Authentication:** Session-based (Flask sessions + bcrypt)
**Infrastructure/Hosting:** Vercel (serverless Python)
**Testing:** `unittest` module

## Project Structure

```text
StudentDB/
├── api/
│   └── app.py              # Core Flask application logic
├── db/                     # Database utilities & schemas
├── docs/                   # Documentation and API specs
├── static/                 # Static assets (CSS/JS/Images)
├── templates/              # Jinja2 HTML views
├── tests/                  # Unit and integration tests
├── app.py                  # Local dev entry point
├── vercel.json             # Vercel serverless deployment config
└── requirements.txt        # Python dependencies
```

## How It Works

1. Users authenticate via session-based logins.
2. Faculty users get RBAC (Role-Based Access Control) permissions to mutate student records.
3. Students have read-only access (enforced by Supabase RLS and Flask) to their data.
4. The system securely proxies all database queries to Supabase via `httpx`.

## Installation

```bash
git clone https://github.com/your-username/StudentDB.git
cd StudentDB
```
For Windows:
```bat
start.bat
```
For Linux/macOS:
```bash
pip install -r requirements.txt
```

## Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com) project (free tier works)

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-random-secret-key
FLASK_ENV=development
```

## Running Locally

```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000)

## Usage

| Role    | ID / Register No | Password  |
|---------|-----------------|-----------|
| Student | `DEMO001`       | `demo001` |
| Faculty | `admin`         | `123@Admin`|

## API Documentation

For backend route specs and JSON structures, please refer to:
[docs/api.md](docs/api.md)

## Testing

Run the testing suite to validate functionality and structure:
```bash
python -m unittest tests/test_basic.py
```

## Security

- **CSRF Protection** on every form and fetch request.
- **Login Rate Limiting** — 5-attempt lockout per IP.
- **Session Hardening** — HttpOnly, SameSite, 8-hour expiry.
- **Security Headers** — X-Frame-Options, CSP, HSTS, nosniff.
- **Input Sanitisation** — length-limited, stripped on all fields.
- **Password Strength** — enforced minimum strength on change.
- **Supabase RLS** — row-level security policies on all tables.

## Performance

Performance benchmarks are not currently verified. Optimization focuses on lightweight rendering via Jinja2 and HTTP/2 usage via `httpx`.

## Deployment

Deploying via Vercel:
```bash
npm i -g vercel
vercel --prod
```
Set up Environment Variables in the Vercel Dashboard.

## Roadmap

- Add automated Email recovery system.
- Implement comprehensive E2E testing with Playwright.
- Integrate a robust CI/CD pipeline for automated testing and releases.

## Known Limitations

- Real-time features using WebSockets are restricted by Vercel Serverless environment.
- PDF generation may take longer on free-tier serverless functions.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Sanjay Kumar** (2026)

## Acknowledgements

- [Flask Framework](https://flask.palletsprojects.com/)
- [Supabase](https://supabase.com/)
- [ReportLab](https://www.reportlab.com/)
