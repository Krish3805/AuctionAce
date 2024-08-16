from django.db import models
from datetime import timedelta, datetime
from django.contrib.auth.models import User

class Category(models.Model):
    CategoryID = models.CharField(max_length=100, unique=True)
    CategoryName = models.CharField(max_length=255)
    ParentCategoryID = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.CategoryName

class Product(models.Model):
    ItemID = models.CharField(max_length=100, unique=True)
    ProductTitle = models.CharField(max_length=255)
    ProductDescription = models.TextField()
    MainImageURL = models.URLField()
    AllImagesURLs = models.JSONField()
    CategoryID = models.ForeignKey(Category, on_delete=models.CASCADE)
    ItemSpecifications = models.JSONField()
    EndTime = models.DateTimeField()
    winner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_products')
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.EndTime = datetime.now() + timedelta(minutes=float(self.starting_price))
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.ProductTitle
class Bid(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    def __str__(self):
        return f'{self.user.username} bid {self.amount} on {self.product.ProductTitle}'
     