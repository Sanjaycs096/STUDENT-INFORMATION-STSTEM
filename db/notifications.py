"""
Notification System
Manages in-app notifications for students and faculty
"""

from datetime import datetime
from db.supabase import get_supabase
from db.rbac import get_user_id, get_user_role

def create_notification(user_id, user_role, notification_type, title, message):
    """
    Create a new notification
    
    Args:
        user_id: User ID to receive notification
        user_role: User role ('student', 'faculty', 'admin')
        notification_type: Type of notification ('attendance_shortage', 'marks_updated', etc.)
        title: Notification title
        message: Notification message
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        notification_data = {
            'user_id': str(user_id),
            'user_role': user_role,
            'type': notification_type,
            'title': title,
            'message': message,
            'is_read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('notifications').insert(notification_data).execute()
        return True
        
    except Exception as e:
        print(f"Error creating notification: {e}")
        return False

def get_user_notifications(user_id=None, unread_only=False, limit=50):
    """
    Get notifications for a user
    
    Args:
        user_id: User ID (auto-detected if not provided)
        unread_only: Only return unread notifications
        limit: Maximum number of notifications to return
    
    Returns:
        List of notifications
    """
    try:
        if not user_id:
            user_id = get_user_id()
        
        if not user_id:
            return []
        
        supabase = get_supabase()
        
        query = supabase.table('notifications').select('*').eq('user_id', user_id)
        
        if unread_only:
            query = query.eq('is_read', False)
        
        query = query.order('created_at', desc=True).limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return []

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        supabase = get_supabase()
        
        supabase.table('notifications').update({
            'is_read': True
        }).eq('id', notification_id).execute()
        
        return True
        
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return False

def mark_all_read(user_id=None):
    """Mark all notifications as read for a user"""
    try:
        if not user_id:
            user_id = get_user_id()
        
        if not user_id:
            return False
        
        supabase = get_supabase()
        
        supabase.table('notifications').update({
            'is_read': True
        }).eq('user_id', user_id).eq('is_read', False).execute()
        
        return True
        
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return False

def get_unread_count(user_id=None):
    """Get count of unread notifications"""
    try:
        if not user_id:
            user_id = get_user_id()
        
        if not user_id:
            return 0
        
        supabase = get_supabase()
        
        result = supabase.table('notifications')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .eq('is_read', False)\
            .execute()
        
        return result.count if hasattr(result, 'count') else len(result.data if result.data else [])
        
    except Exception as e:
        print(f"Error getting unread count: {e}")
        return 0

def delete_notification(notification_id, user_id=None):
    """Delete a notification"""
    try:
        if not user_id:
            user_id = get_user_id()
        
        supabase = get_supabase()
        
        # Ensure user owns this notification
        supabase.table('notifications')\
            .delete()\
            .eq('id', notification_id)\
            .eq('user_id', user_id)\
            .execute()
        
        return True
        
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False

# Specific notification creators

def notify_attendance_shortage(register_number, semester, attendance_percentage):
    """Notify student of attendance shortage"""
    if attendance_percentage >= 75:
        return  # No notification needed
    
    create_notification(
        user_id=register_number,
        user_role='student',
        notification_type='attendance_shortage',
        title='Attendance Alert',
        message=f'Your attendance for Semester {semester} is {attendance_percentage:.1f}%. Minimum required is 75%.'
    )

def notify_marks_updated(register_number, semester, cgpa):
    """Notify student that marks have been updated"""
    create_notification(
        user_id=register_number,
        user_role='student',
        notification_type='marks_updated',
        title='Marks Updated',
        message=f'Your marks for Semester {semester} have been updated. Current CGPA: {cgpa:.2f}'
    )

def notify_profile_changed(register_number, changed_fields):
    """Notify student that their profile was updated"""
    fields_str = ', '.join(changed_fields)
    create_notification(
        user_id=register_number,
        user_role='student',
        notification_type='profile_changed',
        title='Profile Updated',
        message=f'Your profile has been updated. Changed fields: {fields_str}'
    )

def notify_system_message(user_id, user_role, title, message):
    """Send a system notification"""
    create_notification(
        user_id=user_id,
        user_role=user_role,
        notification_type='system',
        title=title,
        message=message
    )

def check_and_notify_attendance_shortages():
    """
    Background task to check all students for attendance shortages
    Should be run periodically (e.g., daily/weekly)
    """
    try:
        supabase = get_supabase()
        
        # Get all attendance records
        attendance_result = supabase.table('attendance').select('*').execute()
        
        if not attendance_result.data:
            return
        
        for record in attendance_result.data:
            register_number = record['register_number']
            
            # Check each semester
            for i in range(1, 9):
                attendance = record.get(f'sem{i}_attendance', 100)
                
                if attendance < 75:
                    # Check if notification was already sent recently
                    existing = supabase.table('notifications')\
                        .select('id')\
                        .eq('user_id', register_number)\
                        .eq('type', 'attendance_shortage')\
                        .gte('created_at', (datetime.utcnow().replace(hour=0, minute=0, second=0)).isoformat())\
                        .execute()
                    
                    # Only send if not already sent today
                    if not existing.data:
                        notify_attendance_shortage(register_number, i, attendance)
        
    except Exception as e:
        print(f"Error checking attendance shortages: {e}")
