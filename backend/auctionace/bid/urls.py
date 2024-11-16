from django.urls import path
from .import views

urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('place-bid/', views.PlaceBidView.as_view(), name='place-bid'),
    path('automated-bid/', views.AutomatedBidsView.as_view(), name='automated-bid'),
    path('get-product/<int:product_id>/',
         views.get_product, name='get_product'),
    path('user-bids/', views.UserBidsView.as_view(), name='user-bids'),
    path('orders/', views.UserOrdersView.as_view(), name='user-orders'),
    path('orders/<int:order_id>/',
         views.OrderDetailView.as_view(), name='order_detail'),
    path('checkout/<int:product_id>/',
         views.CheckoutView.as_view(), name='checkout'),
    path('user-profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('create-payment-intent/<int:order_id>/',
         views.CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('confirm-payment/<int:order_id>/',
         views.ConfirmPaymentView.as_view(), name='confirm-payment'),
    path('contact/', views.contact_us, name='contact_us'),

]
