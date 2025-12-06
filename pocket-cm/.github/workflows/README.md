# GitHub Workflows Documentation

## Overview

This repository uses GitHub Actions to automate testing, linting, and deployment processes. The workflows are optimized for fast feedback on pull requests while ensuring comprehensive testing on main branches.

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Smart unified CI/CD pipeline with conditional execution**

**Triggers:**
- Push to `main`, `develop`, `feature/*` branches
- Pull requests to `main` or `develop`
- Daily scheduled run at 2 AM UTC

**Jobs:**

#### `test-config`
- **Purpose:** Determine optimal test strategy based on branch/context
- **Outputs:** `test-mode`, `run-security`, `run-docker`, `cache-key`
- **Logic:**
  - Main branch: `full` mode + security + docker
  - Develop branch: `full` mode only
  - Pull requests: `fast` mode
  - Feature branches: `quick` mode

#### `test` (Conditional execution)
- **Quick Mode** (~15 seconds):
  - Critical Pydantic validation tests only
  - No linting (maximum speed)

- **Fast Mode** (~30 seconds):
  - Critical tests (Pydantic + Security)
  - Fast linting on src/ only

- **Full Mode** (~3-5 minutes):
  - Complete test suite with coverage reporting
  - Full linting (src/ + tests/)
  - Type checking with mypy
  - Coverage upload to Codecov
  - HTML coverage artifacts

#### `security` (Main branch only)
- **Purpose:** Security vulnerability scanning
- **Tools:** Safety (dependencies) + Bandit (code analysis)
- **Output:** JSON reports for security monitoring

#### `docker-test` (Main branch only)
- **Purpose:** Docker image validation
- **Steps:** Build → Health check → API endpoint validation
- **Caching:** GitHub Actions cache for Docker layers

### 2. Release Pipeline (`release.yml`)

**Automated deployment on GitHub releases**

**Triggers:**
- Release publication event

**Features:**
- Docker Hub authentication
- Multi-tagging strategy (branch, PR, semver)
- Optimized build caching
- Production-ready image publishing

## Branch Strategy

### `main` Branch
- ✅ **Full test suite** with comprehensive checks
- ✅ **Security scanning** for vulnerabilities
- ✅ **Docker validation** with health checks
- ✅ **Coverage reporting** to Codecov
- ✅ **Release ready** for production

### `develop` Branch
- ✅ **Full test suite** with all checks
- ❌ No security scan (faster iteration)
- ❌ No Docker test (faster iteration)
- ✅ **Coverage reporting** for tracking

### `feature/*` Branches
- ⚡ **Quick tests only** (15 seconds)
- ✅ Critical path validation
- ❌ No security scan
- ❌ No Docker test
- ❌ No coverage reporting (speed optimization)

### Pull Requests
- ⚡ **Fast tests** (30 seconds) for quick validation
- ✅ **Smart caching** based on test mode
- ✅ **Automated merges** when all checks pass

## Performance Optimizations

### Smart Caching
- **Mode-based cache keys:** Different caches for quick/fast/full modes
- **Dependency-based invalidation:** Fast cache refresh on requirement changes
- **Docker layer caching:** Optimized for frequent builds

### Execution Times
- **Feature branches:** ~15 seconds (quick mode)
- **Pull requests:** ~30 seconds (fast mode)
- **Main/Develop:** ~3-5 minutes (full mode)

### Resource Efficiency
- **Conditional job execution:** Only run what's needed
- **Parallel job execution:** Security and Docker tests run in parallel
- **Matrix strategy:** Python version testing when needed

## Monitoring & Observability

### Coverage Tracking
- **Codecov integration:** Historical coverage tracking
- **PR comments:** Coverage diff visualization
- **Artifacts:** HTML reports available for download

### Status Badges
- CI pipeline status
- Test coverage percentage
- Build health indicators

### Security Monitoring
- **Dependency vulnerability scanning** with Safety
- **Static code analysis** with Bandit
- **JSON report outputs** for integration

## Troubleshooting Guide

### Common Issues

1. **Cache Invalidation**
   ```bash
   # Clear cache by changing requirements.txt version
   # Or manually invalidate in GitHub Actions settings
   ```

2. **Test Timeouts**
   - Quick mode: 15 second timeout
   - Fast mode: 30 second timeout
   - Full mode: 5 minute timeout

3. **Docker Build Failures**
   ```bash
   # Test locally before push
   docker build -t pocket-cm:test .
   docker run -p 8000:8000 pocket-cm:test
   ```

### Local Development Commands
```bash
# Run tests like CI
pytest tests/ -v --cov=src                    # Full mode
pytest tests/test_pydantic_validation.py -v   # Quick mode
pytest tests/test_pydantic_validation.py tests/test_security.py -v  # Fast mode

# Linting
ruff check src/                    # Fast mode
ruff check src/ tests/             # Full mode

# Type checking
mypy src/ --ignore-missing-imports
```

## Best Practices

1. **Feature Development:** Use descriptive feature branch names
2. **Pull Requests:** Keep PRs focused with clear descriptions
3. **Testing:** Write tests for new features and edge cases
4. **Dependencies:** Pin versions in requirements.txt
5. **Commits:** Use conventional commit format for automated changelogs

## Configuration Details

### Environment Variables
- `DOCKER_USERNAME`: Docker Hub credentials
- `DOCKER_PASSWORD`: Docker Hub access token
- `CODECOV_TOKEN`: Coverage reporting (optional)

### Workflow Permissions
- `contents: read`: Repository access
- `packages: write`: Docker registry access

## Future Roadmap

- [ ] Integration tests with test database
- [ ] Performance regression testing
- [ ] Multi-environment deployments (staging/production)
- [ ] Slack/Discord notifications for CI events
- [ ] Automated semantic versioning
- [ ] Security vulnerability auto-remediation