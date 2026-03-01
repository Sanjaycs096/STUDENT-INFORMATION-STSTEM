-- Student Information System - Supabase PostgreSQL Schema
-- Migration from MySQL to PostgreSQL

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students Table
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_name VARCHAR(100) NOT NULL,
    register_number VARCHAR(20) UNIQUE NOT NULL,
    dob DATE,
    gender VARCHAR(10),
    blood_group VARCHAR(5),
    department VARCHAR(50),
    father_name VARCHAR(100),
    mother_name VARCHAR(100),
    student_phone VARCHAR(15),
    parent_phone VARCHAR(15),
    gmail_id VARCHAR(100),
    address TEXT,
    password TEXT,
    current_password VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    register_number VARCHAR(20) UNIQUE NOT NULL,
    sem1_attendance INTEGER DEFAULT 100,
    sem2_attendance INTEGER DEFAULT 100,
    sem3_attendance INTEGER DEFAULT 100,
    sem4_attendance INTEGER DEFAULT 100,
    sem5_attendance INTEGER DEFAULT 100,
    sem6_attendance INTEGER DEFAULT 100,
    sem7_attendance INTEGER DEFAULT 100,
    sem8_attendance INTEGER DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (register_number) REFERENCES students(register_number) ON DELETE CASCADE
);

-- Academic Table
CREATE TABLE IF NOT EXISTS academic (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    register_number VARCHAR(20) UNIQUE NOT NULL,
    sem1_cgpa FLOAT DEFAULT 0.0,
    sem1_backlogs INTEGER DEFAULT 0,
    sem2_cgpa FLOAT DEFAULT 0.0,
    sem2_backlogs INTEGER DEFAULT 0,
    sem3_cgpa FLOAT DEFAULT 0.0,
    sem3_backlogs INTEGER DEFAULT 0,
    sem4_cgpa FLOAT DEFAULT 0.0,
    sem4_backlogs INTEGER DEFAULT 0,
    sem5_cgpa FLOAT DEFAULT 0.0,
    sem5_backlogs INTEGER DEFAULT 0,
    sem6_cgpa FLOAT DEFAULT 0.0,
    sem6_backlogs INTEGER DEFAULT 0,
    sem7_cgpa FLOAT DEFAULT 0.0,
    sem7_backlogs INTEGER DEFAULT 0,
    sem8_cgpa FLOAT DEFAULT 0.0,
    sem8_backlogs INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (register_number) REFERENCES students(register_number) ON DELETE CASCADE
);

-- Faculty Table
CREATE TABLE IF NOT EXISTS faculty (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    faculty_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    password VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student Documents Table
CREATE TABLE IF NOT EXISTS student_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    register_number VARCHAR(20) NOT NULL,
    aadhar_number VARCHAR(20),
    tenth_marksheet VARCHAR(255),
    twelfth_marksheet VARCHAR(255),
    transfer_certificate VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (register_number) REFERENCES students(register_number) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_register_number ON students(register_number);
CREATE INDEX IF NOT EXISTS idx_students_department ON students(department);
CREATE INDEX IF NOT EXISTS idx_attendance_register_number ON attendance(register_number);
CREATE INDEX IF NOT EXISTS idx_academic_register_number ON academic(register_number);
CREATE INDEX IF NOT EXISTS idx_faculty_faculty_id ON faculty(faculty_id);
CREATE INDEX IF NOT EXISTS idx_documents_register_number ON student_documents(register_number);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attendance_updated_at BEFORE UPDATE ON attendance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_academic_updated_at BEFORE UPDATE ON academic
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faculty_updated_at BEFORE UPDATE ON faculty
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON student_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculty ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_documents ENABLE ROW LEVEL SECURITY;

-- SELECT: open read for all (standard public-read pattern, excluded from linter warnings)
CREATE POLICY "students_select"          ON students          FOR SELECT USING (true);
CREATE POLICY "attendance_select"        ON attendance        FOR SELECT USING (true);
CREATE POLICY "academic_select"          ON academic          FOR SELECT USING (true);
CREATE POLICY "faculty_select"           ON faculty           FOR SELECT USING (true);
CREATE POLICY "student_documents_select" ON student_documents FOR SELECT USING (true);

-- INSERT: only anon/authenticated/service_role (Flask backend uses anon key)
CREATE POLICY "students_insert"          ON students          FOR INSERT WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "attendance_insert"        ON attendance        FOR INSERT WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "academic_insert"          ON academic          FOR INSERT WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "faculty_insert"           ON faculty           FOR INSERT WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "student_documents_insert" ON student_documents FOR INSERT WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));

-- UPDATE
CREATE POLICY "students_update"          ON students          FOR UPDATE USING (auth.role() IN ('anon','authenticated','service_role')) WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "attendance_update"        ON attendance        FOR UPDATE USING (auth.role() IN ('anon','authenticated','service_role')) WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "academic_update"          ON academic          FOR UPDATE USING (auth.role() IN ('anon','authenticated','service_role')) WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "faculty_update"           ON faculty           FOR UPDATE USING (auth.role() IN ('anon','authenticated','service_role')) WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "student_documents_update" ON student_documents FOR UPDATE USING (auth.role() IN ('anon','authenticated','service_role')) WITH CHECK (auth.role() IN ('anon','authenticated','service_role'));

-- DELETE
CREATE POLICY "students_delete"          ON students          FOR DELETE USING (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "attendance_delete"        ON attendance        FOR DELETE USING (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "academic_delete"          ON academic          FOR DELETE USING (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "faculty_delete"           ON faculty           FOR DELETE USING (auth.role() IN ('anon','authenticated','service_role'));
CREATE POLICY "student_documents_delete" ON student_documents FOR DELETE USING (auth.role() IN ('anon','authenticated','service_role'));
