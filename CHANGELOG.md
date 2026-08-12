# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Standardized GitHub templates (`bug_report.md`, `feature_request.md`, `pull_request_template.md`)
- Continuous Integration workflow with `flake8` Python linting via GitHub Actions
- `docs/api.md` detailing all backend endpoints and request validation rules
- `docs/architecture.md` detailing system components and application data flow
- Missing `CHANGELOG.md` to track future updates

### Changed
- Scrubbed sensitive Supabase credentials from `.env.example`
- Synchronized local development demo passwords in CLI output (`start.bat`) with actual backend logic

### Removed
- Cleaned up dummy/local auto-generated PDF reports from the root and `uploads/` directories
