import os
import re
import json
from bs4 import BeautifulSoup, Comment
from google.cloud import translate_v2 as translate

# --- НАСТРОЙКИ ---
# ВАЖНО: Сделай резервную копию этой папки перед запуском!
SOURCE_DIR = 'main/templates/main' 
SOURCE_LANG = 'ru'
TARGET_LANG = 'en'
# Имя файла для кэша переводов
CACHE_FILE = 'translation_cache.json'
# Максимальное количество фрагментов текста в одном запросе к API
BATCH_SIZE = 120
# ------------------

# Укажи путь к файлу с ключами аутентификации Google
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys.json"

try:
    translate_client = translate.Client()
except Exception as e:
    print(f"Ошибка инициализации клиента Google Translate: {e}")
    exit()

DJANGO_TAG_RE = re.compile(r'{[%{].*?[%}]}')
# НОВОЕ: Регулярное выражение для поиска строк, которые НЕ нужно переводить (CSS, числа и т.д.)
NON_TRANSLATABLE_RE = re.compile(r'^(\d+[\.,]?\d*|#[\da-fA-F]{3,6}|[\d\.]+(px|em|rem|%|vh|vw|s|ms))$')

def load_cache():
    """Загружает кэш переводов из файла, если он существует."""
    if os.path.exists(CACHE_FILE):
        print(f"Загрузка кэша из файла: {CACHE_FILE}")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache_data):
    """Сохраняет кэш переводов в файл."""
    print(f"Сохранение кэша в файл: {CACHE_FILE}")
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

def translate_html_file(file_path, cache):
    print(f"\n--- Обработка файла: {file_path} ---")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # НОВОЕ: Используем более надежный парсер 'lxml'
            soup = BeautifulSoup(content, 'lxml')
    except Exception as e:
        print(f"Не удалось прочитать файл: {e}")
        return False

    tags_to_modify = []
    texts_to_fetch_from_api = []
    
    all_text_nodes = soup.find_all(string=True)

    for text_node in all_text_nodes:
        # Стандартные фильтры
        if text_node.parent.name in ['script', 'style', 'head', 'title', 'textarea'] or isinstance(text_node, Comment):
            continue
        
        text = text_node.strip()
        
        # НОВОЕ: Дополнительная проверка, чтобы не переводить технический мусор
        if text and not DJANGO_TAG_RE.match(text) and not NON_TRANSLATABLE_RE.match(text):
            if text not in cache:
                if text not in texts_to_fetch_from_api:
                    texts_to_fetch_from_api.append(text)
            tags_to_modify.append(text_node)

    if not texts_to_fetch_from_api and not tags_to_modify:
        print("Текст для перевода не найден. Файл пропущен.")
        return False

    if texts_to_fetch_from_api:
        print(f"Найдено {len(texts_to_fetch_from_api)} новых уникальных фрагментов для перевода.")
        for i in range(0, len(texts_to_fetch_from_api), BATCH_SIZE):
            batch = texts_to_fetch_from_api[i:i + BATCH_SIZE]
            print(f"Отправка части {i//BATCH_SIZE + 1} ({len(batch)} фрагментов)...")
            
            try:
                results = translate_client.translate(batch, source_language=SOURCE_LANG, target_language=TARGET_LANG)
                for original, translation in zip(batch, results):
                    cache[original] = translation['translatedText']
            except Exception as e:
                print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при обращении к API Google Translate: {e}")
                return False
    else:
        print("Все тексты найдены в кэше. Запрос к API не требуется.")

    # Замена текста
    has_changed = False
    for text_node in tags_to_modify:
        original_text = text_node.strip()
        if original_text in cache:
            translated_text = cache[original_text]
            if original_text != translated_text:
                # Заменяем только если перевод отличается от оригинала
                text_node.replace_with(text_node.replace(original_text, translated_text))
                has_changed = True
    
    if not has_changed:
        print("В файле не было изменений после перевода.")
        return False

    # Перезапись файла
    try:
        with open(file_path, 'w', encoding='utf-8') as f_out:
            # Используем .prettify() для более чистого вывода HTML
            f_out.write(soup.prettify(formatter='html5'))
        print(f"Файл успешно переведен и сохранен: {file_path}")
        return True
    except Exception as e:
        print(f"Не удалось сохранить файл: {e}")
        return False

# --- Основной цикл ---
if __name__ == '__main__':
    # Перед запуском установи lxml: pip install lxml
    translation_cache = load_cache()
    
    if not os.path.exists(SOURCE_DIR):
        print(f"Ошибка: Исходная директория не найдена: '{SOURCE_DIR}'")
    else:
        for root, dirs, files in os.walk(SOURCE_DIR):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    translate_html_file(file_path, translation_cache)

        save_cache(translation_cache)
        print("\n--- Перевод завершен. ---")
