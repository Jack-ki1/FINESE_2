# Changelog

All notable changes to FINESE2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2024-XX-XX

### Added
- Comprehensive .gitignore file for better version control
- Database models (User, Dataset, Experiment, ModelVersion, Job, AuditLog)
- Test framework with pytest and sample tests
- Docker support with Dockerfile and docker-compose.yml
- Makefile for common development tasks
- Environment configuration with .env.example
- Pre-commit hooks for code quality
- Documentation structure (docs/)
- Configuration files (setup.cfg, pyproject.toml)
- Enhanced main routes for SPA-style routing
- python-dotenv integration for environment variables

### Changed
- Updated application version to 4.0.0
- Improved database initialization with model imports
- Enhanced error handling in routes
- Better dashboard.html serving across all UI routes

### Improved
- Code organization and structure recommendations
- Developer experience with tooling
- Project maintainability
- Security best practices

### Deprecated
- Duplicate utils directory (consolidated into app/utils)

### Removed
- Empty directories (experiments/, models/, etc.) - to be cleaned by user

## [3.0.0] - Previous Release

### Features
- Consolidated architecture with 9 core modules
- Flask-based web application
- Data upload and management
- EDA capabilities
- Machine learning model training
- Dashboard creation
- Basic AI operations

---

## Version Guidelines

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## How to Update This File

When making changes:

1. Add entries under "Unreleased" section during development
2. Move to versioned section when releasing
3. Use appropriate categories: Added, Changed, Deprecated, Removed, Fixed, Security
4. Include GitHub issue/PR numbers when applicable

Example:
```markdown
## [Unreleased]

### Added
- New feature description (#123)

### Fixed
- Bug fix description (#124)
```
