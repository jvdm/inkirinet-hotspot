
from django.urls import path

from .apps import ContractsConfig
from .views import HomeView
from .views import LoginView


app_name = ContractsConfig.name

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login')
]
