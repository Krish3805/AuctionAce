from rest_framework import serializers
from .models import Product, Category, Bid
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data['username'], validated_data['email'], validated_data['password'])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid Credentials")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['CategoryID', 'CategoryName', 'ParentCategoryID']


class BidSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Bid
        fields = ['user', 'amount', 'min_bid_increment']


class ProductSerializer(serializers.ModelSerializer):
    CategoryID = CategorySerializer()
    bids = BidSerializer(many=True, read_only=True)
    highest_bidder = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'ItemID', 'ProductTitle', 'current_price', 'starting_price', 'ProductDescription',
            'MainImageURL', 'AllImagesURLs', 'CategoryID', 'ItemSpecifications', 'EndTime', 'bids','highest_bidder'
        ]

    def get_highest_bidder(self, obj):
        highest_bid = obj.bids.order_by('-amount').first()

        if highest_bid:
            return {
                'user': highest_bid.user.username,
                'amount': highest_bid.amount
            }
        return None
