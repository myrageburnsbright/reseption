import os
import json
from google.cloud import translate_v2 as translate

# --- НАСТРОЙКИ ---
# Файл с данными от скрейпера
INPUT_JSON_FILE = 'result.json'
# Файл, куда будет сохранен результат
OUTPUT_JSON_FILE = 'products_data_translated.json'
# Файл для кэширования переводов, чтобы экономить запросы
CACHE_FILE = 'translation_cache.json'

SOURCE_LANG = 'ru'
TARGET_LANG = 'en'
BATCH_SIZE = 120 # Лимит Google API

# Поля, которые нужно перевести в каждом товаре
FIELDS_TO_TRANSLATE = ['name', 'description']
# Поля, которые нужно перевести внутри опций
OPTION_FIELDS_TO_TRANSLATE = ['value', 'text']
# ------------------

# Укажи путь к файлу с ключами аутентификации Google
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys.json"

try:
    translate_client = translate.Client()
except Exception as e:
    print(f"Ошибка инициализации клиента Google Translate: {e}")
    exit()

def load_cache():
    """Загружает кэш переводов из файла."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache_data):
    """Сохраняет кэш переводов в файл."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

def translate_texts(texts, cache):
    """Переводит список текстов, используя кэш и API."""
    unique_texts = list(set(texts)) # Убираем дубликаты
    texts_to_fetch = [text for text in unique_texts if text not in cache]

    if not texts_to_fetch:
        print("Все тексты найдены в кэше. Запрос к API не требуется.")
        return cache

    print(f"Найдено {len(texts_to_fetch)} новых уникальных фрагментов для перевода.")
    
    # Разбиваем на части (батчи) и переводим
    for i in range(0, len(texts_to_fetch), BATCH_SIZE):
        batch = texts_to_fetch[i:i + BATCH_SIZE]
        print(f"Отправка части {i//BATCH_SIZE + 1} ({len(batch)} фрагментов)...")
        try:
            results = translate_client.translate(batch, source_language=SOURCE_LANG, target_language=TARGET_LANG)
            # Обновляем кэш новыми переводами
            for original, translation in zip(batch, results):
                cache[original] = translation['translatedText']
        except Exception as e:
            print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при обращении к API: {e}")
            break # Прерываем в случае ошибки, чтобы не тратить запросы

    return cache

def process_and_translate_products(file_path):
    """Основная функция: загружает, переводит и сохраняет данные о товарах."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_products = json.load(f)
        print(f"--- Успешно загружено {len(all_products)} товаров из файла {file_path} ---")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ОШИБКА: Не удалось прочитать файл {file_path}. {e}")
        return

    # --- Этап 1: Сбор всего текста для перевода ---
    all_texts_to_translate = []
    for product in all_products:
        for field in FIELDS_TO_TRANSLATE:
            if product.get(field):
                all_texts_to_translate.append(product[field])
        
        for option_group in product.get('options', {}).values():
            for variant in option_group.get('variants', []):
                for field in OPTION_FIELDS_TO_TRANSLATE:
                    if variant.get(field):
                        all_texts_to_translate.append(variant[field])

    # --- Этап 2: Перевод собранного текста ---
    translation_cache = load_cache()
    translation_cache = translate_texts(all_texts_to_translate, translation_cache)
    save_cache(translation_cache) # Сохраняем обновленный кэш

    # --- Этап 3: Создание новой структуры с переведенными данными ---
    translated_products = []
    for product in all_products:
        translated_product = product.copy() # Копируем, чтобы не изменять оригинал в памяти
        
        for field in FIELDS_TO_TRANSLATE:
            if translated_product.get(field):
                translated_product[field] = translation_cache.get(translated_product[field], translated_product[field])

        if 'options' in translated_product:
            for group_name, option_details in translated_product['options'].items():
                for variant in option_details.get('variants', []):
                    for field in OPTION_FIELDS_TO_TRANSLATE:
                        if variant.get(field):
                            variant[field] = translation_cache.get(variant[field], variant[field])
        
        translated_products.append(translated_product)
        
    # --- Этап 4: Сохранение результата в новый файл ---
    try:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(translated_products, f, indent=2, ensure_ascii=False)
        print(f"\n--- Перевод завершен. Результат сохранен в файл: {OUTPUT_JSON_FILE} ---")
    except Exception as e:
        print(f"ОШИБКА при сохранении файла: {e}")

# --- Основной процесс ---
if __name__ == '__main__':
    process_and_translate_products(INPUT_JSON_FILE)
