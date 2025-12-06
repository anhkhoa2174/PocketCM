# GitHub Workflows Documentation

## Overview

This repository uses GitHub Actions to automate testing, linting, and deployment processes. The workflows are designed to provide fast feedback on pull requests while ensuring comprehensive testing on the main branch.

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Primary workflow for continuous integration**

**Triggers:**
- Push to `main`, `develop`, `feature/*` branches
- Pull requests to `main` or `develop`
- Daily scheduled run at 2 AM UTC

**Jobs:**

#### `full-test` (Main/Develop branches only)
- **Purpose:** Complete test suite with full coverage
- **When:** Main/develop branches or scheduled runs
- **Includes:**
  - Full pytest test suite with coverage reporting
  - Code linting with ruff
  - Type checking with mypy
  - Coverage upload to Codecov

#### `fast-test` (PRs & Feature branches)
- **Purpose:** Quick feedback for pull requests
- **When:** Pull requests or non-main/develop branches
- **Includes:**
  - Critical tests only (Pydantic validation, Security)
  - Fast linting with ruff
  - ~30 seconds execution time

#### `security` (Main branch only)
- **Purpose:** Security vulnerability scanning
- **When:** Main branch only
- **Includes:**
  - Safety dependency check
  - Bandit security linter

#### `docker-test` (Main branch only)
- **Purpose:** Docker image validation
- **When:** Main branch only, after full-test passes
- **Includes:**
  - Docker build
  - Container health check
  - API endpoint validation

### 2. Unit Tests (`test.yml`)

**Dedicated unit testing workflow**

**Triggers:**
- Push to any branch
- Pull requests to any branch

**Features:**
- Runs tests on Python 3.11
- Coverage reporting to Codecov
- Artifact upload for HTML reports
- Parallel execution with matrix strategy

### 3. Quick Tests (`quick-test.yml`)

**Ultra-fast testing for feature branches**

**Triggers:**
- Push to non-main branches
- (Not triggered on pull requests to avoid duplication with ci.yml)

**Features:**
- Only runs critical tests
- Minimal dependencies installation
- ~15 seconds execution time

## Branch Strategy

### `main` Branch
- ✅ **Full test suite** with all checks
- ✅ **Security scanning**
- ✅ **Docker validation**
- ✅ **Coverage reporting**
- ✅ **Deployment ready**

### `develop` Branch
- ✅ **Full test suite** with all checks
- ❌ No security scan (skip for faster iteration)
- ❌ No Docker test (skip for faster iteration)
- ✅ **Coverage reporting**

### `feature/*` Branches
- ❌ **Fast tests only** (critical path validation)
- ❌ No security scan
- ❌ No Docker test
- ❌ Limited coverage (speed optimization)
- ⚡ **Fast feedback** (~30 seconds)

### Pull Requests
- ✅ **Fast tests** for quick validation
- ✅ **Full context** from target branch
- ✅ **Automated merges** when checks pass

## Caching Strategy

### Dependency Caching
- Uses `actions/cache@v3` for pip packages
- Separate cache keys for different job types
- Fast cache invalidation on dependency changes

### Build Caching
- Docker layer caching with GitHub Actions cache
- Optimized for frequent CI runs

## Coverage Reporting

### Codecov Integration
- Coverage reports uploaded to Codecov for main branches
- Historical coverage tracking
- PR coverage comments
- Coverage badges in README

### Artifacts
- HTML coverage reports saved as artifacts
- Available for download from GitHub Actions UI
- Retained for 30 days

## Performance Optimization

### Fast Feedback Loop
- **Feature branches:** ~30 seconds
- **Pull requests:** ~1 minute
- **Main branch:** ~3-5 minutes (full suite)

### Resource Usage
- Parallel job execution where applicable
- Smart caching reduces redundant work
- Conditional job execution based on branch

## Monitoring

### Status Indicators
- GitHub Actions status badges
- Test coverage badges
- Build status in PR comments

### Notifications
- Automatic status updates on pull requests
- Failure notifications with detailed logs
- Success confirmations for completed pipelines

## Troubleshooting

### Common Issues

1. **Cache Misses**
   - Invalidated on dependency changes
   - Automatic regeneration on next run

2. **Test Failures**
   - Detailed logs in GitHub Actions UI
   - Local reproduction using same command

3. **Timeouts**
   - Fast-test mode for quick iterations
   - Adjustable timeouts in workflow files

### Debugging
```bash
# Run tests locally like CI
pytest tests/ -v --cov=src

# Run specific test files
pytest tests/test_pydantic_validation.py -v

# Check linting
ruff check src/
```

## Best Practices

1. **Commit Messages:** Follow conventional commit format
2. **Branch Naming:** Use descriptive feature branch names
3. **Pull Requests:** Keep PRs focused and well-tested
4. **Dependencies:** Update requirements.txt pin versions
5. **Tests:** Write tests for new features and bug fixes

## Future Enhancements

- [ ] Integration tests with test database
- [ ] Performance regression testing
- [ ] Multi-environment testing (staging/production)
- [ ] Automated deployment on successful main branch builds
- [ ] Slack/Discord notifications for CI/CD events