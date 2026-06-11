# 🐛 SecureVault Debug Issues & Solutions

> **Purpose**: Document common issues encountered during development, testing, and deployment. This serves as a troubleshooting guide for developers building or maintaining the application.

**Last Updated**: June 11, 2026  
**Version**: 1.0

---

## Table of Contents

1. [Database & Migration Issues](#database--migration-issues)
2. [Authentication & Security Issues](#authentication--security-issues)
3. [Encryption & Key Management Issues](#encryption--key-management-issues)
4. [Docker & Deployment Issues](#docker--deployment-issues)
5. [Testing Issues](#testing-issues)
6. [API & Performance Issues](#api--performance-issues)
7. [Environment Configuration Issues](#environment-configuration-issues)

---

## Database & Migration Issues

### Issue: Database Connection Timeout in Docker

**Problem**: Connection refused when trying to connect to PostgreSQL from API container.

**Root Cause**: 
- PostgreSQL container not fully initialized before API tries to connect
- Database not exposed on correct port in docker-compose
- Network not properly configured between containers

**Solution**:
```yaml
# docker/docker-compose.yml
services:
  postgres:
    # ... config ...
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  api:
    depends_on:
      postgres:
        condition: service_healthy
```

**Prevention**: Use health checks and `depends_on` with service_healthy condition.

---

### Issue: Alembic Migration Fails on Fresh Database

**Problem**: `alembic upgrade head` fails with "target database is not up to date"

**Root Cause**: 
- Migration environment not properly initialized
- Database schema version table not created
- Concurrent migrations running

**Solution**:
```bash
# Reset migration state
alembic stamp head
alembic downgrade base
alembic upgrade head
```

**Prevention**: Ensure only one migration process runs at a time. Use database locks in production.

---

### Issue: SQLAlchemy ORM Session Leak in FastAPI

**Problem**: Warning about unclosed sessions, increased memory usage over time

**Root Cause**: 
- Database session not properly closed in dependency injection
- Exception in endpoint prevents session cleanup
- Async context not properly managed

**Solution**:
```python
# app/database.py
@asynccontextmanager
async def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Prevention**: Use try-finally blocks and async context managers consistently.

---

## Authentication & Security Issues

### Issue: JWT Token Validation Fails After Secret Rotation

**Problem**: Existing tokens become invalid after changing SECRET_KEY

**Root Cause**: 
- HS256 tokens signed with old key, validated with new key
- No grace period for key rotation
- Multiple instances with different keys

**Solution**:
```python
# app/security/auth.py - Implement key versioning
class AuthService:
    def verify_token(self, token: str):
        # Try current key first, then previous key for grace period
        for secret_key in [self.current_key, self.previous_key]:
            try:
                payload = jwt.decode(token, secret_key, algorithms=["HS256"])
                return payload
            except jwt.InvalidSignatureError:
                continue
        raise InvalidTokenError()
```

**Prevention**: Implement key versioning with grace periods (7+ days) for rotation.

---

### Issue: Password Hash Not Verifying Correctly

**Problem**: Login fails even with correct password; bcrypt verification returns False

**Root Cause**: 
- Encoding issues (bytes vs string)
- Salt rounds mismatch
- Unicode normalization not applied

**Solution**:
```python
# Ensure consistent encoding
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
```

**Prevention**: Use standardized encoding (UTF-8) throughout. Test with unicode passwords.

---

### Issue: Rate Limiting Not Working in Docker

**Problem**: Rate limit headers present but requests not actually throttled

**Root Cause**: 
- Redis not configured in slowapi
- Limiter using in-memory storage (doesn't persist across instances)
- Multiple API instances each have independent limits

**Solution**:
```python
# app/main.py - Use Redis for distributed rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.ext.redis import RedisStorage

redis_storage = RedisStorage("redis://redis:6379")
limiter = Limiter(key_func=get_remote_address, storage=redis_storage)
```

**Prevention**: Use Redis in production. Document that in-memory limiting is for development only.

---

## Encryption & Key Management Issues

### Issue: Fernet Decryption Fails - "Invalid Token"

**Problem**: `cryptography.fernet.InvalidToken` when decrypting secrets

**Root Cause**: 
- Encryption key changed between storage and retrieval
- Encrypted data corrupted during transmission/storage
- Wrong key version being used
- TTL expired (if using Fernet with TTL)

**Solution**:
```python
# app/security/encryption.py - Add debug logging
from cryptography.fernet import Fernet, InvalidToken

class EncryptionService:
    def decrypt(self, encrypted_value: str) -> str:
        try:
            cipher = Fernet(self.key.encode())
            decrypted = cipher.decrypt(encrypted_value.encode())
            return decrypted.decode('utf-8')
        except InvalidToken as e:
            logger.error(f"Decryption failed for key={self.key[:8]}..., ciphertext_len={len(encrypted_value)}")
            raise
```

**Prevention**: 
- Never change ENCRYPTION_KEY without re-encrypting all secrets
- Log encryption key fingerprints for debugging
- Test round-trip encryption in tests

---

### Issue: Encryption Key Not Loaded from Environment

**Problem**: Secrets encrypted with dummy key, decryption fails in production

**Root Cause**: 
- ENCRYPTION_KEY environment variable not set
- Config reading from wrong source
- Local testing config overriding production config

**Solution**:
```python
# app/config.py - Validate on startup
class Settings:
    def __init__(self):
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        if not self.encryption_key or len(self.encryption_key) < 32:
            raise ValueError("ENCRYPTION_KEY must be set and >= 32 chars")
```

**Prevention**: Validate all critical secrets on application startup. Fail fast.

---

## Docker & Deployment Issues

### Issue: Docker Build Fails - "No module named app"

**Problem**: `ModuleNotFoundError: No module named 'app'` in Docker container

**Root Cause**: 
- WORKDIR not set correctly
- PYTHONPATH not configured
- Relative imports used without proper path setup

**Solution**:
```dockerfile
# docker/Dockerfile
WORKDIR /app
COPY SecureVault/ .
ENV PYTHONPATH=/app:$PYTHONPATH

RUN pip install -r requirements.txt
```

**Prevention**: Always set WORKDIR and PYTHONPATH explicitly. Use absolute imports.

---

### Issue: Database Changes Not Persisting in Docker

**Problem**: Secrets added in one container run, gone in next run

**Root Cause**: 
- Volume not mounted for PostgreSQL
- Using temporary sqlite instead of postgres
- Container stopped without commit

**Solution**:
```yaml
# docker/docker-compose.yml
services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  api:
    depends_on:
      - postgres

volumes:
  postgres_data:
```

**Prevention**: Always use named volumes. Test persistence with container restart.

---

### Issue: Port Conflict - Port 5432 or 8000 Already in Use

**Problem**: `Error: Port 5432 is already in use` or `Address already in use`

**Root Cause**: 
- Previous container not stopped
- Another service using same port
- Port binding not released

**Solution**:
```bash
# Find and kill process using port
netstat -ano | findstr :5432  # Windows
lsof -i :5432  # Linux/Mac

# Or stop all docker containers
docker-compose down -v

# Or change ports
docker run -p 5433:5432 postgres
```

**Prevention**: Use `docker-compose down` to properly clean up. Map to different local ports if needed.

---

## Testing Issues

### Issue: Tests Pass Locally but Fail in CI/CD

**Problem**: `pytest` passes locally but fails in GitHub Actions

**Root Cause**: 
- Environment variables not set in CI
- Database not initialized in CI
- Race conditions exposed by parallel test execution
- Platform-specific path issues (Windows vs Linux)

**Solution**:
```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Set environment
        run: |
          echo "DATABASE_URL=postgresql://postgres:postgres@localhost/test_db" >> $GITHUB_ENV
```

**Prevention**: Use same test config in CI as locally. Run CI tests locally before push.

---

### Issue: Test Database Not Cleaned Between Tests

**Problem**: Test data persists; tests fail if run in different order

**Root Cause**: 
- Database cleanup missing in teardown
- Fixtures not properly isolated
- Shared state between tests

**Solution**:
```python
# tests/conftest.py
@pytest.fixture(scope="function")
def db():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    
    yield db_session
    
    db_session.close()
    Base.metadata.drop_all(bind=engine)  # CRITICAL: Clean up after test
```

**Prevention**: Use function-scoped fixtures, not session-scoped. Explicitly drop tables after tests.

---

### Issue: pytest Fixtures Not Found

**Problem**: `fixture 'client' not found` or `fixture 'db' not found`

**Root Cause**: 
- conftest.py in wrong directory
- conftest.py not imported
- pytest not finding the file

**Solution**:
```
tests/
├── conftest.py        # Root conftest - fixtures available to all tests
├── unit/
│   └── test_auth.py
├── integration/
│   └── test_api.py
```

**Prevention**: Put conftest.py in `tests/` root. pytest auto-discovers it.

---

## API & Performance Issues

### Issue: API Returns 500 Error with No Logs

**Problem**: `Internal Server Error` with no helpful error message in logs

**Root Cause**: 
- Exception not being caught properly
- Logging not configured
- Async code raising exceptions not awaited
- Database connection pool exhausted

**Solution**:
```python
# app/main.py - Add exception handler
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")  # Log full traceback
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": str(type(exc))}
    )
```

**Prevention**: Add global exception handlers. Configure structured logging (JSON). Monitor logs.

---

### Issue: High Memory Usage / Memory Leak

**Problem**: Container memory grows until OOM kill

**Root Cause**: 
- Database connections not closed
- Large query results in memory
- Circular references preventing garbage collection
- Unbounded caches

**Solution**:
```python
# Enable memory profiling
from memory_profiler import profile

@profile
def retrieve_secrets(user_id: int):
    # Process in batches
    batch_size = 100
    offset = 0
    while True:
        secrets = db.query(Secret).filter(
            Secret.user_id == user_id
        ).offset(offset).limit(batch_size).all()
        
        if not secrets:
            break
        
        # Process batch
        yield from secrets
        offset += batch_size
```

**Prevention**: Use streaming/pagination for large datasets. Profile in staging environment.

---

### Issue: Slow API Response - Timeout in Load Balancer

**Problem**: Request takes >30s, timeout error

**Root Cause**: 
- N+1 query problem (querying in loop)
- Unindexed database queries
- Encryption/decryption on large payloads
- Blocking I/O in async code

**Solution**:
```python
# Use eager loading
secrets = db.query(Secret).filter(
    Secret.user_id == user_id
).options(joinedload(Secret.versions)).all()  # Load relationships eagerly

# Add database indexes
# migrations/versions/xxx_add_indexes.py
def upgrade():
    op.create_index('ix_secret_user_id', 'secret', ['user_id'])
    op.create_index('ix_secret_created_at', 'secret', ['created_at'])
```

**Prevention**: Use query analysis tools. Profile endpoints. Add database indexes.

---

## Environment Configuration Issues

### Issue: Environment Variables Not Loading

**Problem**: `KeyError` or AttributeError when accessing `settings.some_var`

**Root Cause**: 
- `.env` file not in correct location
- Environment variables not exported
- python-dotenv not installed
- Wrong file path in config

**Solution**:
```python
# app/config.py - Use python-dotenv
from dotenv import load_dotenv
import os

# Load from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./securevault.db")
```

**Prevention**: Use `.env.example` with all required vars. Validate config on startup.

---

### Issue: .env Secrets Exposed in Version Control

**Problem**: API keys, passwords in GitHub repository history

**Root Cause**: 
- `.env` file committed to git
- Secrets logged to stdout
- Secrets in error messages
- Cache still holds old commits

**Solution**:
```bash
# Immediately remove from history
git filter-branch --tree-filter 'rm -f .env' -- --all
git push --force-with-lease

# Regenerate all secrets
# Rotate all exposed API keys, passwords, tokens
```

**Prevention**: 
- Add `.env` to `.gitignore` immediately
- Use `.env.example` for template
- Use GitHub secrets for CI/CD
- Scan commits with `truffleHog` or `git-secrets`

---

## Related Documentation

- [Security Considerations](../SECURITY.md)
- [Testing Guide](./testing.md)
- [Deployment Guide](./deployment.md)
- [API Reference](./api.md)

---

## Reporting Issues

When reporting issues:
1. Check this document first
2. Include error message and logs
3. Include environment (Docker/Local, OS, Python version)
4. Include steps to reproduce
5. Include relevant code/config snippets

---

**Note**: This document is living and should be updated as new issues are discovered and resolved.
