# 🔐 SecureVault

A production-ready secrets management API built with **FastAPI**, **PostgreSQL**, and **Fernet encryption**. Designed for enterprise deployments with comprehensive DevOps tooling, CI/CD integration, and security-first architecture.

![Python](https://img.shields.io/badge/Python-98.2%25-3776ab?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-Passing-4caf50?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development Setup](#local-development-setup)
  - [Environment Configuration](#environment-configuration)
  - [Database Setup](#database-setup)
  - [Docker Deployment](#docker-deployment)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [API Endpoints](#api-endpoints)
- [Security Considerations](#security-considerations)
- [Monitoring & Logging](#monitoring--logging)
- [Contributing](#contributing)


---

## 🧭 Overview

**SecureVault** is a self-hosted secrets management service for teams and applications. It provides a secure REST API to store, retrieve, rotate, and audit sensitive credentials (API keys, database passwords, tokens, certificates, etc.) with:

- **End-to-end encryption** using Fernet (symmetric encryption)
- **JWT-based authentication** with configurable token expiry
- **Audit logging** for all secret operations
- **Secret versioning & rotation** capabilities
- **TTL support** for time-limited secrets
- **Rate limiting** to prevent abuse
- **Container-ready** with Docker & Docker Compose

Perfect for microservices, CI/CD pipelines, and distributed systems where secrets need centralized, auditable management.

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| 🔐 **Encryption at Rest** | Fernet symmetric encryption (AES-128 in CBC mode) |
| 🔑 **JWT Authentication** | HS256 signed tokens with configurable expiry |
| 🗄️ **Database** | PostgreSQL with SQLAlchemy ORM |
| 🔄 **Migrations** | Alembic for schema versioning |
| 📊 **Audit Logging** | Complete action trails for compliance |
| 🔁 **Secret Rotation** | Built-in versioning and rotation support |
| ⏱️ **TTL Support** | Time-to-live for temporary secrets |
| 🚦 **Rate Limiting** | Configurable request throttling (slowapi) |
| 📡 **Monitoring** | Sentry integration ready, structured JSON logging |
| 🐳 **Containerization** | Docker & Docker Compose configs included |
| ✅ **Test Coverage** | Pytest suite with unit & integration tests |
| 🔄 **CI/CD Ready** | GitHub Actions pipeline configured |

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | 0.104.1 |
| **Web Server** | Uvicorn | 0.24.0 |
| **Database** | PostgreSQL | 13+ |
| **ORM** | SQLAlchemy | 2.0.23 |
| **Migrations** | Alembic | 1.12.1 |
| **Encryption** | cryptography (Fernet) | 41.0.7 |
| **Authentication** | PyJWT / bcrypt | 2.9.0 / 4.1.1 |
| **Rate Limiting** | slowapi | 0.1.9 |
| **Testing** | pytest | 7.4.3 |
| **Code Quality** | black, flake8, mypy, bandit | Latest |
| **Container** | Docker / Docker Compose | Latest |
| **Logging** | python-json-logger | 2.0.7 |
| **Monitoring** | Sentry SDK | 1.38.0 |

---

## 📂 Project Structure

```
SecureVault/
├── .github/workflows/          # GitHub Actions CI/CD pipelines
│   └── ci.yml                  # (default) Test, lint, build workflow
│
├── alembic/                    # Database migration scripts
│   ├── versions/               # Individual migration files
│   ├── env.py                  # Alembic environment configuration
│   └── script.py.mako          # Migration template
│
├── app/                        # Application source code
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── routes.py               # API endpoint definitions
│   ├── database.py             # Database connection & session management
│   ├── auth.py                 # JWT authentication logic
│   ├── config.py               # Settings from environment
│   └── utils.py                # Helper utilities
│
├── docker/                     # Docker configurations
│   ├── Dockerfile              # Production image
│   ├── Dockerfile.dev          # Development image
│   └── docker-compose.yml      # Multi-container orchestration
│
├── docs/                       # Documentation
│   ├── API.md                  # API reference
│   ├── DEPLOYMENT.md           # Deployment guides
│   └── ARCHITECTURE.md         # System design
│
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures & configuration
│   ├── test_auth.py            # Authentication tests
│   ├── test_secrets.py         # Secret management tests
│   └── test_api.py             # API endpoint tests
│
├── .env.example                # Template environment file
├── .env                        # Actual config (git-ignored)
├── .gitignore                  # Git exclusions
├── alembic.ini                 # Alembic settings
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
├── secrets_manager.py          # Core secrets encryption & storage logic
├── __init__.py                 # Package metadata (v0.1.0)
└── README.md                   # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (3.11+ recommended)
- **PostgreSQL 13+** (locally or Docker)
- **Docker & Docker Compose** (optional, but recommended)
- **git**

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/Jawahir01/SecureVault.git
cd SecureVault

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Environment Configuration

Copy the example `.env` file and customize for your environment:

```bash
cp .env.example .env
```

Key variables to configure:

```env
# Database (default: Docker Compose service)
DATABASE_URL=postgresql://securevault_user:securevault_pass@postgres:5432/securevault_db
DATABASE_ECHO=False           # Set True for SQL debug logging

# Security - CHANGE THESE IN PRODUCTION!
SECRET_KEY=your-super-secret-key-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development      # development | production | staging
DEBUG=True                   # False in production

# API Configuration
API_TITLE=SecureVault
API_VERSION=1.0.0
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=5        # Requests per period
RATE_LIMIT_PERIOD=60         # Seconds

# Monitoring (optional)
LOG_LEVEL=INFO               # DEBUG | INFO | WARNING | ERROR
SENTRY_DSN=                  # Leave empty to disable Sentry
```

**⚠️ Production Security Notes:**
- Generate strong `SECRET_KEY` and `ENCRYPTION_KEY`: `openssl rand -hex 32`
- Use environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- Never commit `.env` files to git (already in `.gitignore`)

### Database Setup

Initialize the PostgreSQL database with Alembic migrations:

```bash
# Create initial migration (if needed)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations to database
alembic upgrade head

# Verify migration status
alembic current
alembic history
```

For rollback:

```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

### Docker Deployment

**Quickstart with Docker Compose:**

```bash
docker-compose up --build
```

This starts:
- **FastAPI app** on `http://localhost:8000`
- **PostgreSQL database** on `localhost:5432`
- **Interactive API docs** at `http://localhost:8000/docs`

**Check logs:**

```bash
docker-compose logs -f app
docker-compose logs -f postgres
```

**Stop services:**

```bash
docker-compose down
docker-compose down -v  # Also remove volumes/data
```

**Production Docker build:**

```bash
docker build -f docker/Dockerfile -t securevault:latest .
docker run -d \
  --name securevault \
  -p 8000:8000 \
  --env-file .env.production \
  securevault:latest
```

---

## 🧪 Testing

The project includes a comprehensive test suite (all **passing** ✅).

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_secrets.py

# Run specific test function
pytest tests/test_secrets.py::test_encrypt_decrypt

# Run with coverage report
pytest --cov=app --cov-report=html tests/

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests in parallel (faster)
pytest -n auto
```

**Test markers** (defined in `pytest.ini`):
```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Tests requiring DB/external services
```

**Output location:**
- Coverage report: `htmlcov/index.html`
- Pytest cache: `.pytest_cache/`

---

## 🔄 CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on every push and pull request:

### Workflow Steps

1. **Dependency Installation** — Install `requirements.txt`
2. **Linting & Code Quality** — Run flake8, black, isort, mypy, bandit
3. **Unit Tests** — pytest with coverage
4. **Integration Tests** — Database-dependent tests
5. **Security Scanning** — bandit for security issues, pip-audit for dependencies
6. **Build Docker Image** — Build and tag container image
7. **Push to Registry** (Optional) — Push to Docker Hub / ECR on `main` branch

**Status Badge:**
```markdown
![CI](https://github.com/Jawahir01/SecureVault/actions/workflows/ci.yml/badge.svg)
```

**View pipeline results:** https://github.com/Jawahir01/SecureVault/actions

---

## 📡 API Endpoints

> Full interactive API documentation available at `http://localhost:8000/docs` (Swagger UI)

### Core Secret Operations

```
POST   /api/secrets              # Store a new secret
GET    /api/secrets/:key         # Retrieve a secret
PUT    /api/secrets/:key         # Update/rotate secret
DELETE /api/secrets/:key         # Delete a secret
GET    /api/secrets              # List all secret keys
```

### Authentication

```
POST   /api/auth/login           # Get JWT token (username + password)
POST   /api/auth/refresh         # Refresh expired token
POST   /api/auth/logout          # Invalidate token
```

### Audit & Monitoring

```
GET    /api/secrets/:key/audit   # Get audit log for secret
GET    /api/secrets/:key/history # Get version history
GET    /api/health               # Health check
```

**Example: Store a secret**

```bash
curl -X POST "http://localhost:8000/api/secrets" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "db_password",
    "value": "super-secret-pw",
    "ttl": 86400,
    "metadata": {"environment": "production"}
  }'
```

**Example: Retrieve a secret**

```bash
curl -X GET "http://localhost:8000/api/secrets/db_password" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## 🔒 Security Considerations

### Encryption

- **Fernet (symmetric)** — AES-128 in CBC mode with HMAC authentication
- **At-rest encryption** — All secrets encrypted before database storage
- **In-transit encryption** — Use HTTPS in production (reverse proxy recommended)

### Authentication & Authorization

- **JWT tokens** — HS256 signed, configurable expiry
- **Access tokens** — Default 30 minutes (set via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh tokens** — Default 7 days (set via `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Password hashing** — bcrypt with salt rounds

### Defense Layers

1. **Secret Masking** — Sensitive values never logged
2. **Rate Limiting** — Prevent brute-force attacks (configurable)
3. **CORS** — Restrict origin access (configured in `.env`)
4. **Audit Logging** — Complete access trail for compliance
5. **Security Scanning** — CI/CD includes bandit & pip-audit

### Best Practices

- ✅ Rotate `SECRET_KEY` and `ENCRYPTION_KEY` quarterly
- ✅ Use strong, randomly-generated keys (32+ bytes)
- ✅ Deploy behind HTTPS-enabled reverse proxy (nginx, Traefik)
- ✅ Run in isolated network namespace (Kubernetes NetworkPolicy)
- ✅ Implement secrets backup & disaster recovery
- ✅ Monitor with Sentry for error tracking
- ✅ Use strong database passwords (alphanumeric + special chars)
- ✅ Enable database SSL connections in production
- ❌ Never hardcode secrets
- ❌ Never commit `.env` to git

---

## 📊 Monitoring & Logging

### Structured Logging

Logs are output as JSON for easy parsing by log aggregators:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "action": "secret_retrieved",
  "secret_key": "db_password",
  "user": "app_service",
  "duration_ms": 42
}
```

### Sentry Integration

Enable error tracking by setting `SENTRY_DSN`:

```env
SENTRY_DSN=https://key@sentry.io/project-id
```

### Log Levels

Set via `LOG_LEVEL` environment variable:

```
DEBUG   — Detailed diagnostic info
INFO    — General informational messages
WARNING — Warning messages (default for production)
ERROR   — Error conditions
```

### Metrics to Monitor

- API response times
- Database connection pool utilization
- Cache hit rate (if caching layer added)
- Failed authentication attempts
- Rate limit rejections
- Secret rotation frequency

---

## 🤝 Contributing

We welcome contributions! Follow these steps:

1. **Fork** the repository
2. **Create feature branch** — `git checkout -b feature/awesome-feature`
3. **Code** with test coverage
4. **Run linting & tests** — `pytest`, `black`, `flake8`, `mypy`
5. **Commit clearly** — `git commit -m "Add awesome feature"`
6. **Push** — `git push origin feature/awesome-feature`
7. **Open Pull Request** with description

### Development Guidelines

- Follow PEP 8 (enforced by black/flake8)
- Write tests for all new features
- Update docs for API changes
- Run full test suite before pushing: `pytest && black . && flake8 app/`

---


## 🆘 Support & Issues

- **Issues** — https://github.com/Jawahir01/SecureVault/issues
- **Discussions** — https://github.com/Jawahir01/SecureVault/discussions
- **Docs** — See `/docs` directory for detailed guides

---

<p align="center">
  <strong>🔐 Build secure, scalable secret management with SecureVault</strong><br>
  <em>Enterprise-grade secrets vault for DevSecOps teams</em>
</p>