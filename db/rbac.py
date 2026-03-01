"""
Role-Based Access Control (RBAC) Module
Provides middleware and decorators for permission-based access control
"""

from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from db.supabase import get_supabase

# Permission cache to avoid repeated database queries
_permissions_cache = {}

def get_user_role():
    """Get current user's role from session"""
    if 'faculty_id' in session:
        return 'admin' if session.get('faculty_id') == 'admin' else 'faculty'
    elif 'register_number' in session:
        return 'student'
    return None

def get_user_id():
    """Get current user's ID from session"""
    if 'faculty_id' in session:
        return session.get('faculty_id')
    elif 'register_number' in session:
        return session.get('register_number')
    return None

def get_role_permissions(role):
    """Get permissions for a role from database with caching"""
    if role in _permissions_cache:
        return _permissions_cache[role]
    
    try:
        supabase = get_supabase()
        result = supabase.table('roles_permissions').select('permissions').eq('role', role).execute()
        
        if result.data and len(result.data) > 0:
            permissions = result.data[0]['permissions']
            _permissions_cache[role] = permissions
            return permissions
    except:
        pass
    
    # Default permissions if database query fails
    default_permissions = {
        'student': {
            'can_view_profile': True,
            'can_view_grades': True,
            'can_view_attendance': True,
            'can_change_password': True,
            'can_download_report': True,
            'can_view_notifications': True
        },
        'faculty': {
            'can_view_profile': True,
            'can_add_student': True,
            'can_edit_student': True,
            'can_mark_attendance': True,
            'can_update_marks': True,
            'can_view_all_students': True,
            'can_download_student_report': True,
            'can_view_notifications': True
        },
        'admin': {
            'can_view_profile': True,
            'can_add_student': True,
            'can_edit_student': True,
            'can_delete_student': True,
            'can_mark_attendance': True,
            'can_update_marks': True,
            'can_view_all_students': True,
            'can_upload_documents': True,
            'can_download_student_report': True,
            'can_view_activity_logs': True,
            'can_view_notifications': True,
            'can_manage_faculty': True
        }
    }
    
    return default_permissions.get(role, {})

def has_permission(permission):
    """Check if current user has a specific permission"""
    role = get_user_role()
    if not role:
        return False
    
    permissions = get_role_permissions(role)
    return permissions.get(permission, False)

def require_permission(permission, redirect_to='index'):
    """Decorator to require specific permission for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(permission):
                # For API requests, return JSON error
                if request.is_json or request.args.get('action'):
                    return jsonify({
                        'success': False,
                        'error': 'Permission denied',
                        'message': f'You do not have permission to {permission.replace("can_", "").replace("_", " ")}'
                    }), 403
                
                # For page requests, redirect
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(allowed_roles, redirect_to='index'):
    """Decorator to require specific role(s) for a route"""
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_role = get_user_role()
            
            if current_role not in allowed_roles:
                # For API requests, return JSON error
                if request.is_json or request.args.get('action'):
                    return jsonify({
                        'success': False,
                        'error': 'Access denied',
                        'message': f'This feature is only available to {", ".join(allowed_roles)}'
                    }), 403
                
                # For page requests, redirect
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_access(resource_type, resource_id=None):
    """
    Check if user has access to a specific resource
    resource_type: 'student_profile', 'student_data', 'admin_panel', etc.
    resource_id: specific resource identifier (e.g., register_number)
    """
    role = get_user_role()
    user_id = get_user_id()
    
    if not role or not user_id:
        return False
    
    # Admin has access to everything
    if role == 'admin':
        return True
    
    # Faculty has access to most student data
    if role == 'faculty' and resource_type in ['student_profile', 'student_data', 'attendance', 'marks']:
        return True
    
    # Students can only access their own data
    if role == 'student' and resource_type in ['student_profile', 'student_data', 'attendance', 'marks']:
        return resource_id == user_id or resource_id is None
    
    return False

def clear_permissions_cache():
    """Clear the permissions cache (call when permissions are updated)"""
    global _permissions_cache
    _permissions_cache = {}
