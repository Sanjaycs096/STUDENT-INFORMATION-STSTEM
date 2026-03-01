"""
Flask Application for Vercel Serverless Deployment
Student Information System - Python + Supabase Backend
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from werkzeug.utils import secure_filename
import os
import sys
import httpx
import secrets
import re
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase import get_supabase
from db.rbac import require_permission, require_role, has_permission, get_user_role, get_user_id
from db.activity_logger import (
    log_login, log_logout, log_attendance_update, log_marks_update,
    log_student_added, log_student_edited, log_student_deleted,
    log_password_change, log_report_download, log_document_upload,
    get_activity_logs
)
from db.notifications import (
    get_user_notifications, mark_notification_read, mark_all_read,
    get_unread_count, notify_marks_updated, notify_profile_changed,
    notify_attendance_shortage
)
from db.pdf_generator import generate_student_report

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# ==================== SESSION & SECURITY CONFIGURATION ====================
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV', 'development') == 'production',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_COOKIE_NAME='sis_session',
)

# Get Supabase client
supabase = get_supabase()


# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== SECURITY HELPERS ====================

# --- Rate limiting (in-memory, per IP) ---
_failed_logins: dict = defaultdict(list)
_rate_lock = Lock()
RATE_LIMIT = 5    # max failed attempts before lockout
RATE_WINDOW = 300  # seconds (5 minutes)

def _clean_ip(ip: str) -> str:
    """Normalise proxy-forwarded IP to first address."""
    return (ip or 'unknown').split(',')[0].strip()

def is_rate_limited(ip: str) -> bool:
    """Return True if this IP has exceeded the failed-login threshold."""
    ip = _clean_ip(ip)
    with _rate_lock:
        cutoff = datetime.utcnow() - timedelta(seconds=RATE_WINDOW)
        _failed_logins[ip] = [t for t in _failed_logins[ip] if t > cutoff]
        return len(_failed_logins[ip]) >= RATE_LIMIT

def record_failed_login(ip: str) -> None:
    with _rate_lock:
        _failed_logins[_clean_ip(ip)].append(datetime.utcnow())

def clear_failed_logins(ip: str) -> None:
    with _rate_lock:
        _failed_logins[_clean_ip(ip)] = []

# --- CSRF protection ---
def csrf_token() -> str:
    """Return (creating if absent) a per-session CSRF token."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf() -> bool:
    """Validate CSRF token from X-CSRF-Token header, form field, or JSON body."""
    server_token = session.get('_csrf_token', '')
    if not server_token:
        return False
    client_token = (
        request.headers.get('X-CSRF-Token')
        or request.form.get('_csrf_token')
    )
    if not client_token and request.is_json:
        data = request.get_json(silent=True) or {}
        client_token = data.get('_csrf_token', '')
    return bool(client_token) and secrets.compare_digest(server_token, str(client_token))

# Register as a Jinja2 global so {{ csrf_token() }} works in every template
app.jinja_env.globals['csrf_token'] = csrf_token

# --- Input sanitisation ---
def _s(value, max_len: int = 200) -> str:
    """Strip, truncate, and return as str; returns '' for None/falsy."""
    return str(value or '').strip()[:max_len]

def _validate_password_strength(pwd: str) -> tuple:
    """Return (ok: bool, message: str) for a candidate password."""
    if len(pwd) < 6:
        return False, 'Password must be at least 6 characters.'
    if len(pwd) > 128:
        return False, 'Password too long (max 128 characters).'
    return True, ''

# --- Security response headers ---
@app.after_request
def add_security_headers(response):
    """Attach security headers to every response."""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers.pop('Server', None)
    return response


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
@app.route('/index.php')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/login.php', methods=['GET', 'POST'])
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    """Handle student and faculty login"""
    if request.method == 'POST':
        # --- Rate limiting ---
        client_ip = _clean_ip(
            request.environ.get('HTTP_X_FORWARDED_FOR', '') or
            request.environ.get('REMOTE_ADDR', 'unknown')
        )
        if is_rate_limited(client_ip):
            flash('Too many failed login attempts. Please wait 5 minutes and try again.', 'error')
            return render_template('login.html')

        user_type = _s(request.form.get('userType'), 20)
        register_number = _s(request.form.get('registerNumber', ''), 50)
        password = _s(request.form.get('password', ''), 128)

        if user_type == 'student':
            # Demo student bypass (no database required)
            if register_number.upper() == 'DEMO001' and password == 'demo001':
                session.clear()
                session.permanent = True
                session['student'] = {
                    'register_number': 'DEMO001',
                    'student_name': 'Demo Student',
                    'department': 'Computer Science'
                }
                session['register_number'] = 'DEMO001'
                clear_failed_logins(client_ip)
                log_login('DEMO001', 'student', success=True)
                return redirect(url_for('student_index'))

            # Student login
            result = supabase.table('students').select('*').ilike('register_number', register_number).execute()
            
            if result.data and len(result.data) > 0:
                student = result.data[0]
                
                # Default password is lowercase register_number if no custom password set
                default_password = student['register_number'].lower()
                actual_password = student.get('current_password') or default_password
                
                if password == actual_password:
                    session.clear()
                    session.permanent = True
                    session['student'] = {
                        'register_number': student['register_number'],
                        'student_name': student['student_name'],
                        'department': student['department']
                    }
                    session['register_number'] = student['register_number']
                    clear_failed_logins(client_ip)
                    # Log successful login
                    log_login(student['register_number'], 'student', success=True)
                    return redirect(url_for('student_index'))
                else:
                    record_failed_login(client_ip)
                    flash('Invalid Student Password!', 'error')
                return render_template('login.html')
            else:
                record_failed_login(client_ip)
                flash('Student not found!', 'error')
                return render_template('login.html')
        
        elif user_type == 'faculty':
            # Default admin login
            if register_number.lower() == 'admin' and password == '123@Admin':
                session.clear()
                session.permanent = True
                session['faculty'] = {
                    'faculty_id': 'admin',
                    'name': 'Admin'
                }
                session['faculty_id'] = 'admin'
                clear_failed_logins(client_ip)
                # Log admin login
                log_login('admin', 'admin', success=True)
                return redirect(url_for('admin'))
            
            # Regular faculty login
            result = supabase.table('faculty').select('*').ilike('faculty_id', register_number).execute()
            
            if result.data and len(result.data) > 0:
                faculty = result.data[0]
                
                # Default password is lowercase faculty_id if no custom password set
                default_password = faculty['faculty_id'].lower()
                actual_password = faculty.get('password') or default_password
                
                if password == actual_password:
                    session.clear()
                    session.permanent = True
                    session['faculty'] = {
                        'faculty_id': faculty['faculty_id'],
                        'name': faculty.get('name', 'Faculty')
                    }
                    session['faculty_id'] = faculty['faculty_id']
                    clear_failed_logins(client_ip)
                    return redirect(url_for('faculty_dashboard'))
                else:
                    record_failed_login(client_ip)
                    flash('Invalid Faculty Credentials!', 'error')
                    return render_template('login.html')
            else:
                record_failed_login(client_ip)
                flash('Faculty not found!', 'error')
                return render_template('login.html')
    
    return render_template('login.html')


@app.route('/logout.html')
def logout():
    """Handle logout"""
    # Log logout before clearing session
    user_id = get_user_id()
    user_role = get_user_role()
    if user_id and user_role:
        log_logout(user_id, user_role)
    
    session.clear()
    return redirect(url_for('login'))


@app.route('/change_password.php', methods=['GET', 'POST'])
@app.route('/change_password.html', methods=['GET', 'POST'])
def change_password():
    """Handle password change"""
    if 'register_number' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # CSRF validation
        if not validate_csrf():
            return jsonify({'success': False, 'message': 'Invalid security token. Refresh and try again.'}), 403

        # Check if it's a JSON request (from fetch API)
        if request.is_json:
            data = request.get_json() or {}
            current_password = _s(data.get('current_password'), 128)
            new_password = _s(data.get('new_password'), 128)
        else:
            current_password = _s(request.form.get('current_password'), 128)
            new_password = _s(request.form.get('new_password'), 128)

        # Password strength check
        ok, msg = _validate_password_strength(new_password)
        if not ok:
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'error')
            return render_template('change_password.html')

        register_number = session['register_number']

        result = supabase.table('students').select('*').eq('register_number', register_number).execute()

        if result.data and len(result.data) > 0:
            student = result.data[0]
            default_password = student['register_number'].lower()
            actual_password = student.get('current_password') or default_password

            if current_password == actual_password:
                supabase.table('students').update({
                    'current_password': new_password
                }).eq('register_number', register_number).execute()

                # Log password change
                log_password_change(register_number, 'student')

                # Return JSON for fetch API
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Password changed successfully'})
                return redirect(url_for('student_index'))
            else:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Current password is incorrect'})
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Student not found'})
    
    return render_template('change_password.html')


# ==================== STUDENT DASHBOARD ROUTES ====================

@app.route('/student_index.php')
@app.route('/student_index.html')
def student_index():
    """Student dashboard"""
    if 'register_number' not in session:
        return redirect(url_for('login'))
    
    # Handle API fetch requests
    if request.args.get('action') == 'fetch':
        register_number = session['register_number']
        result = supabase.table('students').select('student_name', 'department', 'dob').eq('register_number', register_number).execute()
        student = result.data[0] if result.data else None
        return jsonify({'student': student})
    
    return render_template('student_index.html')


@app.route('/student_dashboard.php')
@app.route('/student_dashboard.html')
def student_dashboard():
    """Student personal details page"""
    if 'register_number' not in session:
        return redirect(url_for('login'))
    
    register_number = session['register_number']
    
    # API endpoint for fetch request
    if request.args.get('action') == 'fetch':
        result = supabase.table('students').select('*').eq('register_number', register_number).execute()
        student = result.data[0] if result.data else None
        return jsonify({'student': student, 'register_number': register_number})
    
    return render_template('student_dashboard.html')


@app.route('/academic_details.php')
@app.route('/academic_details.html')
def academic_details():
    """Student academic details page"""
    if 'register_number' not in session:
        return redirect(url_for('login'))
    
    register_number = session['register_number']
    
    # API endpoint for fetch request
    if request.args.get('action') == 'fetch':
        result = supabase.table('academic').select('*').eq('register_number', register_number).execute()
        academic = result.data[0] if result.data else None
        return jsonify({'academic': academic})
    
    return render_template('academic_details.html')


@app.route('/performance.php')
@app.route('/performance.html')
def performance():
    """Student performance page"""
    if 'register_number' not in session:
        return redirect(url_for('login'))
    
    register_number = session['register_number']
    
    # API endpoint for fetch request
    if request.args.get('action') == 'fetch':
        academic_result = supabase.table('academic').select('*').eq('register_number', register_number).execute()
        attendance_result = supabase.table('attendance').select('*').eq('register_number', register_number).execute()
        
        academic = academic_result.data[0] if academic_result.data else None
        attendance_data = attendance_result.data[0] if attendance_result.data else None
        
        # Extract attendance percentages for 8 semesters
        attendance_array = []
        if attendance_data:
            for i in range(1, 9):
                attendance_array.append(attendance_data.get(f'sem{i}_attendance', 100))
        else:
            attendance_array = [100] * 8
        
        return jsonify({'academic': academic, 'attendance': attendance_array})
    
    return render_template('performance.html')


# ==================== ADMIN ROUTES ====================

@app.route('/admin.php', methods=['GET', 'POST'])
@app.route('/admin.html', methods=['GET', 'POST'])
def admin():
    """Admin dashboard - Add new student"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # CSRF validation
        if not validate_csrf():
            flash('Invalid security token. Please refresh the page and try again.', 'error')
            return render_template('admin.html'), 403

        # Extract form data
        student_data = {
            'student_name': _s(request.form.get('student_name'), 100),
            'register_number': _s(request.form.get('register_number'), 20).upper(),
            'dob': _s(request.form.get('dob'), 20),
            'gender': _s(request.form.get('gender'), 10),
            'blood_group': _s(request.form.get('blood_group'), 5),
            'department': _s(request.form.get('department'), 100),
            'father_name': _s(request.form.get('father_name'), 100),
            'mother_name': _s(request.form.get('mother_name'), 100),
            'student_phone': _s(request.form.get('student_phone'), 15),
            'parent_phone': _s(request.form.get('parent_phone'), 15),
            'gmail_id': _s(request.form.get('gmail_id'), 100),
            'address': _s(request.form.get('address'), 500),
            'password': '',
            'current_password': ''
        }
        
        # Insert student
        result = supabase.table('students').insert(student_data).execute()
        
        if result.data:
            reg_no = student_data['register_number']
            
            # Initialize attendance record
            attendance_data = {'register_number': reg_no}
            for i in range(1, 9):
                attendance_data[f'sem{i}_attendance'] = 100
            supabase.table('attendance').insert(attendance_data).execute()
            
            # Initialize academic record
            academic_data = {'register_number': reg_no}
            for i in range(1, 9):
                academic_data[f'sem{i}_cgpa'] = 0.0
                academic_data[f'sem{i}_backlogs'] = 0
            supabase.table('academic').insert(academic_data).execute()
            
            # Log student addition
            log_student_added(reg_no, student_data['student_name'], get_user_id())
    
    return render_template('admin.html')


@app.route('/student_list.php')
@app.route('/student_list.html')
def student_list():
    """View all students"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    # Handle API fetch requests
    if request.args.get('action') == 'fetch':
        try:
            result = supabase.table('students').select('register_number', 'student_name', 'department').order('register_number').execute()
            students = result.data if result.data else []
            return jsonify({'students': students})
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            return jsonify({'error': f'Database error: {e}', 'students': []}), 503
    
    return render_template('student_list.html')


@app.route('/view_student.php')
@app.route('/view_student.html')
def view_student():
    """View individual student details"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    # API endpoint for fetch request
    if request.args.get('action') == 'fetch':
        reg_no = request.args.get('register_number')
        if not reg_no:
            return jsonify({'error': 'No register number provided'}), 400
        
        try:
            student_result = supabase.table('students').select('*').eq('register_number', reg_no).execute()
            academic_result = supabase.table('academic').select('*').eq('register_number', reg_no).execute()
            attendance_result = supabase.table('attendance').select('*').eq('register_number', reg_no).execute()
            
            student = student_result.data[0] if student_result.data else None
            if not student:
                return jsonify({'error': 'Student not found'}), 404
            
            academic = academic_result.data[0] if academic_result.data else None
            attendance = attendance_result.data[0] if attendance_result.data else None
            
            return jsonify({
                'student': student,
                'academic': academic,
                'attendance': attendance
            })
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            return jsonify({'error': f'Database error: {e}'}), 503
    
    return render_template('view_student.html')

@app.route('/edit.php', methods=['GET', 'POST'])
@app.route('/edit.html', methods=['GET', 'POST'])
def edit_student():
    """Edit student details"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    # Handle GET fetch for student list
    if request.method == 'GET' and request.args.get('action') == 'fetch':
        try:
            result = supabase.table('students').select('register_number').order('register_number').execute()
            students = result.data if result.data else []
            return jsonify({'students': students})
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            return jsonify({'error': f'Database error: {e}', 'students': []}), 503
    
    if request.method == 'POST':
        # CSRF validation for state-changing (update) actions only
        if request.form.get('action') == 'update' and not validate_csrf():
            return jsonify({'error': 'Invalid security token. Refresh and try again.'}), 403

        register_number = _s(request.form.get('register_number'), 20)

        if request.form.get('action') == 'fetch':
            # Fetch student for editing
            try:
                result = supabase.table('students').select('*').eq('register_number', register_number).execute()
                if result.data:
                    student = result.data[0]
                    if 'id' in student:
                        student['_id'] = str(student['id'])
                        del student['id']
                    return jsonify(student)
                else:
                    return jsonify({'error': 'Student not found'}), 404
            except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
                return jsonify({'error': f'Database error: {e}'}), 503
        
        elif request.form.get('action') == 'update':
            # Update student
            update_data = {
                'student_name': _s(request.form.get('student_name'), 100),
                'dob': _s(request.form.get('dob'), 20),
                'gender': _s(request.form.get('gender'), 10),
                'blood_group': _s(request.form.get('blood_group'), 5),
                'department': _s(request.form.get('department'), 100),
                'father_name': _s(request.form.get('father_name'), 100),
                'mother_name': _s(request.form.get('mother_name'), 100),
                'student_phone': _s(request.form.get('student_phone'), 15),
                'parent_phone': _s(request.form.get('parent_phone'), 15),
                'gmail_id': _s(request.form.get('gmail_id'), 100),
                'address': _s(request.form.get('address'), 500)
            }
            
            try:
                result = supabase.table('students').update(update_data).eq('register_number', register_number).execute()
            except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
                return jsonify({'error': f'Database error: {e}'}), 503
            
            if result.data:
                # Log student edit
                changed_fields = list(update_data.keys())
                log_student_edited(register_number, changed_fields, get_user_id())
                
                # Notify student of profile change
                notify_profile_changed(register_number, changed_fields)
                
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Update failed'}), 400
    
    return render_template('edit.html')


@app.route('/delete.php', methods=['GET', 'POST'])
@app.route('/delete.html', methods=['GET', 'POST'])
def delete_student():
    """Delete student"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # CSRF validation
        if not validate_csrf():
            return jsonify({'success': False, 'message': 'Invalid security token. Refresh and try again.'}), 403

        register_number = _s(request.form.get('register_number'), 20)
        dob = _s(request.form.get('dob'), 20)

        try:
            # Validate student exists and DOB matches
            result = supabase.table('students').select('*').eq('register_number', register_number).execute()
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            return jsonify({'success': False, 'message': f'Database error: {e}'}), 503
        
        if result.data:
            student = result.data[0]
            # Format DOB from student (assuming YYYY-MM-DD) to YYYYMMDD for comparison
            student_dob = student['dob'].replace('-', '')
            
            if student_dob == dob:
                # Log deletion before deleting
                log_student_deleted(register_number, student.get('student_name', 'Unknown'), get_user_id())
                
                # Delete student (cascade will handle related records)
                supabase.table('students').delete().eq('register_number', register_number).execute()
                return jsonify({'success': True, 'message': 'Student deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Invalid DOB. Student not deleted.'}), 400
        else:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    return render_template('delete.html')


@app.route('/attendance.php', methods=['GET', 'POST'])
@app.route('/attendance.html', methods=['GET', 'POST'])
def attendance():
    """Manage student attendance"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    # Handle GET fetch for students
    if request.method == 'GET' and request.args.get('action') == 'fetch':
        department = request.args.get('department')
        semester = request.args.get('semester')
        
        if department and semester:
            try:
                students_result = supabase.table('students').select('register_number', 'student_name').eq('department', department).execute()
                students = students_result.data if students_result.data else []
                return jsonify({'students': students})
            except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
                return jsonify({'error': f'Database error: {e}', 'students': []}), 503
    
    if request.method == 'POST':
        # CSRF validation (token sent as X-CSRF-Token header by JS)
        if not validate_csrf():
            return jsonify({'success': False, 'message': 'Invalid security token. Refresh and try again.'}), 403

        data = request.get_json() or {}
        attendance_date = _s(data.get('date'), 20)
        semester = int(data.get('semester', 1))
        attendance_records = data.get('attendance', [])
        column = f'sem{semester}_attendance'
        
        # Process attendance for each student
        for record in attendance_records:
            reg_no = record['register_number']
            status = record['status']
            
            # Get current attendance
            att_result = supabase.table('attendance').select('*').eq('register_number', reg_no).execute()
            
            if att_result.data:
                att_record = att_result.data[0]
                current_percentage = att_record.get(column, 100)
                
                if status == 'absent':
                    new_percentage = max(0, current_percentage - 2)
                else:
                    new_percentage = current_percentage
                
                supabase.table('attendance').update({
                    column: new_percentage
                }).eq('register_number', reg_no).execute()
                
                # Notify if attendance is low
                if new_percentage < 75:
                    notify_attendance_shortage(reg_no, semester, new_percentage)
            else:
                # Create new attendance record
                new_percentage = 98 if status == 'absent' else 100
                att_data = {'register_number': reg_no}
                for i in range(1, 9):
                    att_data[f'sem{i}_attendance'] = 100 if i != semester else new_percentage
                supabase.table('attendance').insert(att_data).execute()
        
        # Log attendance update
        register_numbers = [r['register_number'] for r in attendance_records]
        log_attendance_update(register_numbers, semester, attendance_date, get_user_id())
        
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    
    return render_template('attendance.html')


@app.route('/marks.php', methods=['GET', 'POST'])
@app.route('/marks.html', methods=['GET', 'POST'])
def marks():
    """Manage student marks/grades"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    # Handle GET fetch for students with marks
    if request.method == 'GET' and request.args.get('action') == 'fetch':
        department = request.args.get('department')
        semester = request.args.get('semester')
        
        if department and semester:
            try:
                # Get students from department
                students_result = supabase.table('students').select('register_number', 'student_name').eq('department', department).execute()
                students = students_result.data if students_result.data else []
                
                # Get existing academic data
                academic_result = supabase.table('academic').select('*').execute()
                academic_data = {a['register_number']: a for a in academic_result.data} if academic_result.data else {}
                
                # Combine data
                for student in students:
                    reg_no = student['register_number']
                    if reg_no in academic_data:
                        student['cgpa'] = academic_data[reg_no].get(f'sem{semester}_cgpa', '')
                        student['backlogs'] = academic_data[reg_no].get(f'sem{semester}_backlogs', 0)
                    else:
                        student['cgpa'] = ''
                        student['backlogs'] = 0
                
                return jsonify({'students': students})
            except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
                return jsonify({'error': f'Database error: {e}', 'students': []}), 503
    
    if request.method == 'POST':
        # CSRF validation (token sent as X-CSRF-Token header by JS)
        if not validate_csrf():
            return jsonify({'success': False, 'message': 'Invalid security token. Refresh and try again.'}), 403

        data = request.get_json() or {}
        semester = int(data.get('semester', 1))
        marks_data = data.get('marks', [])
        
        for record in marks_data:
            register_number = record['register_number']
            cgpa = float(record['cgpa'])
            backlogs = int(record['backlogs'])
            
            update_data = {
                f'sem{semester}_cgpa': cgpa,
                f'sem{semester}_backlogs': backlogs
            }
            
            # Check if record exists
            result = supabase.table('academic').select('*').eq('register_number', register_number).execute()
            
            if result.data:
                # Update existing
                supabase.table('academic').update(update_data).eq('register_number', register_number).execute()
            else:
                # Insert new
                update_data['register_number'] = register_number
                supabase.table('academic').insert(update_data).execute()
            
            # Notify student of marks update
            notify_marks_updated(register_number, semester, cgpa)
        
        # Log marks update
        register_numbers = [r['register_number'] for r in marks_data]
        log_marks_update(register_numbers, semester, get_user_id())
        
        return jsonify({'success': True, 'message': 'Marks updated successfully'})
    
    return render_template('marks.html')


@app.route('/faculty_dashboard.html')
def faculty_dashboard():
    """Faculty dashboard"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('faculty_dashboard.php')


@app.route('/faculty.html')
def faculty():
    """Faculty page"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('faculty.php')


@app.route('/proof.html', methods=['GET', 'POST'])
def proof():
    """Upload student documents/proof"""
    if 'faculty_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        register_number = request.form.get('register_number')
        aadhar_number = request.form.get('aadhar_number')
        
        # Handle file uploads
        files_data = {}
        
        for field_name in ['tenth_marksheet', 'twelfth_marksheet', 'transfer_certificate']:
            if field_name in request.files:
                file = request.files[field_name]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # In production, upload to Supabase Storage
                    # For now, store filename
                    files_data[field_name] = filename
        
        # Save document record
        doc_data = {
            'register_number': register_number,
            'aadhar_number': aadhar_number,
            **files_data
        }
        
        # Check if record exists
        result = supabase.table('student_documents').select('*').eq('register_number', register_number).execute()
        
        if result.data:
            supabase.table('student_documents').update(doc_data).eq('register_number', register_number).execute()
        else:
            supabase.table('student_documents').insert(doc_data).execute()
        
        # Log document upload
        if files_data:
            log_document_upload(register_number, ', '.join(files_data.keys()), get_user_id())
    
    return render_template('proof.php')


# ==================== NEW FEATURES: PAGES ====================

@app.route('/notifications.php')
@app.route('/notifications.html')
def notifications_page():
    """Notifications page for students and faculty"""
    if not get_user_id():
        return redirect(url_for('login'))
    return render_template('notifications.html')


# ==================== NEW FEATURES: API ENDPOINTS ====================

# Notifications API
@app.route('/api/notifications', methods=['GET'])
def api_get_notifications():
    """Get notifications for current user"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 50))
    
    notifications = get_user_notifications(user_id, unread_only, limit)
    unread_count = get_unread_count(user_id)
    
    return jsonify({
        'success': True,
        'notifications': notifications,
        'unread_count': unread_count
    })

@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
def api_mark_notification_read(notification_id):
    """Mark a notification as read"""
    if not get_user_id():
        return jsonify({'error': 'Not authenticated'}), 401
    
    success = mark_notification_read(notification_id)
    return jsonify({'success': success})

@app.route('/api/notifications/mark-all-read', methods=['POST'])
def api_mark_all_notifications_read():
    """Mark all notifications as read"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    success = mark_all_read(user_id)
    return jsonify({'success': success})

# Activity Logs API (Admin only)
@app.route('/api/activity-logs', methods=['GET'])
@require_role('admin')
def api_get_activity_logs():
    """Get activity logs (admin only)"""
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    logs = get_activity_logs(user_id, limit, offset)
    
    return jsonify({
        'success': True,
        'logs': logs,
        'count': len(logs)
    })

# PDF Report Generation
@app.route('/api/download-report/<register_number>', methods=['GET'])
def api_download_report(register_number):
    """Generate and download student progress report"""
    user_role = get_user_role()
    user_id = get_user_id()
    
    # Students can only download their own report
    if user_role == 'student' and register_number != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Faculty and admin can download any student's report
    if user_role not in ['student', 'faculty', 'admin']:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Generate PDF
    pdf_buffer = generate_student_report(register_number)
    
    if not pdf_buffer:
        return jsonify({'error': 'Student not found or error generating report'}), 404
    
    # Log the download
    log_report_download(register_number, user_id, user_role)
    
    # Send PDF file
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Student_Report_{register_number}.pdf'
    )

# Permission Check API
@app.route('/api/check-permission/<permission>', methods=['GET'])
def api_check_permission(permission):
    """Check if current user has a specific permission"""
    if not get_user_id():
        return jsonify({'has_permission': False, 'error': 'Not authenticated'}), 401
    
    has_perm = has_permission(permission)
    return jsonify({'has_permission': has_perm, 'permission': permission})

# User Role API
@app.route('/api/user-role', methods=['GET'])
def api_get_user_role():
    """Get current user's role"""
    role = get_user_role()
    user_id = get_user_id()
    
    if not role or not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'role': role,
        'user_id': user_id
    })


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if _is_api_request():
        return jsonify({'error': 'Not found'}), 404
    return render_template('error.html',
        code=404,
        title='Page Not Found',
        message='The page you are looking for doesn\'t exist or has been moved. Check the URL and try again.',
        icon='fas fa-search',
        icon_color='#6c63ff',
        gradient_a='#6c63ff',
        gradient_b='#00cfff'
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    if _is_api_request():
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html',
        code=500,
        title='Server Error',
        message='Something went wrong on our end. Please try again in a moment or contact the administrator.',
        icon='fas fa-triangle-exclamation',
        icon_color='#ff5fa0',
        gradient_a='#ff5fa0',
        gradient_b='#ffd166'
    ), 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    if _is_api_request():
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('error.html',
        code=403,
        title='Access Denied',
        message='You don\'t have permission to access this page. Please log in with an appropriate account.',
        icon='fas fa-lock',
        icon_color='#ffd166',
        gradient_a='#ffd166',
        gradient_b='#ff5fa0'
    ), 403


def _is_api_request() -> bool:
    """Detect if the request expects a JSON response."""
    return bool(
        request.args.get('action') == 'fetch'
        or request.is_json
        or request.path.startswith('/api/')
        or (request.method == 'POST' and request.content_type and 'json' in request.content_type)
    )


@app.errorhandler(httpx.ConnectError)
def handle_connect_error(error):
    """Handle Supabase / network connection failures"""
    msg = ('Cannot connect to the database. '
           'Check your SUPABASE_URL in .env and your internet connection.')
    if _is_api_request():
        return jsonify({'error': msg, 'connection_failed': True}), 503
    flash(msg, 'error')
    return redirect(url_for('login'))


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Catch-all for unhandled exceptions — return JSON for API, HTML for pages."""
    err_str = str(error)
    # Re-surface connection errors through the dedicated handler
    if 'getaddrinfo' in err_str or 'ConnectError' in err_str or 'connection' in err_str.lower():
        return handle_connect_error(error)
    app.logger.exception('Unhandled exception: %s', error)
    if _is_api_request():
        return jsonify({'error': 'An unexpected server error occurred. Please try again.'}), 500
    # Never expose raw exception details to the browser
    return render_template('error.html',
        code=500,
        title='Server Error',
        message='An unexpected error occurred. Please try again or contact the administrator.',
        icon='fas fa-triangle-exclamation',
        icon_color='#ff5fa0',
        gradient_a='#ff5fa0',
        gradient_b='#ffd166'
    ), 500


# For Vercel serverless
if __name__ != '__main__':
    # This is the entry point for Vercel
    application = app
