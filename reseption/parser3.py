import os
from bs4 import BeautifulSoup

# --- НАСТРОЙКИ ---
# 1. Укажи полный путь к твоему сохраненному HTML-файлу
HTML_FILE_PATH = '/home/lainvasora/dev/reseption/reseption/links2.txt'  # <-- ЗАМЕНИ ЭТО НА СВОЙ ПУТЬ
OUTPUT = '/home/lainvasora/dev/reseption/reseption/links5.txt' 
# 2. Селектор для карточки товара (чтобы искать ссылки только внутри них)
PRODUCT_CARD_SELECTOR = '.t-store__card'
# ------------------

def extract_links_from_html(file_path, card_selector):
    """
    Читает HTML-файл, находит все ссылки внутри карточек товаров и выводит их.
    """
    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        print(f"ОШИБКА: Файл не найден по пути: {file_path}")
        return

    print(f"--- Чтение файла: {file_path} ---")
    s = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for link in lines:
            s.add(link)

    print(len(s))
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        for w in s:
            f.write(w)

# --- Основной процесс ---
if __name__ == '__main__':
    extract_links_from_html(HTML_FILE_PATH, PRODUCT_CARD_SELECTOR)
    print("\n--- Поиск ссылок завершен. ---")

