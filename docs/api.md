# API Documentation

The StudentDB application uses a hybrid approach of server-rendered HTML forms and asynchronous JSON APIs (mostly structured using the `?action=` query parameter).

## Base Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Landing page |
| `/login.php` | GET, POST | User authentication |
| `/logout.html` | GET | End session |

## Student Endpoints

All student endpoints require a valid student session.

| Endpoint | Method | Action | Description |
|----------|--------|--------|-------------|
| `/student_index.php` | GET | `fetch` | Returns basic student info (`student_name`, `department`, `dob`) |
| `/student_dashboard.php` | GET | `fetch` | Returns complete student profile data |
| `/academic_details.php` | GET | `fetch` | Returns student's academic records |
| `/performance.php` | GET | `fetch` | Returns aggregated academic and attendance data for charts |
| `/change_password.php` | POST | none | Updates the student's password (requires CSRF) |

## Faculty Endpoints

All faculty endpoints require a valid faculty/admin session.

| Endpoint | Method | Action | Description |
|----------|--------|--------|-------------|
| `/admin.php` | POST | none | Creates a new student record (requires CSRF) |
| `/student_list.php` | GET | `fetch` | Returns a list of all students |
| `/view_student.php` | GET | `fetch` | Returns detailed data for a specific student (`?register_number=...`) |
| `/edit.php` | GET | `fetch` | Returns a list of students for selection |
| `/edit.php` | POST | `fetch` | Returns data for a specific student to edit |
| `/edit.php` | POST | `update`| Updates a student record (requires CSRF) |
| `/delete.php` | POST | none | Deletes a student record, confirming with DOB |
| `/attendance.php`| GET | `fetch` | Returns students for a specific department and semester |
| `/attendance.php`| POST | none | Submits attendance records for a batch of students |
| `/marks.php` | GET | `fetch` | Returns students and their current marks |
| `/marks.php` | POST | none | Submits mark updates for a batch of students |

## Security Requirements

### CSRF Protection
All state-changing requests (POST, PUT, DELETE, or action=update) require a CSRF token.
The token can be provided via:
1. `_csrf_token` form field
2. `X-CSRF-Token` HTTP header
3. `_csrf_token` in the JSON payload

### Rate Limiting
Authentication endpoints are protected by an in-memory rate limiter (max 5 failed attempts per IP within a 5-minute window).
