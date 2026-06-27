from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, get_stats
from .views import CustomTokenObtainPairView

from .views import register, forgot_password, reset_password_confirm

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')  # ← basename ajouté

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', get_stats, name='stats'),
     # ... vos autres routes
    path('register/', register, name='register'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password-confirm/', reset_password_confirm, name='reset_password_confirm'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair')
]