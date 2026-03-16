# Multi-Tenant SaaS Platform

Enterprise multi-tenant SaaS platform built with Django + Next.js, featuring per-domain tenant isolation, role-based access control, JWT authentication, and async email processing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Next.js     │  │  Django API  │  │  Celery Worker   │  │
│  │  :3000       │→ │  :8000       │  │  (async emails)  │  │
│  └──────────────┘  └──────┬───────┘  └────────┬─────────┘  │
│                            │                    │            │
│                    ┌───────┴────────────────────┴──────┐    │
│                    │          Redis :6379               │    │
│                    └───────────────────────────────────┘    │
│                            │                                 │
│                    ┌───────┴───────┐                        │
│                    │  PostgreSQL   │  (Supabase in prod)    │
│                    │  :5432        │                        │
│                    └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer        | Technology                         |
|--------------|-------------------------------------|
| Backend      | Django 4.2 + DRF                    |
| Multi-tenant | django-tenants (schema per tenant)  |
| Auth         | JWT (simplejwt) + Django Auth       |
| Rate Limit   | django-ratelimit                    |
| CORS         | django-cors-headers                 |
| Queue        | Celery + Redis                      |
| Email        | Resend API (async via Celery)       |
| Database     | PostgreSQL (Supabase)               |
| Frontend     | Next.js 14 + shadcn/ui              |
| Container    | Docker + Docker Compose             |

## Multi-Tenancy

Each tenant gets an isolated PostgreSQL schema:

```
empresa1.sistema.com → schema: empresa1
empresa2.sistema.com → schema: empresa2
public (shared)      → schema: public (tenants, domains tables)
```

Every request is automatically routed to the correct tenant based on the domain.

## User Roles

| Role          | Django Admin | Frontend Access         |
|---------------|-------------|-------------------------|
| GLOBAL_ADMIN  | ✅ Full     | Full                    |
| RH            | ❌          | Full (manage users etc) |
| LEADER        | ❌          | Limited (read-only)     |

## Security Features

- **Rate limiting**: 3 login attempts per minute per IP
- **Account lockout**: Locked after 3 consecutive wrong passwords
- **Email notification**: User receives email when account is locked
- **Magic Link**: Secure password reset via Resend API
- **JWT**: Short-lived access tokens (15min) + refresh tokens (7 days)
- **Token blacklist**: Logout invalidates refresh tokens

## Quick Start

### Prerequisites

- Docker & Docker Compose
- A [Resend](https://resend.com) account (for emails)
- A [Supabase](https://supabase.com) PostgreSQL instance (production) or local Docker DB

### 1. Clone and configure

```bash
git clone <repo>
cd final-project

# Configure backend
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

### 2. Start services

```bash
# Build and start all services
make build
make up

# Or with docker compose directly
docker compose up -d
```

### 3. Initialize database

```bash
# Run migrations
make migrate

# Create the public tenant and demo tenant
make seed

# Create your global admin user
make createsuperuser
```

### 4. Access the application

| Service           | URL                              |
|-------------------|----------------------------------|
| Frontend          | http://localhost:3000            |
| Django API        | http://localhost:8000            |
| Django Admin      | http://localhost:8000/admin/     |
| API Docs (Swagger)| http://localhost:8000/api/docs/  |
| Celery Flower     | http://localhost:5555            |

### 5. Create a tenant via Django Admin

1. Go to http://localhost:8000/admin/
2. Login with your superuser credentials
3. Go to **Tenants** → **Add Tenant**
4. Fill in company details (name, CNPJ, CNAE, email)
5. Set schema_name (e.g., `empresa1`)
6. Add a Domain (e.g., `empresa1.localhost`)
7. Add `127.0.0.1 empresa1.localhost` to your `/etc/hosts`
8. Access http://empresa1.localhost:8000

## API Endpoints

### Authentication

```
POST /api/auth/login/              # Login → JWT tokens
POST /api/auth/logout/             # Logout (blacklist token)
POST /api/auth/token/refresh/      # Refresh access token
POST /api/auth/password/reset/     # Request magic link
POST /api/auth/password/reset/confirm/ # Confirm reset with token
```

### Users

```
GET    /api/users/me/          # Current user profile
GET    /api/users/             # List users (RH+)
POST   /api/users/             # Create user (RH+)
GET    /api/users/{id}/        # Get user
PUT    /api/users/{id}/        # Update user
DELETE /api/users/{id}/        # Deactivate user
POST   /api/users/change-password/  # Change password
```

### Core

```
GET /api/health/               # Health check
GET /api/tenant/               # Current tenant info
GET /api/dashboard/stats/      # Dashboard statistics
```

## Supabase Configuration

To use Supabase PostgreSQL instead of local Docker:

1. Create a project at https://supabase.com
2. Get your connection string from **Project Settings → Database**
3. Update `backend/.env`:

```env
DB_NAME=postgres
DB_USER=postgres.your-project-ref
DB_PASSWORD=your-password
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=6543
```

4. In `docker-compose.yml`, remove the `db` service and its dependencies

## Project Structure

```
final-project/
├── backend/
│   ├── apps/
│   │   ├── tenants/      # Tenant & Domain models
│   │   ├── users/        # Custom User model, roles, permissions
│   │   ├── authentication/ # Login, logout, JWT, password reset
│   │   └── core/         # Health check, dashboard stats
│   ├── config/
│   │   ├── settings/     # base, development, production
│   │   ├── celery.py     # Celery configuration
│   │   └── urls.py       # Root URL conf
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # UI components (shadcn/ui)
│   │   ├── services/     # API client, auth service
│   │   └── hooks/        # useAuth, useToast
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── Makefile
└── README.md
```

## Development

```bash
# View logs
make logs

# Django shell
make shell

# Run specific service logs
docker compose logs -f api
docker compose logs -f celery_worker

# Restart a service
docker compose restart api

# Access PostgreSQL
docker compose exec db psql -U postgres -d saas_db
```

## Environment Variables

See `backend/.env.example` for all available configuration options.

Key variables:
- `SECRET_KEY` - Django secret key (change in production!)
- `RESEND_API_KEY` - Your Resend API key for emails
- `DB_*` - Database connection settings
- `REDIS_URL` - Redis connection string
- `FRONTEND_URL` - Frontend URL for email links
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins
