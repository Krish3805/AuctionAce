from django.contrib import admin
from .models import Category, Product, Bid, AutomatedBid

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('CategoryID', 'CategoryName', 'ParentCategoryID')
    search_fields = ('CategoryName', 'CategoryID')
    list_filter = ('ParentCategoryID',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('ItemID', 'ProductTitle', 'CategoryID', 'starting_price', 'current_price', 'EndTime', 'winner')
    search_fields = ('ProductTitle', 'ItemID', 'CategoryID__CategoryName')
    list_filter = ('CategoryID', 'EndTime')
    ordering = ('-EndTime',)  # Sort by EndTime in descending order

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'amount', 'min_bid_increment')
    search_fields = ('product__ProductTitle', 'user__username')
    list_filter = ('product',)

@admin.register(AutomatedBid)
class AutomatedBidAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'max_bid', 'active', 'created_at')
    search_fields = ('product__ProductTitle', 'user__username')
    list_filter = ('product', 'active', 'created_at')
    ordering = ('-created_at',)  # Sort by created_at in descending order
