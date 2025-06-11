import json
import re

# --- НАСТРОЙКИ ---
# Файл с переведенными данными
INPUT_JSON_FILE = 'products_final_price.json'
# Итоговый файл с измененными ключами
OUTPUT_JSON_FILE = 'products_final_no_ru.json'
# Карта для переименования ключей в опциях
KEY_TRANSLATION_MAP = {
    "Выберите цвет:": "Chose color",
    "Цвета": "Colors",
    "Ш x Ш х В х Г (мм)": "WWHD(in)",
    "Ширина": "Width",
    "Dropdown 1": "backlight",
    "Высота х Ширина х Глубина": "Height x Width x Depth",
}
# ------------------

def rename_and_filter_keys(file_path):
    """
    Загружает JSON, переименовывает и фильтрует ключи в опциях,
    и сохраняет результат в новый файл.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_products = json.load(f)
        print(f"--- Успешно загружено {len(all_products)} товаров из файла {file_path} ---")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ОШИБКА: Не удалось прочитать файл {file_path}. {e}")
        return

    # --- Основной цикл обхода ---
    for product in all_products:
        options = product.get('options', {})
        if not options:
            continue

        modified_options = {}
        # Проходим по всем ключам в оригинальном словаре опций
        for original_key, option_details in options.items():
            new_key = None
            if original_key in KEY_TRANSLATION_MAP:
                # Если ключ есть в нашей карте, берем перевод
                new_key = KEY_TRANSLATION_MAP[original_key]
            elif original_key.isascii():
                # Если ключ уже на латинице (английский), оставляем как есть
                new_key = original_key
            
            # Если ключ был на кириллице и не найден в карте, он будет проигнорирован.

            if new_key:
                # Добавляем в новый словарь только те ключи, которые прошли проверку
                modified_options[new_key] = option_details

        # Заменяем старый словарь опций на новый, отфильтрованный и переименованный
        product['options'] = modified_options
    
    # --- Сохранение результата в новый файл ---
    try:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        print(f"\n--- Обработка ключей завершена. Результат сохранен в файл: {OUTPUT_JSON_FILE} ---")
    except Exception as e:
        print(f"ОШИБКА при сохранении файла: {e}")

# --- Основной процесс ---
if __name__ == '__main__':
    rename_and_filter_keys(INPUT_JSON_FILE)
