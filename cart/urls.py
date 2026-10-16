from django.urls import path
from . import views
urlpatterns = [
    path("popularity/", views.popularity_map, name="cart.popularity_map"),
    path('', views.index, name='cart.index'),
    path('<int:id>/add/', views.add, name='cart.add'),
    path('clear/', views.clear, name='cart.clear'),
    path('purchase/', views.purchase, name='cart.purchase'),
]
