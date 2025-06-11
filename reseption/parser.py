import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException

# --- НАСТРОЙКИ ---
# ВСТАВЬ СЮДА ССЫЛКУ НА СТРАНИЦУ ТОВАРА, КОТОРУЮ ХОЧЕШЬ ПРОВЕРИТЬ
PRODUCT_PAGE_URL = 'https://re-seption.com/stoly/tproduct/766214456-518549979941-stol-rukovoditelya-seo'

# --- ТВОИ СЕЛЕКТОРЫ ---
# CSS-селекторы для данных внутри карточки
PRODUCT_NAME_SELECTOR = '.js-product-name'
PRODUCT_PRICE_SELECTOR = '.js-product-price'
# Добавил селектор для описания, он тоже полезен
PRODUCT_DESCRIPTION_SELECTOR = '.t-product__text'

# Селекторы для опций и галереи
PRODUCT_OPTIONS_FORM_SELECTOR = 'form.t-product__option-variants'
OPTION_ITEM_SELECTOR = '.t-product__option-item'
OPTION_INPUT_SELECTOR = '.t-product__option-input'
OPTION_IMAGE_SELECTOR = '.t-product__option-checkmark'
PRODUCT_SELECT_SELECTOR = 'select.js-product-option-variants'
GALLERY_THUMBNAIL_SELECTOR = '.t-slds__thumbsbullet .t-slds__bgimg'

OUTPUT = '/home/lainvasora/dev/reseption/reseption/links5.txt' 
# ------------------


def setup_driver():
    """Настраивает и возвращает драйвер для Selenium."""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except ImportError:
        print("Библиотека webdriver-manager не найдена. Установите: pip install webdriver-manager")
        service = Service()
        
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def parse_product_page(driver, product_url):
    """Заходит на страницу товара и собирает всю информацию."""
    print(f"--- Парсинг страницы: {product_url} ---")
    try:
        driver.get(product_url)
        time.sleep(3) # Даем странице полностью загрузиться

        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        name = soup.select_one(PRODUCT_NAME_SELECTOR).text.strip() if soup.select_one(PRODUCT_NAME_SELECTOR) else 'Название не найдено'
        price = soup.select_one(PRODUCT_PRICE_SELECTOR).text.strip() if soup.select_one(PRODUCT_PRICE_SELECTOR) else 'Цена не найдена'
        description = soup.select_one(PRODUCT_DESCRIPTION_SELECTOR).text.strip() if soup.select_one(PRODUCT_DESCRIPTION_SELECTOR) else 'Описание не найдено'

        # Сбор галереи изображений
        gallery_images = [thumb.get('data-original') for thumb in soup.select(GALLERY_THUMBNAIL_SELECTOR) if thumb.get('data-original')]

        # Сбор всех опций товара
        product_options = {}

        # 1. Радио-кнопки
        for form in soup.select(PRODUCT_OPTIONS_FORM_SELECTOR):
            items = form.select(OPTION_ITEM_SELECTOR)
            if not items: continue
            
            group_name_input = items[0].select_one(OPTION_INPUT_SELECTOR)
            if not group_name_input: continue
            
            group_name = group_name_input.get('name', 'Опция')
            variants = []
            for item in items:
                input_tag = item.select_one(OPTION_INPUT_SELECTOR)
                if not input_tag: continue
                variants.append({
                    'value': input_tag.get('value'),
                    'image': item.select_one(OPTION_IMAGE_SELECTOR).get('data-original') if item.select_one(OPTION_IMAGE_SELECTOR) else None,
                    'is_default': input_tag.has_attr('checked')
                })
            product_options[group_name] = {'type': 'radio', 'variants': variants}

        # 2. Выпадающие списки
        for i, select in enumerate(soup.select(PRODUCT_SELECT_SELECTOR)):
            group_name = select.get('name') or f"Dropdown {i+1}"
            variants = [{'value': o.get('value'), 'text': o.text.strip(), 'price_modifier': o.get('data-product-variant-price')} for o in select.find_all('option')]
            product_options[group_name] = {'type': 'select', 'variants': variants}

        return {
            'name': name,
            'price': price,
            'description': description,
            'product_url': product_url,
            'gallery_images': gallery_images,
            'options': product_options
        }
    except Exception as e:
        print(f"!!! Ошибка при парсинге страницы {product_url}: {e}")
        return None


# --- Основной процесс ---
if __name__ == '__main__':
    driver = setup_driver()
    product_data = None
    lines = None
    with open(OUTPUT, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    all_data = []
    for link in lines:
        try:
            # Запускаем парсинг только для одной страницы
            # ИСПРАВЛЕНИЕ: Убираем лишние пробелы и символы переноса строки из ссылки
            clean_link = link.strip()
            if not clean_link:
                continue

            product_data = parse_product_page(driver, clean_link)
            if product_data:
                all_data.append(product_data)
        finally:
            print(f"go to: {link} --- Пауза 3 секунд ---")
            time.sleep(3)
        
    driver.quit()
    print("\n--- Работа тестового скрейпера завершена. ---\n")

    # Выводим результат в консоль
    if all_data:
        print("--- Собранные данные: ---")

        with open('result.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        # Используем json.dumps для красивого вывода
        print(len(all_data))
    else:
        print("Не удалось собрать данные о товаре.")

