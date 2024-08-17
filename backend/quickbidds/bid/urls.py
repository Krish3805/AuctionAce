from django.urls import path
from .views import LoginView, LogoutView, ProductListView, RegisterView, get_product, place_bid,automated_bids

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('place-bid/', place_bid, name='place-bid'),
    path('automated-bid/',automated_bids,name='automated-bid'),
    path('get-product/<int:product_id>/', get_product, name='get_product'),

]
