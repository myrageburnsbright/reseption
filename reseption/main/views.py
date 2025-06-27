
from django.shortcuts import render, get_object_or_404
from django.db.models import Min, Max
from .models import Product
from django.http import HttpResponse
from decimal import Decimal
from django.views.generic import DetailView

def robots_txt(request):
    content = "User-agent: *\nDisallow: /\n"
    return HttpResponse(content, content_type="text/plain")

# Create your views here.
def index(request):
    context = {}

    return render(request, 'main/index.html', context=context)

PRODUCTS_PER_PAGE = 21

def katalog(request):
    products_queryset = Product.objects.order_by('id')
    
    price_range = Product.objects.aggregate(
        min_price=Min('base_price'),
        max_price=Max('base_price')
    )
    min_price_overall = price_range.get('min_price')
    max_price_overall = price_range.get('max_price')

    current_min_price = request.GET.get('price_min', min_price_overall)
    current_max_price = request.GET.get('price_max', max_price_overall)

    if current_min_price:
        products_queryset = products_queryset.filter(base_price__gte=current_min_price)
    
    if current_max_price:
        products_queryset = products_queryset.filter(base_price__lte=current_max_price)

    print(products_queryset.all().count(), "count")
    context = {
        'products': products_queryset[:PRODUCTS_PER_PAGE],
        'min_price_overall': min_price_overall,
        'max_price_overall': max_price_overall,
        'current_min_price': current_min_price,
        'current_max_price': current_max_price,
        'show_more_btn': len(products_queryset) > PRODUCTS_PER_PAGE
    }

    return render(request, 'main/katalog.html', context=context)

def load_more_products(request):
    """
    Эта вью-функция вызывается только через AJAX (JavaScript).
    Она возвращает HTML-фрагмент со следующей порцией товаров.
    """
    # Получаем номер страницы из GET-параметра ?page=...
    try:
        page_number = int(request.GET.get('page', 1))
        if page_number < 1:
            page_number = 1
    except ValueError:
        return HttpResponse('') # Если пришло не число, ничего не возвращаем

    # Вычисляем смещение (offset) для среза
    offset = (page_number - 1) * PRODUCTS_PER_PAGE
    limit = offset + PRODUCTS_PER_PAGE


    # Получаем следующую порцию товаров с помощью среза
    products = Product.objects.order_by('id')

    current_min_price = request.GET.get('price_min')
    current_max_price = request.GET.get('price_max')
    print(current_min_price, current_max_price, "dassaddsadas")
    # 3. Фильтруем товары, если значения цен указаны
    if current_min_price:
        # __gte означает "greater than or equal" (больше или равно)
        products = products.filter(base_price__gte=current_min_price)
    
    if current_max_price:
        # __lte означает "less than or equal" (меньше или равно)
        products = products.filter(base_price__lte=current_max_price)

    products = products[offset:limit]
    # 4. Вычисляем общий минимальный и максимальный ценник для всех товаров
    # Если срез пустой, значит, товары закончились
    if not products:
        return HttpResponse('') # Пустой ответ, чтобы JS спрятал кнопку
    context = {'products': products}
    # Рендерим маленький шаблон только с новыми карточками.
    # Обрати внимание, что теперь мы передаем переменную 'products', а не 'products_page'.
    return render(request, 'main/_product_cards.html', context=context)
    
def product_detail(request, product_id):
    """
    Displays the product detail page for a single product.
    """

    product = get_object_or_404(
        Product.objects.prefetch_related(
            'gallery_images',
            'options__variants' 
        ),
        id=product_id
    )

    main_image = product.gallery_images.first()

    context = {
        'product': product,
        'main_image_url': main_image.image_url if main_image else None,
    }
    return render(request, 'main/product_detail.html', context)
