from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Bid
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
        product=product).order_by('-created_at').first()

    if latest_bid:
        latest_bid_amount = Decimal(latest_bid.amount)
        current_price = Decimal(product.current_price)

        percentage_increment = latest_bid_amount * Decimal('0.01')
        fixed_increment = Decimal('200.00')

        min_increment = max(percentage_increment, fixed_increment)
    else:
        min_increment = Decimal('200.00')

    return min_increment


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
    token = request.data.get('token')  # Token passed from frontend

    try:
        token = Token.objects.get(key=token)
        user_id = token.user_id

        # Fetch the user
        user = User.objects.get(id=user_id)
        print(f'User: {user}')

        product = Product.objects.get(ItemID=product_id)
        print(product)
        new_bid = Bid.objects.create(
            product=product, user=user, amount=bid_amount
        )
        print(new_bid)
        product.current_price = bid_amount
        product.save()

        return Response({"success": "Bid placed successfully."}, status=200)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)
