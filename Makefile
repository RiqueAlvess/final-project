.PHONY: help build up down logs shell migrate createsuperuser seed_hse

help:
	@echo "Available commands:"
	@echo "  make build           - Build all Docker images"
	@echo "  make up              - Start all services (Redis + API + Celery + Frontend)"
	@echo "  make down            - Stop all services"
	@echo "  make logs            - Show logs from all services"
	@echo "  make shell           - Open Django shell"
	@echo "  make migrate         - Run database migrations against Supabase"
	@echo "  make createsuperuser - Create a global admin superuser"
	@echo "  make seed            - Create public + demo tenants"
	@echo ""
	@echo ""
	@echo "API runs on port 8080 by default. Override with: API_PORT=9000 make up"
	@echo "Database is Supabase (external). Set DATABASE_URL in backend/.env before running."

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec api python manage.py shell

migrate:
	docker compose exec api python manage.py migrate_schemas --shared
	docker compose exec api python manage.py migrate_schemas

makemigrations:
	docker compose exec api python manage.py makemigrations

createsuperuser:
	docker compose exec api python manage.py createsuperuser

seed:
	docker compose exec api python manage.py shell -c "
from apps.tenants.models import Tenant, Domain

# Create public tenant
try:
    public = Tenant.objects.get(schema_name='public')
    print('Public tenant already exists')
except Tenant.DoesNotExist:
    public = Tenant.objects.create(
        schema_name='public',
        name='System',
        cnpj='00.000.000/0000-00',
        cnae='0000-0',
        responsible_email='admin@sistema.com',
    )
    Domain.objects.create(domain='localhost', tenant=public, is_primary=True)
    print('Public tenant created')

# Create demo tenant
try:
    demo = Tenant.objects.get(schema_name='demo')
    print('Demo tenant already exists')
except Tenant.DoesNotExist:
    demo = Tenant.objects.create(
        schema_name='demo',
        name='Demo Company',
        cnpj='12.345.678/0001-90',
        cnae='6201-5',
        responsible_email='rh@demo.com',
    )
    Domain.objects.create(domain='demo.localhost', tenant=demo, is_primary=True)
    print('Demo tenant created: http://demo.localhost:8080')
"

seed_hse:
	docker compose exec api python manage.py seed_hse_questions

restart:
	docker compose restart

status:
	docker compose ps
