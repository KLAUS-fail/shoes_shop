from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('add/', views.order_add, name='order_add'),
    path('<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('<int:pk>/status/', views.order_status_update, name='order_status_update'),
]