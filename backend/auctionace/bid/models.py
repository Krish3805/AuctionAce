from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags


class Category(models.Model):
    CategoryID = models.CharField(max_length=100, unique=True)
    CategoryName = models.CharField(max_length=255)
    ParentCategoryID = models.CharField(max_length=100, blank=True)

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
    STATUS_CHOICES = [
        ('live', 'Live'),
        ('sold', 'Sold'),
        ('unsold', 'Unsold'),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='live')

    def update_winner(self):
        GREEN = '\033[92m'
        RED = '\033[91m'
        RESET = '\033[0m'

        if timezone.now() >= self.EndTime:
            highest_bid = self.bids.order_by('-amount').first()
            if highest_bid:
                self.winner = highest_bid.user
                self.current_price = highest_bid.amount  # Update current price to winning bid
                
                print(f"{GREEN}{self.ItemID} has been sold to {self.winner}{RESET}")
                self.status = 'sold'
            else:
                self.status = 'unsold'
                print(f"{RED}{self.ItemID} has been unsold{RESET}")
        else:
            self.status = 'live'

    def save(self, *args, **kwargs):
        if not self.pk:
            # For new products, set the EndTime based on the starting price
            self.EndTime = datetime.now() + timedelta(seconds=float(self.starting_price) - 24500)
        else:
            # When updating a product, check the winner
            self.update_winner()

        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.ProductTitle

class Bid(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_bid_increment = models.DecimalField(
        max_digits=10, decimal_places=2, default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f'{self.user.username} bid {self.amount} on {self.product.ProductTitle}'


class AutomatedBid(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    max_bid = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.ProductTitle} - {self.user.username} - {self.status}'

    def save(self, *args, **kwargs):
        # Check if status is changing to 'confirmed'
        if self.pk:
            old_status = Order.objects.get(pk=self.pk).status
            if old_status != 'confirmed' and self.status == 'confirmed':
                pass

        super(Order, self).save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profile')
    phone = models.CharField(max_length=10)
    address = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
