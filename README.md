<div align="center">

# 🎓 Student Information System
### M. Kumarasamy College of Engineering

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

> A modern, full-stack **Student Information System** built with Flask and Supabase. Manage student records, attendance, academic performance, and faculty operations — all through a clean, responsive web interface.

<br/>

[🚀 Live Demo](#demo) · [⚡ Quick Start](#quick-start) · [📖 Features](#features) · [🏗️ Architecture](#architecture)

---

</div>

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎓 Student Portal
- 📋 **Personal Dashboard** — view & update profile details
- 📊 **Performance Charts** — CGPA trends across all semesters
- 📅 **Attendance Tracker** — semester-wise attendance percentage
- 🔒 **Secure Account** — change password with strength validation
- 🔔 **Notifications** — real-time alerts for marks & attendance
- 📄 **PDF Reports** — download full academic report card

</td>
<td width="50%">

### 👨‍🏫 Faculty Portal
- ➕ **Add Students** — full registration with document upload
- ✏️ **Edit Records** — update any student detail instantly
- 🗑️ **Delete with Verification** — DOB-confirmed safe deletion
- 📋 **Attendance Management** — mark present/absent by dept & semester
- 📈 **Marks Entry** — CGPA & backlog entry for each semester
- 👥 **Student List** — searchable, paginated student directory

</td>
</tr>
</table>

### 🔐 Security Features
- **CSRF Protection** on every form and fetch request
- **Login Rate Limiting** — 5-attempt lockout per IP
- **Session Hardening** — HttpOnly, SameSite, 8-hour expiry
- **Security Headers** — X-Frame-Options, CSP, HSTS, nosniff
- **Input Sanitisation** — length-limited, stripped on all fields
- **Password Strength** — enforced minimum strength on change
- **Supabase RLS** — row-level security policies on all tables

---

## 📸 Screenshots

> **TODO:** Add screenshots of the working dashboard here. Recommended views:
> - Login page
> - Student Dashboard & Charts
> - Faculty Marks/Attendance Entry

---

## 🏗️ Architecture

```
StudentDB/
├── api/
│   └── app.py              # Flask application (all routes + security)
├── db/
│   ├── supabase.py         # Supabase client singleton
│   ├── rbac.py             # Role-based access control
│   ├── activity_logger.py  # Audit logging
│   ├── notifications.py    # In-app notification system
│   ├── pdf_generator.py    # PDF report generation
│   └── schema.sql          # Database schema + RLS policies
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS and static assets
├── app.py                  # Local dev entry point
├── vercel.json             # Vercel serverless config
└── requirements.txt        # Python dependencies
```

```
Browser ──► Flask (api/app.py) ──► Supabase (PostgreSQL)
                │
                ├── RBAC + Session Auth
                ├── CSRF Validation
                ├── Input Sanitisation
                └── Jinja2 Templates
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- A [Supabase](https://supabase.com) project (free tier works)

### 1. Clone & Install

```bash
git clone https://github.com/your-username/StudentDB.git
cd StudentDB
```

Run the included batch file (Windows) — it installs all dependencies automatically:

```bat
start.bat
```

Or install manually:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example env file and fill in your Supabase credentials:

```bash
cp .env.example .env
```

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-random-secret-key
FLASK_ENV=development
```

### 3. Set Up Database

Run `db/schema.sql` in your Supabase **SQL Editor** to create all tables and RLS policies.

### 4. Run Locally

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) 🎉

---

## 🌐 Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Add your environment variables in the Vercel project dashboard under **Settings → Environment Variables**.

---

## 🔑 Demo Credentials

| Role    | ID / Register No | Password  |
|---------|-----------------|-----------|
| Student | `DEMO001`       | `demo001` |
| Faculty | `admin`         | `123@Admin`|

> ⚠️ **Default student password** is the register number in lowercase (e.g. `cs2023001` → password: `cs2023001`). Students should change it on first login.

---

## 🛠️ Tech Stack

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| **Backend**  | Python 3.10, Flask 3.0, Werkzeug 3.0            |
| **Database** | Supabase (PostgreSQL) with Row-Level Security   |
| **Auth**     | Session-based (Flask sessions + bcrypt)         |
| **HTTP**     | httpx 0.27.2 (HTTP/2 enabled)                  |
| **PDF**      | ReportLab 4.0                                   |
| **Hosting**  | Vercel (serverless Python)                      |
| **Frontend** | Vanilla HTML/CSS/JS + Jinja2 templates          |

---

## 📦 Dependencies

```
Flask==3.0.0
Werkzeug==3.0.1
python-dotenv==1.0.0
bcrypt==4.1.2
reportlab==4.0.7
supabase==2.9.1
httpx[http2]==0.27.2
h2==4.1.0
websockets==15.0.1
```

---

## 🗄️ Database Schema

| Table        | Purpose                                    |
|------------- |--------------------------------------------|
| `students`   | Core student records (name, dept, contact) |
| `academic`   | CGPA & backlogs per semester (sem1–sem8)   |
| `attendance` | Attendance % per semester (sem1–sem8)      |
| `faculty`    | Faculty accounts                           |
| `activity_logs` | Audit trail for all operations          |
| `notifications` | In-app notification messages            |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---



<div align="center">

Made with ❤️ for **M. Kumarasamy College of Engineering**

*Empowering students through technology and innovation.*

</div>
