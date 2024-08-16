import csv
from django.core.management.base import BaseCommand
from bid.models import Product, Category


class Command(BaseCommand):
    help = 'Load products and categories from CSV files into the database'

    def handle(self, *args, **kwargs):
        self.import_categories()
        self.import_products()

    def import_categories(self):
        with open('data/categories1.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                category, created = Category.objects.get_or_create(
                    CategoryID=row['CategoryID'],
                    defaults={
                        'CategoryName': row['CategoryName'],
                    }
                )
                if not created:
                    category.CategoryName = row['CategoryName']
                    category.save()

        self.stdout.write(self.style.SUCCESS(
            'Categories imported successfully'))

    def import_products(self):
        with open('data/products1.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                category = Category.objects.get(CategoryID=row['CategoryID'])
                product, created = Product.objects.get_or_create(
                    ItemID=row['ItemID'],
                    defaults={
                        'ProductTitle': row['ProductTitle'],
                        'starting_price': row['ProductPrice'],
                        'current_price': row['ProductPrice'],
                        'ProductDescription': row['ProductDescription'],
                        'MainImageURL': row['MainImageURL'],
                        'AllImagesURLs': row['AllImagesURLs'],
                        'CategoryID': category,
                        'ItemSpecifications': row['ItemSpecifications'],
                    }
                )
                if not created:
                    product.ProductTitle = row['ProductTitle']
                    product.starting_price = row['ProductPrice']
                    product.current_price = row['ProductPrice']
                    product.ProductDescription = row['ProductDescription']
                    product.MainImageURL = row['MainImageURL']
                    product.AllImagesURLs = row['AllImagesURLs']
                    product.CategoryID = category
                    product.ItemSpecifications = row['ItemSpecifications']
                    product.save()

        self.stdout.write(self.style.SUCCESS('Products imported successfully'))
