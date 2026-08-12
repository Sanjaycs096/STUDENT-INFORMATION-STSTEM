# Architecture Documentation

## Overview
StudentDB is a full-stack web application designed to manage student information, academic records, and attendance. It leverages a serverless Python backend deployed on Vercel, with a Supabase PostgreSQL database for persistent storage.

## Components

### 1. Frontend (Templates & Static)
- **Vanilla HTML/CSS/JS**: Client-side rendering is kept lightweight by utilizing server-side templates with dynamic asynchronous fetching.
- **Jinja2 Templates**: Flask renders the initial HTML structure.
- **Global Styles**: Defined in `static/global-styles.css` for consistent UI components.

### 2. Backend (Flask Application)
- **`api/app.py`**: The main entry point for Vercel serverless functions. It contains all route definitions, request handling, CSRF protection, and rate-limiting logic.
- **Local Entry**: `app.py` allows running the application locally via a WSGI server.

### 3. Database Services (`db/`)
- **`supabase.py`**: Manages the singleton client for Supabase interactions.
- **`rbac.py`**: Handles Role-Based Access Control logic, verifying permissions for different user roles (student vs faculty).
- **`activity_logger.py`**: Provides audit trails for login events, password changes, and record modifications.
- **`notifications.py`**: A system for logging and retrieving in-app notifications (e.g., marks updated, attendance shortage).
- **`pdf_generator.py`**: Utilizes ReportLab to generate academic performance PDFs on the fly.

## Data Flow
1. **Client Request**: The browser sends an HTTP request to Vercel.
2. **Serverless Function**: Vercel routes the request to `api/app.py`.
3. **Authentication/Validation**: The backend verifies session cookies, CSRF tokens, and applies rate limiting.
4. **Database Query**: Flask communicates with the Supabase PostgreSQL database using REST (via the `supabase-py` SDK).
5. **Response**: Flask returns either a rendered Jinja2 HTML template or a JSON response for asynchronous `fetch` calls.

## Deployment Model
The application is designed for serverless execution on Vercel. The `vercel.json` configuration directs all incoming traffic (including PHP-like legacy route names) to the `api/app.py` handler, enabling horizontal scaling without maintaining a persistent server.
