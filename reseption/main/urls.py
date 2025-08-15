
from django.contrib import admin
from django.urls import path, include
from .views import catalog, catalog_load_more
from main import views
app_name = 'main'

urlpatterns = [
    path("robots.txt", views.robots_txt),
    path('', views.index, name='index'),
    path('katalog/', views.katalog, name='katalog'),
    path('load_more_products/', views.load_more_products, name='load_more_products'),
    path('product_detail/<int:product_id>', views.product_detail, name='product_detail'),
    path('catalog/', catalog, name='catalog'),
    path('catalog/load-more/', catalog_load_more, name='catalog_load_more'),
]
