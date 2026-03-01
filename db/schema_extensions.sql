-- Schema Extensions for Enhanced Features
-- Add these tables to your Supabase database

-- 1. Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_role TEXT NOT NULL CHECK (user_role IN ('student', 'faculty', 'admin')),
    action TEXT NOT NULL,
    details JSONB,
    ip_address TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp DESC);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);

-- 2. Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_role TEXT NOT NULL CHECK (user_role IN ('student', 'faculty', 'admin')),
    type TEXT NOT NULL CHECK (type IN ('attendance_shortage', 'marks_updated', 'profile_changed', 'system')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- 3. Roles and Permissions Table
CREATE TABLE IF NOT EXISTS roles_permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    role TEXT NOT NULL UNIQUE CHECK (role IN ('student', 'faculty', 'admin')),
    permissions JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default permissions
INSERT INTO roles_permissions (role, permissions) VALUES
('student', '{
    "can_view_profile": true,
    "can_edit_profile": false,
    "can_view_grades": true,
    "can_view_attendance": true,
    "can_change_password": true,
    "can_download_report": true,
    "can_view_notifications": true
}'::jsonb),
('faculty', '{
    "can_view_profile": true,
    "can_edit_profile": false,
    "can_view_grades": true,
    "can_view_attendance": true,
    "can_change_password": true,
    "can_add_student": true,
    "can_edit_student": true,
    "can_delete_student": false,
    "can_mark_attendance": true,
    "can_update_marks": true,
    "can_view_all_students": true,
    "can_download_student_report": true,
    "can_view_notifications": true
}'::jsonb),
('admin', '{
    "can_view_profile": true,
    "can_edit_profile": true,
    "can_view_grades": true,
    "can_view_attendance": true,
    "can_change_password": true,
    "can_add_student": true,
    "can_edit_student": true,
    "can_delete_student": true,
    "can_mark_attendance": true,
    "can_update_marks": true,
    "can_view_all_students": true,
    "can_upload_documents": true,
    "can_download_student_report": true,
    "can_view_activity_logs": true,
    "can_view_notifications": true,
    "can_manage_faculty": true
}'::jsonb)
ON CONFLICT (role) DO NOTHING;

-- Enable Row Level Security (RLS)
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles_permissions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for activity_logs (admin can see all, users can see their own)
CREATE POLICY "Users can view their own activity logs"
    ON activity_logs FOR SELECT
    USING (user_id = current_setting('request.jwt.claims', true)::json->>'user_id');

CREATE POLICY "Admins can view all activity logs"
    ON activity_logs FOR SELECT
    USING (current_setting('request.jwt.claims', true)::json->>'role' = 'admin');

-- RLS Policies for notifications (users see their own)
CREATE POLICY "Users can view their own notifications"
    ON notifications FOR SELECT
    USING (user_id = current_setting('request.jwt.claims', true)::json->>'user_id');

CREATE POLICY "Users can update their own notifications"
    ON notifications FOR UPDATE
    USING (user_id = current_setting('request.jwt.claims', true)::json->>'user_id');

-- RLS Policies for roles_permissions (everyone can read)
CREATE POLICY "Everyone can view role permissions"
    ON roles_permissions FOR SELECT
    TO public
    USING (true);
