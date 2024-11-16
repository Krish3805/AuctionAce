from rest_framework import serializers
from .models import Product, Category, Bid, Order, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'user']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['CategoryID', 'CategoryName', 'ParentCategoryID']


class BidSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Bid
        fields = ['user', 'amount', 'min_bid_increment', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    CategoryID = CategorySerializer()
    bids = BidSerializer(many=True, read_only=True)
    highest_bidder = serializers.SerializerMethodField()
    min_bid_increment = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'ItemID', 'ProductTitle', 'current_price', 'starting_price', 'ProductDescription', 'status',
            'MainImageURL', 'AllImagesURLs', 'CategoryID', 'ItemSpecifications', 'EndTime', 'bids',
            'highest_bidder', 'min_bid_increment'
        ]

    def get_highest_bidder(self, obj):
        highest_bid = obj.bids.order_by('-amount').first()
        if highest_bid:
            return {
                'user': highest_bid.user.username,
                'user_id': highest_bid.user.id,
                'amount': highest_bid.amount
            }
        return None

    def get_min_bid_increment(self, obj):
        return calculate_min_bid_increment(obj)


def calculate_min_bid_increment(product):
    min_increment = max(
        int(product.current_price - product.starting_price), 200)
    return min_increment


class OrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    user_profile = UserProfileSerializer(source='user.profile', read_only=True)  # Include user profile details
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'product', 'user', 'user_profile', 'status', 'order_date', 'amount']
