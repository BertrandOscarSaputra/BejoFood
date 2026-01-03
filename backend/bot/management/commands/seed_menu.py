"""
Management command to create sample menu data with Indonesian cuisine.
Usage: python manage.py seed_menu
"""
from django.core.management.base import BaseCommand
from menu.models import Category, MenuItem


class Command(BaseCommand):
    help = 'Seed database with Indonesian cuisine menu data'

    def handle(self, *args, **options):
        self.stdout.write('Creating Indonesian cuisine menu...')

        # Categories (use get_or_create to avoid breaking existing orders)

        # Categories
        categories_data = [
            {'name': 'Makanan Pembuka', 'emoji': '🥗', 'order': 1, 'description': 'Appetizers'},
            {'name': 'Nasi & Mie', 'emoji': '🍚', 'order': 2, 'description': 'Rice & Noodles'},
            {'name': 'Ayam & Bebek', 'emoji': '🍗', 'order': 3, 'description': 'Chicken & Duck'},
            {'name': 'Sate & Bakar', 'emoji': '🍢', 'order': 4, 'description': 'Satay & Grilled'},
            {'name': 'Seafood', 'emoji': '🦐', 'order': 5, 'description': 'Seafood dishes'},
            {'name': 'Minuman', 'emoji': '🥤', 'order': 6, 'description': 'Beverages'},
            {'name': 'Dessert', 'emoji': '🍰', 'order': 7, 'description': 'Desserts'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat = Category.objects.create(**cat_data)
            categories[cat_data['name']] = cat
            self.stdout.write(f"  Created: {cat}")

        # Menu items with Indonesian cuisine and IDR prices
        items_data = [
            # Makanan Pembuka (Appetizers)
            {'category': 'Makanan Pembuka', 'name': 'Lumpia Goreng', 'price': 15000, 'description': 'Crispy spring rolls with vegetables'},
            {'category': 'Makanan Pembuka', 'name': 'Tahu Goreng', 'price': 12000, 'description': 'Fried tofu with sweet soy sauce'},
            {'category': 'Makanan Pembuka', 'name': 'Tempe Mendoan', 'price': 10000, 'description': 'Thin crispy fried tempeh'},
            {'category': 'Makanan Pembuka', 'name': 'Perkedel Jagung', 'price': 8000, 'description': 'Corn fritters'},
            {'category': 'Makanan Pembuka', 'name': 'Gado-Gado', 'price': 25000, 'description': 'Vegetable salad with peanut sauce'},
            
            # Nasi & Mie (Rice & Noodles)
            {'category': 'Nasi & Mie', 'name': 'Nasi Goreng Spesial', 'price': 28000, 'description': 'Special fried rice with egg and chicken'},
            {'category': 'Nasi & Mie', 'name': 'Nasi Padang', 'price': 35000, 'description': 'Steamed rice with Padang-style dishes'},
            {'category': 'Nasi & Mie', 'name': 'Nasi Uduk', 'price': 22000, 'description': 'Coconut rice with side dishes'},
            {'category': 'Nasi & Mie', 'name': 'Mie Goreng', 'price': 25000, 'description': 'Fried noodles with vegetables'},
            {'category': 'Nasi & Mie', 'name': 'Mie Ayam Bakso', 'price': 20000, 'description': 'Chicken noodles with meatballs'},
            {'category': 'Nasi & Mie', 'name': 'Kwetiau Goreng', 'price': 27000, 'description': 'Stir-fried flat rice noodles'},
            
            # Ayam & Bebek (Chicken & Duck)
            {'category': 'Ayam & Bebek', 'name': 'Ayam Goreng Kremes', 'price': 32000, 'description': 'Fried chicken with crispy crumbs'},
            {'category': 'Ayam & Bebek', 'name': 'Ayam Penyet', 'price': 28000, 'description': 'Smashed fried chicken with sambal'},
            {'category': 'Ayam & Bebek', 'name': 'Ayam Bakar Madu', 'price': 35000, 'description': 'Honey grilled chicken'},
            {'category': 'Ayam & Bebek', 'name': 'Bebek Goreng', 'price': 40000, 'description': 'Crispy fried duck'},
            {'category': 'Ayam & Bebek', 'name': 'Opor Ayam', 'price': 30000, 'description': 'Chicken in coconut milk curry'},
            {'category': 'Ayam & Bebek', 'name': 'Rendang Ayam', 'price': 38000, 'description': 'Chicken rendang curry'},
            
            # Sate & Bakar (Satay & Grilled)
            {'category': 'Sate & Bakar', 'name': 'Sate Ayam (10 tusuk)', 'price': 30000, 'description': 'Chicken satay with peanut sauce'},
            {'category': 'Sate & Bakar', 'name': 'Sate Kambing (10 tusuk)', 'price': 45000, 'description': 'Lamb satay with soy sauce'},
            {'category': 'Sate & Bakar', 'name': 'Sate Padang', 'price': 35000, 'description': 'Padang-style beef satay'},
            {'category': 'Sate & Bakar', 'name': 'Ikan Bakar', 'price': 50000, 'description': 'Grilled fish with sambal'},
            {'category': 'Sate & Bakar', 'name': 'Cumi Bakar', 'price': 45000, 'description': 'Grilled squid with soy sauce'},
            
            # Seafood
            {'category': 'Seafood', 'name': 'Udang Goreng Tepung', 'price': 55000, 'description': 'Crispy fried prawns'},
            {'category': 'Seafood', 'name': 'Cumi Goreng Tepung', 'price': 45000, 'description': 'Crispy fried calamari'},
            {'category': 'Seafood', 'name': 'Kepiting Saus Padang', 'price': 85000, 'description': 'Crab in spicy Padang sauce'},
            {'category': 'Seafood', 'name': 'Ikan Asam Manis', 'price': 48000, 'description': 'Sweet and sour fish'},
            {'category': 'Seafood', 'name': 'Udang Saus Tiram', 'price': 58000, 'description': 'Prawns in oyster sauce'},
            
            # Minuman (Beverages)
            {'category': 'Minuman', 'name': 'Es Teh Manis', 'price': 8000, 'description': 'Sweet iced tea'},
            {'category': 'Minuman', 'name': 'Es Jeruk', 'price': 10000, 'description': 'Fresh orange juice'},
            {'category': 'Minuman', 'name': 'Es Kelapa Muda', 'price': 15000, 'description': 'Young coconut ice'},
            {'category': 'Minuman', 'name': 'Es Cendol', 'price': 12000, 'description': 'Green rice flour jelly with coconut milk'},
            {'category': 'Minuman', 'name': 'Jus Alpukat', 'price': 18000, 'description': 'Avocado juice'},
            {'category': 'Minuman', 'name': 'Es Campur', 'price': 15000, 'description': 'Mixed ice dessert drink'},
            {'category': 'Minuman', 'name': 'Kopi Susu', 'price': 12000, 'description': 'Coffee with milk'},
            
            # Dessert
            {'category': 'Dessert', 'name': 'Pisang Goreng', 'price': 10000, 'description': 'Fried banana fritters'},
            {'category': 'Dessert', 'name': 'Klepon', 'price': 8000, 'description': 'Sweet rice balls with palm sugar'},
            {'category': 'Dessert', 'name': 'Dadar Gulung', 'price': 10000, 'description': 'Pandan crepes with coconut'},
            {'category': 'Dessert', 'name': 'Es Krim Kelapa', 'price': 15000, 'description': 'Coconut ice cream'},
            {'category': 'Dessert', 'name': 'Martabak Manis', 'price': 25000, 'description': 'Sweet thick pancake'},
        ]

        for item_data in items_data:
            cat = categories[item_data['category']]
            MenuItem.objects.create(
                category=cat,
                name=item_data['name'],
                price=item_data['price'],
                description=item_data['description']
            )
            self.stdout.write(f"  Created: {item_data['name']}")

        self.stdout.write(self.style.SUCCESS(
            f'\nMenu seeded! {MenuItem.objects.count()} items in {Category.objects.count()} categories.'
        ))
