"""
Activity Logging System
Tracks all important actions in the system for audit trail
"""

from datetime import datetime
from flask import request, session
from db.supabase import get_supabase
from db.rbac import get_user_role, get_user_id
import json

def get_client_ip():
    """Get client IP address from request"""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.environ.get('REMOTE_ADDR', 'unknown')

def log_activity(action, details=None, user_id=None, user_role=None):
    """
    Log an activity to the database
    
    Args:
        action: Action performed (e.g., 'login', 'update_marks', 'delete_student')
        details: Additional details as dictionary
        user_id: User ID (auto-detected if not provided)
        user_role: User role (auto-detected if not provided)
    """
    try:
        supabase = get_supabase()
        
        # Auto-detect user if not provided
        if not user_id:
            user_id = get_user_id()
        if not user_role:
            user_role = get_user_role()
        
        # Skip if no user (shouldn't happen for logged actions)
        if not user_id or not user_role:
            return False
        
        log_entry = {
            'user_id': str(user_id),
            'user_role': user_role,
            'action': action,
            'details': details if details else {},
            'ip_address': get_client_ip(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Insert log entry
        supabase.table('activity_logs').insert(log_entry).execute()
        return True
        
    except Exception as e:
        # Don't let logging errors break the application
        print(f"Error logging activity: {e}")
        return False

def log_login(user_id, user_role, success=True):
    """Log login attempt"""
    log_activity(
        action='login_success' if success else 'login_failed',
        details={'user_id': user_id, 'success': success},
        user_id=user_id,
        user_role=user_role
    )

def log_logout(user_id, user_role):
    """Log logout"""
    log_activity(
        action='logout',
        details={'user_id': user_id},
        user_id=user_id,
        user_role=user_role
    )

def log_attendance_update(register_numbers, semester, date, marked_by):
    """Log attendance marking"""
    log_activity(
        action='mark_attendance',
        details={
            'students_count': len(register_numbers),
            'semester': semester,
            'date': date,
            'marked_by': marked_by
        }
    )

def log_marks_update(register_numbers, semester, updated_by):
    """Log marks/CGPA update"""
    log_activity(
        action='update_marks',
        details={
            'students_count': len(register_numbers),
            'semester': semester,
            'updated_by': updated_by
        }
    )

def log_student_added(register_number, student_name, added_by):
    """Log new student addition"""
    log_activity(
        action='add_student',
        details={
            'register_number': register_number,
            'student_name': student_name,
            'added_by': added_by
        }
    )

def log_student_edited(register_number, fields_updated, edited_by):
    """Log student profile edit"""
    log_activity(
        action='edit_student',
        details={
            'register_number': register_number,
            'fields_updated': fields_updated,
            'edited_by': edited_by
        }
    )

def log_student_deleted(register_number, student_name, deleted_by):
    """Log student deletion"""
    log_activity(
        action='delete_student',
        details={
            'register_number': register_number,
            'student_name': student_name,
            'deleted_by': deleted_by
        }
    )

def log_password_change(user_id, user_role):
    """Log password change"""
    log_activity(
        action='change_password',
        details={'user_id': user_id},
        user_id=user_id,
        user_role=user_role
    )

def log_profile_view(register_number, viewed_by, viewer_role):
    """Log profile viewing"""
    log_activity(
        action='view_student_profile',
        details={
            'register_number': register_number,
            'viewed_by': viewed_by
        },
        user_id=viewed_by,
        user_role=viewer_role
    )

def log_document_upload(register_number, document_type, uploaded_by):
    """Log document upload"""
    log_activity(
        action='upload_document',
        details={
            'register_number': register_number,
            'document_type': document_type,
            'uploaded_by': uploaded_by
        }
    )

def log_report_download(register_number, downloaded_by, downloader_role):
    """Log PDF report download"""
    log_activity(
        action='download_report',
        details={
            'register_number': register_number,
            'downloaded_by': downloaded_by
        },
        user_id=downloaded_by,
        user_role=downloader_role
    )

def get_activity_logs(user_id=None, limit=100, offset=0):
    """
    Retrieve activity logs
    
    Args:
        user_id: Filter by user ID (None for all users - admin only)
        limit: Number of records to retrieve
        offset: Pagination offset
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table('activity_logs').select('*')
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        query = query.order('timestamp', desc=True).limit(limit).offset(offset)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error retrieving activity logs: {e}")
        return []

def get_user_activity_summary(user_id, days=30):
    """Get activity summary for a user"""
    try:
        supabase = get_supabase()
        
        # Calculate date range
        from datetime import timedelta
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        result = supabase.table('activity_logs')\
            .select('action')\
            .eq('user_id', user_id)\
            .gte('timestamp', start_date)\
            .execute()
        
        # Count action types
        summary = {}
        for log in result.data if result.data else []:
            action = log['action']
            summary[action] = summary.get(action, 0) + 1
        
        return summary
        
    except Exception as e:
        print(f"Error getting activity summary: {e}")
        return {}
