from django.urls import path
from . import views
urlpatterns = [
    path('signup/', views.SignInForm.as_view(), name='signup'),
    path('login/', views.LoginForm.as_view(), name='login'),
    path('logout/', views.LogoutForm.as_view(), name='logout'),
]