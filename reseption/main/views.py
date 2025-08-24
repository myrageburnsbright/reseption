import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Min, Max
from .models import Product
from django.http import HttpResponse, JsonResponse, HttpRequest, HttpResponseBadRequest
from decimal import Decimal
from django.views.generic import DetailView
from django.template.loader import render_to_string
from django.db.models import Q, Prefetch, Min, Max
from django.core.paginator import Paginator, EmptyPage
from .models import Product, ProductImage, OptionGroup, RequestCall
from decimal import Decimal
from io import BytesIO
from urllib.request import urlopen

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def robots_txt(request):
    content = "User-agent: *\nDisallow: /\n"
    return HttpResponse(content, content_type="text/plain")

# Create your views here.
def index(request):
    context = {}

    return render(request, 'main/index.html', context=context)

def about(request):
    context = {}

    return render(request, 'main/about.html', context=context)

def privacy(request):
    context = {}

    return render(request, 'main/privacypolicy.html', context=context)
    
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

def callform(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        cc = request.POST.get("cc")
        cc_phone = str(cc or "") + str(phone or "")
        RequestCall.objects.create(name=name, phone= cc_phone)
        return JsonResponse({"name": name, "phone": phone, "cc": cc})
    

PER_PAGE = 12

def _parse_int(v, default):
    try:
        return int(str(v).replace(' ', '').replace(',', ''))
    except Exception:
        return int(default)

def _get_all_colors():
    """
    Собрать все уникальные значения цветов из ВСЕХ групп с именем 'Chose color'
    """
    groups = OptionGroup.objects.filter(name='Chose color').prefetch_related('variants')
    seen, out = set(), []
    for g in groups:
        for v in g.variants.all():
            val = (v.value or '').strip()
            if not val:
                continue
            if val not in seen:
                seen.add(val)
                out.append(val)
    # Стабильная сортировка по алфавиту (без учета регистра)
    out.sort(key=lambda s: s.lower())
    return out

def _filter_products(request: HttpRequest):
    """
    Возвращает (qs, price_min_all, price_max_all, q, sort, pmin, pmax, selected_colors)
    """
    base_qs = (
        Product.objects.all()
        .prefetch_related(
            Prefetch('gallery_images', queryset=ProductImage.objects.order_by('id')),
            Prefetch('options', queryset=OptionGroup.objects.filter(name='Chose color').prefetch_related('variants')),
        )
    )

    # Глобальные min/max (по всем продуктам)
    aggr = Product.objects.aggregate(price_min_all=Min('base_price'), price_max_all=Max('base_price'))
    price_min_all = int(aggr['price_min_all'] or 0)
    price_max_all = int(aggr['price_max_all'] or 0)

    # Поиск
    q = (request.GET.get('q') or '').strip()
    if q:
        base_qs = base_qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    # Цена
    pmin = _parse_int(request.GET.get('pmin'), price_min_all)
    pmax = _parse_int(request.GET.get('pmax'), price_max_all)
    pmin = max(price_min_all, min(pmin, price_max_all))
    pmax = max(price_min_all, min(pmax, price_max_all))
    if pmin > pmax:
        pmin, pmax = pmax, pmin
    base_qs = base_qs.filter(base_price__gte=pmin, base_price__lte=pmax)

    # Цвета (множественный выбор)
    selected_colors = [c.strip() for c in request.GET.getlist('color') if c.strip()]
    if selected_colors:
        base_qs = base_qs.filter(options__name='Chose color', options__variants__value__in=selected_colors).distinct()

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
        pass

    return base_qs, price_min_all, price_max_all, q, sort, pmin, pmax, selected_colors

def _qs_without(request: HttpRequest, remove_keys=(), remove_color_value=None):
    """
    Возвращает строку querystring без указанных ключей и/или без конкретного значения цвета.
    """
    qd = request.GET.copy()

    if remove_color_value is not None:
        colors = qd.getlist('color')
        colors = [c for c in colors if c != remove_color_value]
        if 'color' in qd:
            del qd['color']
        if colors:
            qd.setlist('color', colors)

    for k in remove_keys:
        if k in qd:
            del qd[k]

    if 'page' in qd:
        del qd['page']

    return qd.urlencode()

def catalog(request: HttpRequest):
    qs, price_min_all, price_max_all, q, sort, pmin, pmax, selected_colors = _filter_products(request)

    page_number = _parse_int(request.GET.get('page', 1), 1)
    paginator = Paginator(qs, PER_PAGE)
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages if paginator.num_pages else 1)

    has_more = page_obj.has_next()
    next_page = page_obj.next_page_number() if has_more else None

    colors_all = _get_all_colors()

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

def product_onepager_pdf(request):
    pid = request.GET.get('id')
    if not pid:
        return HttpResponseBadRequest("Missing ?id=<product_id>")

    product = get_object_or_404(
        Product.objects.prefetch_related('gallery_images'),
        pk=pid
    )

    # helpers
    def abs_url(u: str) -> str:
        return request.build_absolute_uri(u)

    def fetch_image(u: str):
        if not u:
            return None
        try:
            with urlopen(u) as r:
                return ImageReader(BytesIO(r.read()))
        except Exception:
            return None

    def get_group(name: str):
        return (
            OptionGroup.objects
            .filter(product=product, name__iexact=name)
            .prefetch_related('variants')
            .first()
        )

    def fmt_number(val: Decimal) -> str:
        q = Decimal('0.01')
        v = (val or Decimal('0')).quantize(q)
        return f"{v:,.2f}".replace(",", " ")  # только число, без валюты

    base_price = product.base_price or Decimal('0')

    # main image
    main_img = None
    first = product.gallery_images.all().first()
    if first and getattr(first, 'image', None):
        main_img = fetch_image(abs_url(first.image.url))

    # groups
    g_color = get_group('Chose color')
    g_size = get_group('WWHD(in)')
    g_back = get_group('backlight')

    # colors
    color_cards = []
    if g_color:
        for v in g_color.variants.all():
            u = v.image.url if v.image else None
            img = fetch_image(abs_url(u)) if u else None
            if img:
                color_cards.append({'img': img, 'label': (v.text or v.value)})
    color_cards = color_cards[:6]  # до 6 карточек на странице

    # price rows (только число)
    def rows_for(group):
        rows = []
        if not group:
            return rows
        for v in group.variants.all():
            price = base_price + (v.price_modifier or Decimal('0'))
            rows.append({'label': (v.text or v.value), 'price': fmt_number(price)})
        return rows

    size_rows = rows_for(g_size)
    back_rows = rows_for(g_back)

    # PDF
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    mx = 12 * mm
    my = 14 * mm
    cw = W - 2 * mx
    y = H - my

    c.setTitle(str(product.name))

    # 1) верхнее фото
    hero_h = 95 * mm
    if main_img:
        bx = mx
        by = y - hero_h
        c.setFillColor(colors.whitesmoke)
        c.rect(bx, by, cw, hero_h, fill=1, stroke=0)
        try:
            iw, ih = main_img.getSize()
            s = min(cw / iw, hero_h / ih)
            tw, th = iw * s, ih * s
            tx = bx + (cw - tw) / 2
            ty = by + (hero_h - th) / 2
            c.drawImage(main_img, tx, ty, tw, th, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
        y = by - 6 * mm

    # 2) блок цветов
    if color_cards:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.gray)
        c.drawString(mx, y, "Color options")
        y -= 4 * mm

        cols = 3
        gap = 5 * mm
        card_w = (cw - gap * (cols - 1)) / cols
        img_h = 42 * mm
        cap_h = 5 * mm
        card_h = img_h + cap_h + 12

        rows_cnt = (len(color_cards) + cols - 1) // cols
        total_h = rows_cnt * card_h + (rows_cnt - 1) * gap
        top_y = y
        base_y = top_y - total_h

        for i, card in enumerate(color_cards):
            row = i // cols
            col = i % cols
            x = mx + col * (card_w + gap)
            card_bottom = top_y - (row + 1) * card_h - row * gap

            c.setFillColor(colors.white)
            c.setStrokeColor(colors.lightgrey)
            c.roundRect(x, card_bottom, card_w, card_h, 6, fill=1, stroke=1)

            c.setFillColor(colors.whitesmoke)
            c.roundRect(x + 6, card_bottom + cap_h + 6, card_w - 12, img_h, 4, fill=1, stroke=0)

            try:
                iw, ih = card['img'].getSize()
                aw, ah = card_w - 12, img_h
                s = min(aw / iw, ah / ih)
                tw, th = iw * s, ih * s
                tx = x + 6 + (aw - tw) / 2
                ty = card_bottom + cap_h + 6 + (ah - th) / 2
                c.drawImage(card['img'], tx, ty, tw, th, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            cap = (card['label'] or '').upper()
            c.drawCentredString(x + card_w / 2, card_bottom + 3, cap)

        y = base_y - 8 * mm

    # 3) темный блок с ценами
    if size_rows or back_rows:
        rows_cnt = max(len(size_rows), len(back_rows), 1)
        name_h = 10 * mm
        head_h = 6 * mm
        row_h = 6 * mm
        foot_h = 6 * mm
        pad = 6 * mm
        panel_h = pad + name_h + 2 * mm + head_h + rows_cnt * row_h + 4 * mm + foot_h + pad
        py = y - panel_h

        c.setFillColorRGB(0.23, 0.25, 0.29)
        c.roundRect(mx, py, cw, panel_h, 10, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(mx + 10, py + panel_h - pad - 7, str(product.name).upper())

        col_gutter = 24  # расстояние между колонками
        inner_pad_x = 12  # внутренний горизонтальный паддинг внутри панели (слева/справа)

        col_w = (cw - 2 * inner_pad_x - col_gutter) / 2
        left_x = mx + inner_pad_x
        right_x = left_x + col_w + col_gutter
        top_y = py + panel_h - pad - name_h - 2 * mm

        def draw_table(x0, header, rows):
            if not rows:
                return
            c.setFont("Helvetica-Bold", 9)
            c.setFillColorRGB(0.81, 0.86, 0.91)
            c.drawString(x0, top_y, header)
            c.drawRightString(x0 + col_w - 2, top_y, "Price")  # -2pt безопасный отступ
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.white)
            y0 = top_y - 3
            for r in rows:
                y0 -= row_h
                c.drawString(x0, y0, str(r['label']))
                c.drawRightString(x0 + col_w - 2, y0, '$' + str(r['price']))  # -2pt

        draw_table(left_x, "WWHD (in)", size_rows)
        draw_table(right_x, "Backlight", back_rows)

        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.81, 0.86, 0.91)
        footer = "  •  ".join(filter(None, [
            getattr(settings, 'COMPANY_PHONE', '8-800-444-36-72'),
            getattr(settings, 'COMPANY_NAME', 'RE-SEPTION'),
            getattr(settings, 'COMPANY_WEBSITE', 're-seption.com'),
        ]))
        c.drawCentredString(mx + cw / 2, py + pad / 2, footer)

    c.showPage()
    c.save()

    pdf = buf.getvalue()
    buf.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="product_{product.pk}.pdf"'
    return response