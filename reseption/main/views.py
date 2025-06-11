
from django.shortcuts import render
from django.db.models import Min, Max
from .models import Product
from django.http import HttpResponse
from decimal import Decimal
# Create your views here.
def index(request):
    context = {}

    return render(request, 'main/index.html', context=context)

PRODUCTS_PER_PAGE = 21

def katalog(request):
    products_queryset = Product.objects.order_by('id')

    # 2. Получаем текущие значения фильтров из GET-запроса
    #    request.GET.get('price_min') вернет значение или None, если параметра нет
    current_min_price = request.GET.get('price_min')
    current_max_price = request.GET.get('price_max')

    # 3. Фильтруем товары, если значения цен указаны
    if current_min_price:
        # __gte означает "greater than or equal" (больше или равно)
        products_queryset = products_queryset.filter(base_price__gte=current_min_price)
    
    if current_max_price:
        # __lte означает "less than or equal" (меньше или равно)
        products_queryset = products_queryset.filter(base_price__lte=current_max_price)

    # 4. Вычисляем общий минимальный и максимальный ценник для всех товаров
    #    Это нужно, чтобы задать границы для ползунка или полей ввода
    price_range = Product.objects.aggregate(
        min_price=Min('base_price'),
        max_price=Max('base_price')
    )
    print(products_queryset.all().count(), "count")
    context = {
        'products': products_queryset[:PRODUCTS_PER_PAGE],
        'min_price_overall': price_range.get('min_price'),
        'max_price_overall': price_range.get('max_price'),
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
    product = Product.objects.get(id=product_id)
    
    context = {'product': product}

    return render(request, 'main/product_detail.html', context=context)