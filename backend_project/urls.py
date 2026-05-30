"""
URL configuration for backend_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from custom_auth.views import (
    RegisterUserView, LoginUserView, LogoutUserView, UserProfileView, 
    AdminRulesView, MockDocumentView, MockAnalyticsView
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/auth/register/', RegisterUserView.as_view(), name='auth_register'),
    path('api/auth/login/', LoginUserView.as_view(), name='login'),
    path('api/auth/logout/', LogoutUserView.as_view(), name='logout'),
    path('api/users/me/', UserProfileView.as_view(), name='user_profile'),
    
    path('api/admin/rules/', AdminRulesView.as_view(), name='admin_rules'),
    
    path('api/v1/documents/', MockDocumentView.as_view(), name='mock_documents'),
    path('api/v1/analytics/', MockAnalyticsView.as_view(), name='mock_analytics'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
