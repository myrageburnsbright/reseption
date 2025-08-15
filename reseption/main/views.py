
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
    
    try:
        page_number = int(request.GET.get('page', 1))
        if page_number < 1:
            page_number = 1
    except ValueError:
        return HttpResponse('')
    
    offset = (page_number - 1) * PRODUCTS_PER_PAGE
    limit = offset + PRODUCTS_PER_PAGE

    products = Product.objects.order_by('id')

    current_min_price = request.GET.get('price_min')
    current_max_price = request.GET.get('price_max')
    if current_min_price:
        products = products.filter(base_price__gte=current_min_price)
    
    if current_max_price:
        products = products.filter(base_price__lte=current_max_price)

    products = products[offset:limit]
    
    if not products:
        return HttpResponse('') # Пустой ответ, чтобы JS спрятал кнопку
    context = {'products': products}
    
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
        'main_image': main_image.image if main_image.image else None,
    }
    return render(request, 'main/product_detail.html', context)

from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Min, Max, Prefetch
from django.template.loader import render_to_string
from urllib.parse import urlencode

from main.models import Product, ProductImage, OptionGroup, OptionVariant

PER_PAGE = 9


def _parse_int(val, default):
    try:
        return int(str(val).replace(' ', '').replace(',', ''))
    except Exception:
        return default


def _get_all_colors():
    # Все уникальные значения цветов (OptionGroup name="Colors")
    return list(
        OptionVariant.objects
        .filter(group__name='Colors')
        .values_list('value', flat=True)
        .distinct()
        .order_by('value')
    )


def _filter_products(request: HttpRequest):
    """
    Возвращает (qs, price_min_all, price_max_all, q, sort, pmin, pmax, selected_colors)
    """
    base_qs = (
        Product.objects.all()
        .prefetch_related(
            Prefetch('gallery_images', queryset=ProductImage.objects.order_by('id')),
            Prefetch('options', queryset=OptionGroup.objects.filter(name='Colors').prefetch_related('variants')),
        )
    )

    # Глобальные min/max (по всем продуктам)
    aggr = Product.objects.aggregate(price_min_all=Min('base_price'), price_max_all=Max('base_price'))
    price_min_all = int(aggr['price_min_all'] or 0)
    price_max_all = int(aggr['price_max_all'] or 0)

    # Поиск
    q = request.GET.get('q', '').strip()
    if q:
        base_qs = base_qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    # Цена
    pmin = request.GET.get('pmin')
    pmax = request.GET.get('pmax')
    pmin = _parse_int(pmin, price_min_all)
    pmax = _parse_int(pmax, price_max_all)
    # Кламп и исправление порядка
    pmin = max(price_min_all, min(pmin, price_max_all))
    pmax = max(price_min_all, min(pmax, price_max_all))
    if pmin > pmax:
        pmin, pmax = pmax, pmin

    base_qs = base_qs.filter(base_price__gte=pmin, base_price__lte=pmax)

    # Цвета (множественный выбор)
    selected_colors = [c.strip() for c in request.GET.getlist('color') if c.strip()]
    if selected_colors:
        base_qs = base_qs.filter(options__name='Colors', options__variants__value__in=selected_colors).distinct()

    # Сортировка
    sort = request.GET.get('sort', 'default')
    if sort == 'price-asc':
        base_qs = base_qs.order_by('base_price', 'name')
    elif sort == 'price-desc':
        base_qs = base_qs.order_by('-base_price', 'name')
    elif sort == 'name-asc':
        base_qs = base_qs.order_by('name')
    elif sort == 'name-desc':
        base_qs = base_qs.order_by('-name')
    else:
        # как по умолчанию в Meta модели Product (ordering=['name'])
        pass

    return base_qs, price_min_all, price_max_all, q, sort, pmin, pmax, selected_colors


def _qs_without(request: HttpRequest, remove_keys=(), remove_color_value=None):
    """
    Возвращает строку querystring без указанных ключей и/или без конкретного значения цвета.
    """
    qd = request.GET.copy()

    # Удаление конкретного значения color=...
    if remove_color_value is not None:
        colors = qd.getlist('color')
        colors = [c for c in colors if c != remove_color_value]
        if 'color' in qd:
            del qd['color']
        if colors:
            qd.setlist('color', colors)

    # Удаление указанных ключей
    for k in remove_keys:
        if k in qd:
            del qd[k]

    # Сброс страницы при любом изменении
    if 'page' in qd:
        del qd['page']

    return qd.urlencode()


def catalog(request: HttpRequest):
    qs, price_min_all, price_max_all, q, sort, pmin, pmax, selected_colors = _filter_products(request)

    # Пагинация
    page_number = _parse_int(request.GET.get('page', 1), 1)
    paginator = Paginator(qs, PER_PAGE)
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages if paginator.num_pages else 1)

    has_more = page_obj.has_next()
    next_page = page_obj.next_page_number() if has_more else None

    # Справочник всех доступных цветов
    colors_all = _get_all_colors()

    # QS для снятия фильтров
    qs_remove_pmin = _qs_without(request, remove_keys=('pmin',))
    qs_remove_pmax = _qs_without(request, remove_keys=('pmax',))
    qs_clear_all = _qs_without(request, remove_keys=('pmin', 'pmax', 'sort', 'q', 'color', 'page'))

    selected_colors_with_qs = [(c, _qs_without(request, remove_color_value=c)) for c in selected_colors]

    ctx = {
        'products': page_obj.object_list,
        'has_more': has_more,
        'next_page': next_page,

        'q': q,
        'sort': sort,

        'price_min_all': price_min_all,
        'price_max_all': price_max_all,
        'pmin': pmin,
        'pmax': pmax,

        'colors_all': colors_all,
        'selected_colors': selected_colors,
        'selected_colors_with_qs': selected_colors_with_qs,

        'qs_remove_pmin': qs_remove_pmin,
        'qs_remove_pmax': qs_remove_pmax,
        'qs_clear_all': qs_clear_all,
    }
    return render(request, 'main/catalog.html', ctx)


def catalog_load_more(request: HttpRequest):
    """
    AJAX endpoint для кнопки "Load more".
    """
    qs, _, _, _, _, _, _, _ = _filter_products(request)

    page_number = _parse_int(request.GET.get('page', 2), 2)
    paginator = Paginator(qs, PER_PAGE)
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages if paginator.num_pages else 1)

    html = render_to_string('main/_product_cards.html', {'products': page_obj.object_list}, request=request)
    data = {
        'html': html,
        'has_more': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None
    }
    return JsonResponse(data)