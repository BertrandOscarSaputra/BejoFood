"""
Management command to create sample menu data.
Usage: python manage.py seed_menu
"""
from django.core.management.base import BaseCommand
from menu.models import Category, MenuItem


class Command(BaseCommand):
    help = 'Seed database with sample menu data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample menu data...')

        # Categories
        categories_data = [
            {'name': 'Appetizers', 'emoji': '🥗', 'order': 1},
            {'name': 'Main Courses', 'emoji': '🍽️', 'order': 2},
            {'name': 'Burgers', 'emoji': '🍔', 'order': 3},
            {'name': 'Pizza', 'emoji': '🍕', 'order': 4},
            {'name': 'Beverages', 'emoji': '🥤', 'order': 5},
            {'name': 'Desserts', 'emoji': '🍰', 'order': 6},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'emoji': cat_data['emoji'], 'order': cat_data['order']}
            )
            categories[cat_data['name']] = cat
            status = 'Created' if created else 'Exists'
            self.stdout.write(f"  {status}: {cat}")

        # Menu items
        items_data = [
            # Appetizers
            {'category': 'Appetizers', 'name': 'Spring Rolls', 'price': 120, 'description': 'Crispy vegetable spring rolls with sweet chili sauce'},
            {'category': 'Appetizers', 'name': 'Chicken Wings', 'price': 180, 'description': 'Buffalo style chicken wings with blue cheese dip'},
            {'category': 'Appetizers', 'name': 'Nachos Supreme', 'price': 200, 'description': 'Loaded nachos with cheese, jalapeños, and salsa'},
            
            # Main Courses
            {'category': 'Main Courses', 'name': 'Grilled Chicken', 'price': 280, 'description': 'Herb-marinated grilled chicken breast with vegetables'},
            {'category': 'Main Courses', 'name': 'Beef Steak', 'price': 450, 'description': '200g premium beef steak with mushroom sauce'},
            {'category': 'Main Courses', 'name': 'Fish & Chips', 'price': 320, 'description': 'Beer-battered fish with crispy fries and tartar sauce'},
            {'category': 'Main Courses', 'name': 'Pasta Carbonara', 'price': 250, 'description': 'Creamy pasta with bacon, egg, and parmesan'},
            
            # Burgers
            {'category': 'Burgers', 'name': 'Classic Burger', 'price': 180, 'description': 'Beef patty, lettuce, tomato, onion, pickles'},
            {'category': 'Burgers', 'name': 'Cheese Burger', 'price': 200, 'description': 'Classic burger with melted cheddar cheese'},
            {'category': 'Burgers', 'name': 'Bacon Deluxe', 'price': 250, 'description': 'Double patty with bacon, cheese, and special sauce'},
            {'category': 'Burgers', 'name': 'Mushroom Swiss', 'price': 230, 'description': 'Beef patty with sautéed mushrooms and swiss cheese'},
            
            # Pizza
            {'category': 'Pizza', 'name': 'Margherita', 'price': 280, 'description': 'Classic tomato sauce, mozzarella, and fresh basil'},
            {'category': 'Pizza', 'name': 'Pepperoni', 'price': 320, 'description': 'Loaded with pepperoni and mozzarella cheese'},
            {'category': 'Pizza', 'name': 'Hawaiian', 'price': 300, 'description': 'Ham, pineapple, and mozzarella'},
            {'category': 'Pizza', 'name': 'BBQ Chicken', 'price': 350, 'description': 'BBQ sauce, grilled chicken, onions, and cilantro'},
            
            # Beverages
            {'category': 'Beverages', 'name': 'Iced Tea', 'price': 60, 'description': 'Refreshing house-brewed iced tea'},
            {'category': 'Beverages', 'name': 'Fresh Lemonade', 'price': 80, 'description': 'Freshly squeezed lemonade'},
            {'category': 'Beverages', 'name': 'Mango Shake', 'price': 120, 'description': 'Creamy mango milkshake'},
            {'category': 'Beverages', 'name': 'Coffee', 'price': 100, 'description': 'Hot brewed coffee'},
            {'category': 'Beverages', 'name': 'Soda', 'price': 50, 'description': 'Coke, Sprite, or Royal'},
            
            # Desserts
            {'category': 'Desserts', 'name': 'Chocolate Cake', 'price': 150, 'description': 'Rich chocolate layer cake'},
            {'category': 'Desserts', 'name': 'Cheesecake', 'price': 180, 'description': 'New York style cheesecake'},
            {'category': 'Desserts', 'name': 'Ice Cream', 'price': 80, 'description': 'Two scoops of your choice'},
            {'category': 'Desserts', 'name': 'Halo-Halo', 'price': 120, 'description': 'Filipino shaved ice dessert'},
        ]

        for item_data in items_data:
            cat = categories[item_data['category']]
            item, created = MenuItem.objects.get_or_create(
                category=cat,
                name=item_data['name'],
                defaults={
                    'price': item_data['price'],
                    'description': item_data['description']
                }
            )
            if created:
                self.stdout.write(f"  Created: {item}")

        self.stdout.write(self.style.SUCCESS(f'\nMenu seeded! {MenuItem.objects.count()} items in {Category.objects.count()} categories.'))
