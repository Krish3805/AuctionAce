import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated

from .models import Product, Bid, AutomatedBid, Order, UserProfile
from decimal import Decimal
from .serializers import UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer, ProductSerializer, OrderSerializer
import stripe



class ProductListView(APIView):
    permission_classes = []

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)

    def put(self, request):
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user)
        serializer = UserProfileUpdateSerializer(
            user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UserBidsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        bids = Bid.objects.filter(user=user).select_related('product')
        products = []
        added_product_ids = set()
        for bid in bids:
            product = bid.product
            if product.id not in added_product_ids and not Order.objects.filter(user=user, product=product).exists():
                product_data = ProductSerializer(product).data
                products.append(product_data)
                added_product_ids.add(product.id)

        return Response(products)


class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user).select_related('product')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if order.status != 'pending':
                return Response({'error': 'Order has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

            intent = stripe.PaymentIntent.create(
                amount=int(order.amount * 100),
                currency='usd',
                metadata={'order_id': order.id}
            )
            return Response({
                'clientSecret': intent['client_secret']
            })

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class ConfirmPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            # Fetch the order
            order = Order.objects.get(id=order_id, user=request.user)
            payment_intent_id = request.data.get('payment_intent_id')

            # Retrieve the PaymentIntent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if payment_intent.status == 'succeeded':
                order.status = 'confirmed'
                order.save()

                customer_email = request.user.email
                stripe_customer_id = getattr(
                    request.user, 'stripe_customer_id', None)

                if stripe_customer_id:
                    customer = stripe.Customer.modify(
                        stripe_customer_id,
                        email=customer_email,
                    )
                else:
                    customer = stripe.Customer.create(
                        email=customer_email,
                        name=request.user.username,
                    )
                    request.user.stripe_customer_id = customer.id
                    request.user.save()

                return Response({'message': 'Payment confirmed'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({'error': 'Stripe error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        user = request.user

        try:
            product = Product.objects.get(ItemID=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if product.winner != user:
            return Response({'error': 'User is not the winner'}, status=status.HTTP_403_FORBIDDEN)

        # Create an order
        order = Order.objects.create(
            user=user, product=product, amount=product.current_price, status='pending')
        product.status = 'sold'
        product.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def calculate_min_bid_increment(product):
    min_increment = max(
        int(product.current_price - product.starting_price), 200)
    return min_increment


class AutomatedBidsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        max_bid = request.data.get('max_bid')

        try:
            user = request.user
            process_automated_bids(product_id, user=user,
                                   max_bid=Decimal(max_bid))
            return Response({"success": "Automated bid placed successfully."}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


def process_automated_bids(product_id, user=None, max_bid=0):
    try:
        product = Product.objects.get(ItemID=product_id)
    except Product.DoesNotExist:
        return

    automated_bids = AutomatedBid.objects.filter(
        product=product, active=True).order_by('-max_bid', 'created_at')

    # If there are no automated bids, create one
    if not automated_bids:
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
            return

    current_bid = Decimal(product.current_price)

    for auto_bid in automated_bids:
        if auto_bid.max_bid > current_bid:
            new_bid_amount = current_bid + calculate_min_bid_increment(product)
            if new_bid_amount <= auto_bid.max_bid:
                Bid.objects.create(
                    product=product, user=auto_bid.user, amount=new_bid_amount)
                product.current_price = new_bid_amount
                product.save()
                current_bid = new_bid_amount
            else:
                auto_bid.active = False
                auto_bid.save()

        if auto_bid.max_bid <= current_bid:
            auto_bid.active = False
            auto_bid.save()


@api_view(['GET'])
def get_product(request, product_id):
    try:
        product = Product.objects.get(ItemID=product_id)

        product_serializer = ProductSerializer(product)

        suggested_products = Product.objects.filter(
            CategoryID=product.CategoryID).exclude(ItemID=product_id)

        suggested_products_serializer = ProductSerializer(
            suggested_products, many=True)

        return Response({
            'product': product_serializer.data,
            'suggested_products': suggested_products_serializer.data
        })

    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)


class PlaceBidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        bid_amount = request.data.get('bid')

        try:
            user = request.user
            product = Product.objects.get(ItemID=product_id)
            new_bid = Bid.objects.create(
                product=product, user=user, amount=Decimal(bid_amount)
            )
            product.current_price = Decimal(bid_amount)
            product.save()

            # Process automated bids after placing the new bid
            process_automated_bids(product_id, user=user)

            return Response({"success": "Bid placed successfully."}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def contact_us(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')

        email_subject = f"New Contact Form Submission: {subject}"
        email_message = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"

        send_mail(
            email_subject,
            email_message,
            email,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )

        return JsonResponse({'status': 'success', 'message': 'Email sent successfully'})
    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)
