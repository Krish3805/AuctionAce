from django.contrib import admin
from .models import Category, Product,Bid
# Register your models here.
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Bid)
