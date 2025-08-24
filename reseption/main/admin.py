# main/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Product, ProductImage, OptionGroup, OptionVariant, RequestCall

# --- Инлайны для редактирования на странице Товара ---

class ProductImageInline(admin.TabularInline):
    """Позволяет добавлять картинки галереи прямо на странице товара."""
    model = ProductImage
    extra = 1

class OptionGroupInline(admin.TabularInline):
    """
    Показывает группы опций на странице товара и дает ссылку на их детальное редактирование.
    """
    model = OptionGroup
    extra = 1
    # Поля, которые будут видны на странице товара
    fields = ('name', 'option_type', 'edit_variants_link')
    # Делает поле со ссылкой нередактируемым
    readonly_fields = ('edit_variants_link',)
    # Не показывать вложенные варианты здесь, чтобы не было хаоса
    inlines = []
    
    def edit_variants_link(self, obj):
        """Создает ссылку на страницу редактирования этой группы опций, где можно управлять вариантами."""
        if obj.pk:
            # 'admin:main_optiongroup_change' - стандартное имя URL. 'main' - имя твоего приложения.
            url = reverse('admin:main_optiongroup_change', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Edit Variants</a>', url)
        return "Save first to add variants"
    
    edit_variants_link.short_description = 'Управление Вариантами'

# --- Основные классы Админки ---

@admin.register(RequestCall)
class RequestCallAdmin(admin.ModelAdmin):
    """Админка для Заявок."""
    list_display = ('name', 'phone', 'created_at')
    search_fields = ('name', 'phone', 'created_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для Товаров."""
    list_display = ('name', 'base_price', 'edit_link')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline, OptionGroupInline]
    fields = ('name', 'description', 'base_price')
    def edit_link(self, obj):
        """Создает ссылку на страницу редактирования этого же товара."""
        url = reverse('admin:main_product_change', args=[obj.pk])
        return format_html('<a href="{}">Edit This Product</a>', url)
    
    edit_link.short_description = 'Ссылка для ред.'

class OptionVariantInlineForGroup(admin.TabularInline):
    """Инлайн для редактирования вариантов на странице Группы Опций."""
    model = OptionVariant
    extra = 1

@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    """Админка для Групп Опций. Здесь удобно редактировать варианты."""
    list_display = ('name', 'product_link', 'option_type')
    search_fields = ('name',)
    list_filter = ('product',)
    inlines = [OptionVariantInlineForGroup]

    def product_link(self, obj):
        """Создает ссылку на связанный товар."""
        url = reverse('admin:main_product_change', args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
        
    product_link.short_description = 'Product Link'