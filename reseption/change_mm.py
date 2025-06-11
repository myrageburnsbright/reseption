import json
import re

# --- НАСТРОЙКИ ---
# Итоговый файл с измененными ключами (от предыдущего шага)
INPUT_JSON_FILE = 'products_final_no_ru.json'
# Финальный файл с конвертированными размерами
OUTPUT_JSON_FILE = 'products_final_converted.json'
# Коэффициент для перевода миллиметров в дюймы
MM_TO_INCH_DIVIDER = 25.4
# ------------------

def convert_mm_to_inches(value_str, conversion_log):
    """
    Находит все числа в строке, конвертирует их из мм в дюймы
    и заменяет единицу измерения.
    """
    def convert_match(match):
        try:
            num_str = match.group(0).replace(' ', '')
            mm_value = float(num_str)
            inch_value = round(mm_value / MM_TO_INCH_DIVIDER, 1)
            return str(inch_value)
        except (ValueError, TypeError):
            return match.group(0)

    # [\d\s]+ находит одно или более чисел и пробелов подряд
    converted_str = re.sub(r'[\d\s.,]+', convert_match, value_str)
    
    # ИСПРАВЛЕНИЕ: Заменяем английские "mm"
    converted_str = converted_str.replace('(mm)', '(in)').replace('mm', '"')
    
    # Записываем в лог, что мы сделали
    conversion_log.append(f"'{value_str}'  ->  '{converted_str}'")
    
    return converted_str

def traverse_and_convert(data, conversion_log):
    """
    Рекурсивно обходит структуру данных и возвращает новую структуру
    с конвертированными значениями, ведя лог изменений.
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_dict[key] = traverse_and_convert(value, conversion_log)
        return new_dict
    elif isinstance(data, list):
        return [traverse_and_convert(item, conversion_log) for item in data]
    # ИСПРАВЛЕНИЕ: Ищем английские "mm"
    elif isinstance(data, str) and 'mm' in data:
        # Если это строка с "mm" - конвертируем ее
        return convert_mm_to_inches(data, conversion_log)
    else:
        # Во всех остальных случаях возвращаем значение как есть
        return data

def convert_units_in_json(file_path):
    """
    Основная функция: загружает, конвертирует и сохраняет данные.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_products = json.load(f)
        print(f"--- Успешно загружено {len(all_products)} товаров из файла {file_path} ---")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ОШИБКА: Не удалось прочитать файл {file_path}. {e}")
        return

    # Создаем пустой лог для отслеживания изменений
    conversion_log = []
    
    # Запускаем рекурсивный обход и конвертацию
    converted_data = traverse_and_convert(all_products, conversion_log)
    
    # --- Выводим отчет о проделанной работе ---
    if conversion_log:
        print(f"\n--- Найдено и сконвертировано {len(conversion_log)} значений: ---")
        for log_entry in conversion_log:
            print(log_entry)
    else:
        print("\n--- Не найдено ни одного значения с 'mm' для конвертации. ---")

    # --- Сохранение результата в новый файл ---
    try:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, indent=2, ensure_ascii=False)
        print(f"\n--- Обработка завершена. Результат сохранен в файл: {OUTPUT_JSON_FILE} ---")
    except Exception as e:
        print(f"ОШИБКА при сохранении файла: {e}")

# --- Основной процесс ---
if __name__ == '__main__':
    convert_units_in_json(INPUT_JSON_FILE)
