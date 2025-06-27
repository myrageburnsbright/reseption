
from django.contrib import admin
from django.urls import path, include
from main import views
app_name = 'main'

urlpatterns = [
    path("robots.txt", views.robots_txt),
    path('', views.index, name='index'),
    path('katalog/', views.katalog, name='katalog'),
    path('load_more_products/', views.load_more_products, name='load_more_products'),
    path('product_detail/<int:product_id>', views.product_detail, name='product_detail'),
]
