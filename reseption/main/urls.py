
from django.contrib import admin
from django.urls import path, include
from .views import catalog, catalog_load_more, about, privacy
from main import views
app_name = 'main'

urlpatterns = [
    path("robots.txt", views.robots_txt),
    path('', views.index, name='index'),
    path('product_detail/<int:product_id>', views.product_detail, name='product_detail'),
    path('catalog/', catalog, name='catalog'),
    path('catalog/load-more/', catalog_load_more, name='catalog_load_more'),
    path('product-pdf/', views.product_onepager_pdf, name='product_onepager_pdf'),
    path('about/', about, name='about'),
    path('privacy/', privacy, name='privacy'),
]
