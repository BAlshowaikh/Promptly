from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # LEARNING URLS
    path("api/learning/", include("apps.learning.urls")),
    
    # AUTH URLS
    path("api/auth/", include("apps.accounts.urls")),
]
