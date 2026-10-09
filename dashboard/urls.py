from django.urls import path
from . import views

urlpatterns = [
    path('top-buyers/', views.top_buyers, name='dashboard.top_buyers'),
]