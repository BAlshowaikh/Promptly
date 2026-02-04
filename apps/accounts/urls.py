from django.urls import path

# Imports form the DRF JWT library (Login and refresh views are alreday ready)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import RegisterView

app_name = "accounts" 

urlpatterns = [
    # Registration
    path("register/", RegisterView.as_view(), name="register"),
    
    # Login (use the built in views from DRF JWT)
    path("login/", TokenObtainPairView.as_view(), name="login"),
    
    # Refresh the token auto (use the built in views from DRF JWT)
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]