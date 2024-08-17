from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Bid, AutomatedBid
from decimal import Decimal
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, ProductSerializer


class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response(status=204)


def calculate_min_bid_increment(product):
    latest_bid = Bid.objects.filter(
        product=product).first()

    if latest_bid:
        latest_bid_amount = Decimal(latest_bid.amount)
        current_price = Decimal(product.current_price)

        percentage_increment = latest_bid_amount * Decimal('0.01')
        fixed_increment = Decimal('200.00')

        min_increment = max(percentage_increment, fixed_increment)
    else:
        min_increment = Decimal('200.00')

    return min_increment


def process_automated_bids(product_id, user=None, max_bid=0, token=None):
    try:
        product = Product.objects.get(ItemID=product_id)
    except Product.DoesNotExist:
        print(f"Product with ID {product_id} does not exist.")
        return

    # Default user handling
    automated_bids = AutomatedBid.objects.filter(
        product=product, active=True).order_by('-max_bid', 'created_at')

    # If no automated bids exist, create one
    if not automated_bids:
        user = get_user(token)
        if user:
            AutomatedBid.objects.create(
                product=product,
                user=user,
                max_bid=max_bid,
                active=True,
                created_at=timezone.now()
            )
            automated_bids = AutomatedBid.objects.filter(
                product=product, active=True).order_by('-max_bid', 'created_at')
        else:
            print("No user provided for creating an automated bid.")
            return

    current_bid = Decimal(product.current_price)

    for auto_bid in automated_bids:
        if auto_bid.max_bid > current_bid:
            new_bid_amount = current_bid + Decimal('1.00')
            if new_bid_amount <= auto_bid.max_bid:
                Bid.objects.create(
                    product=product, user=auto_bid.user, amount=new_bid_amount)
                product.current_price = new_bid_amount
                product.save()
                current_bid = new_bid_amount
            else:
                # Deactivate the automated bid if it cannot place a valid bid
                auto_bid.active = False
                auto_bid.save()

        # Deactivate the automated bid if the max_bid is now less than or equal to the current bid
        if auto_bid.max_bid <= current_bid:
            auto_bid.active = False
            auto_bid.save()

    # Ensure that the product winner is set if no higher bids are possible
    if product.current_price == current_bid:
        product.winner = auto_bid.user
        product.save()


def get_user(token):
    try:
        token = Token.objects.get(key=token)
        user_id = token.user_id
        user = User.objects.get(id=user_id)
        return user
    except (Token.DoesNotExist, User.DoesNotExist, Exception):
        return None

@api_view(['POST'])
def automated_bids(request):
    product_id = request.data.get('product_id')
    max_bid = float(request.data.get('max_bid'))
    token = request.data.get('token')
    process_automated_bids(product_id, max_bid=max_bid, token=token)
    return Response({"success": "automated bid placed successfully."}, status=200)


@api_view(['GET'])
def get_product(request, product_id):
    try:
        product = Product.objects.get(ItemID=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)


@api_view(['POST'])
def place_bid(request):
    product_id = request.data.get('product_id')
    bid_amount = float(request.data.get('bid'))
    token = request.data.get('token')

    try:
        user = get_user(token)
        print(f'User: {user}')

        product = Product.objects.get(ItemID=product_id)
        print(product)
        new_bid = Bid.objects.create(
            product=product, user=user, amount=bid_amount
        )
        print(new_bid)
        product.current_price = bid_amount
        product.save()
        process_automated_bids(product_id, user=user)

        return Response({"success": "Bid placed successfully."}, status=200)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)
