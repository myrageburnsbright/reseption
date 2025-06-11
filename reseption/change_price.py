import json
import re

# --- НАСТРОЙКИ ---
# Файл с переведенными данными
INPUT_JSON_FILE = 'products_data_translated.json'
# Итоговый файл с измененными ценами
OUTPUT_JSON_FILE = 'products_final_price.json'
# На какое число делить цены
DIVIDER = 20
# ------------------

def update_prices_in_json(file_path):
    """
    Загружает JSON, делит все цены на указанное число и сохраняет в новый файл.
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
        # --- Обработка основной цены товара ---
        price_str = product.get('price')
        if isinstance(price_str, str):
            try:
                # ИСПРАВЛЕНИЕ: Убираем пробелы из строки перед поиском числа
                cleaned_str = price_str.replace(' ', '')
                match = re.search(r'-?\d+\.?\d*', cleaned_str.replace(',', '.'))
                if match:
                    original_price = float(match.group())
                    product['price'] = original_price / DIVIDER
            except (ValueError, TypeError):
                print(f"Не удалось обработать цену: {price_str}")

        # --- Обработка опций ---
        options = product.get('options', {})
        for option_group in options.values():
            if option_group.get('type') == 'select':
                for variant in option_group.get('variants', []):
                    price_mod_str = variant.get('price_modifier')
                    if isinstance(price_mod_str, str):
                        try:
                            # ИСПРАВЛЕНИЕ: Убираем пробелы и знак "+"
                            cleaned_mod_str = price_mod_str.replace(' ', '').replace('+', '')
                            match = re.search(r'-?\d+\.?\d*', cleaned_mod_str.replace(',', '.'))
                            if match:
                                original_mod_price = float(match.group())
                                variant['price_modifier'] = original_mod_price / DIVIDER
                        except (ValueError, TypeError):
                            print(f"Не удалось обработать модификатор цены: {price_mod_str}")
    
    # --- Сохранение результата в новый файл ---
    try:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        print(f"\n--- Обработка цен завершена. Результат сохранен в файл: {OUTPUT_JSON_FILE} ---")
    except Exception as e:
        print(f"ОШИБКА при сохранении файла: {e}")

# --- Основной процесс ---
if __name__ == '__main__':
    update_prices_in_json(INPUT_JSON_FILE)
