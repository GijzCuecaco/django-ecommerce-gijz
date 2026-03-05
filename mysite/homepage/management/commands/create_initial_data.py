from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from homepage.models import Product, Category


class Command(BaseCommand):
    help = 'Create default superuser and sample products for the demo store'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        password = 'adminpass123'
        email = 'admin@example.com'
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created superuser {username}/{password}'))
        else:
            self.stdout.write('Superuser already exists')

        # Create default category if it doesn't exist
        default_category, _ = Category.objects.get_or_create(
            slug='general',
            defaults={'name': 'General', 'description': 'General Products'}
        )

        desc = 'LISTED ON 12/23/25 NY GIJZ CUECACO'
        samples = [
            {'name': 'Books Of Ancient Manunubo', 'slug': 'books-of-ancient-manunubo', 'description': desc, 'price': '59.99', 'stock': 25},
            {'name': 'Kutsara ni Kobe Bryant', 'slug': 'kutsara-ni-kobe-bryant', 'description': desc, 'price': '9.99', 'stock': 120},
            {'name': 'BuhokNiAlden', 'slug': 'buhokni-alden', 'description': desc, 'price': '14.50', 'stock': 80},
            {'name': 'PaaNiWally', 'slug': 'paa-ni-wally', 'description': desc, 'price': '34.00', 'stock': 40},
        ]

        created = 0
        updated = 0
        for s in samples:
            obj, was_created = Product.objects.update_or_create(
                slug=s['slug'],
                defaults={
                    'name': s['name'],
                    'description': s['description'],
                    'price': s['price'],
                    'stock': s['stock'],
                    'category': default_category
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} sample products, updated {updated} existing'))
