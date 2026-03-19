"""Management command to ensure the public tenant and localhost domain exist."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create the public tenant and localhost domain if they do not exist.'

    def handle(self, *args, **options):
        from apps.tenants.models import Domain, Tenant

        tenant, tenant_created = Tenant.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'System',
                'cnpj': '00.000.000/0000-00',
                'cnae': '0000-0',
                'responsible_email': 'admin@sistema.com',
            },
        )

        if tenant_created:
            self.stdout.write(self.style.SUCCESS('Public tenant created.'))
        else:
            self.stdout.write('Public tenant already exists.')

        domain, domain_created = Domain.objects.get_or_create(
            domain='localhost',
            defaults={'tenant': tenant, 'is_primary': True},
        )

        if domain_created:
            self.stdout.write(self.style.SUCCESS('Domain localhost created.'))
        else:
            self.stdout.write('Domain localhost already exists.')
