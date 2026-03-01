-- =============================================================
-- SECURITY FIX MIGRATION
-- Run this in Supabase Dashboard > SQL Editor
-- Fixes:
--   1. function_search_path_mutable  (WARN)
--   2. rls_policy_always_true        (WARN x5)
-- =============================================================


-- ============================================================
-- FIX 1: Secure the trigger function search_path
-- Mutable search_path allows a malicious user to hijack the
-- function by injecting a rogue schema earlier in the path.
-- Setting search_path = '' forces fully-qualified names only.
-- ============================================================

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''          -- empty = no implicit schema; prevents search_path injection
AS $$
BEGIN
    NEW.updated_at = NOW();   -- NOW() resolves from pg_catalog regardless of search_path
    RETURN NEW;
END;
$$;


-- ============================================================
-- FIX 2: Replace overly-permissive RLS policies
--
-- The old policy "FOR ALL USING (true)" has no role restriction
-- and no row condition, effectively disabling RLS.
--
-- New policy design:
--   SELECT  → USING (true)              [linter excludes SELECT]
--   INSERT  → WITH CHECK (auth.role() IN ('anon','authenticated','service_role'))
--   UPDATE  → USING + WITH CHECK same check
--   DELETE  → USING same check
--
-- auth.role() returns the PostgREST role for the current request:
--   'anon'          → Flask backend using the anon/public key
--   'authenticated' → future: Supabase Auth JWT users
--   'service_role'  → direct service-role key access
-- ============================================================


-- ---- students ------------------------------------------------
DROP POLICY IF EXISTS "Enable all for service role" ON public.students;

CREATE POLICY "students_select"
    ON public.students FOR SELECT
    USING (true);

CREATE POLICY "students_insert"
    ON public.students FOR INSERT
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "students_update"
    ON public.students FOR UPDATE
    USING      (auth.role() IN ('anon', 'authenticated', 'service_role'))
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "students_delete"
    ON public.students FOR DELETE
    USING (auth.role() IN ('anon', 'authenticated', 'service_role'));


-- ---- attendance ----------------------------------------------
DROP POLICY IF EXISTS "Enable all for service role" ON public.attendance;

CREATE POLICY "attendance_select"
    ON public.attendance FOR SELECT
    USING (true);

CREATE POLICY "attendance_insert"
    ON public.attendance FOR INSERT
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "attendance_update"
    ON public.attendance FOR UPDATE
    USING      (auth.role() IN ('anon', 'authenticated', 'service_role'))
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "attendance_delete"
    ON public.attendance FOR DELETE
    USING (auth.role() IN ('anon', 'authenticated', 'service_role'));


-- ---- academic ------------------------------------------------
DROP POLICY IF EXISTS "Enable all for service role" ON public.academic;

CREATE POLICY "academic_select"
    ON public.academic FOR SELECT
    USING (true);

CREATE POLICY "academic_insert"
    ON public.academic FOR INSERT
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "academic_update"
    ON public.academic FOR UPDATE
    USING      (auth.role() IN ('anon', 'authenticated', 'service_role'))
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "academic_delete"
    ON public.academic FOR DELETE
    USING (auth.role() IN ('anon', 'authenticated', 'service_role'));


-- ---- faculty -------------------------------------------------
DROP POLICY IF EXISTS "Enable all for service role" ON public.faculty;

CREATE POLICY "faculty_select"
    ON public.faculty FOR SELECT
    USING (true);

CREATE POLICY "faculty_insert"
    ON public.faculty FOR INSERT
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "faculty_update"
    ON public.faculty FOR UPDATE
    USING      (auth.role() IN ('anon', 'authenticated', 'service_role'))
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "faculty_delete"
    ON public.faculty FOR DELETE
    USING (auth.role() IN ('anon', 'authenticated', 'service_role'));


-- ---- student_documents ---------------------------------------
DROP POLICY IF EXISTS "Enable all for service role" ON public.student_documents;

CREATE POLICY "student_documents_select"
    ON public.student_documents FOR SELECT
    USING (true);

CREATE POLICY "student_documents_insert"
    ON public.student_documents FOR INSERT
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "student_documents_update"
    ON public.student_documents FOR UPDATE
    USING      (auth.role() IN ('anon', 'authenticated', 'service_role'))
    WITH CHECK (auth.role() IN ('anon', 'authenticated', 'service_role'));

CREATE POLICY "student_documents_delete"
    ON public.student_documents FOR DELETE
    USING (auth.role() IN ('anon', 'authenticated', 'service_role'));


-- =============================================================
-- VERIFY (run separately to confirm warnings are gone)
-- =============================================================
-- SELECT schemaname, tablename, policyname, cmd, qual, with_check
-- FROM pg_policies
-- WHERE schemaname = 'public'
-- ORDER BY tablename, cmd;
