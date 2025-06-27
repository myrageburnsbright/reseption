# myapp/management/commands/load_products.py
import json
from html import unescape
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Product, ProductImage, OptionGroup, OptionVariant # Замени 'myapp' на имя своего приложения

# --- НАСТРОЙКИ ---
# Путь к финальному JSON-файлу с данными
JSON_FILE_PATH = 'products_final_converted.json'
# ------------------

class Command(BaseCommand):
    help = 'Загружает данные о товарах из JSON-файла в базу данных'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Начало загрузки данных о товарах ---'))

        try:
            with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
                all_products_data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'ОШИБКА: Файл не найден: {JSON_FILE_PATH}'))
            return
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f'ОШИБКА: Не удалось прочитать JSON из файла: {JSON_FILE_PATH}'))
            return

        with transaction.atomic():
            # Очищаем старые данные перед загрузкой (опционально, но рекомендуется для чистоты)
            self.stdout.write('Очистка старых данных...')
            Product.objects.all().delete()

            # Проходим по каждому товару из JSON
            for product_data in all_products_data:
                self.stdout.write(f"  Обработка товара: {product_data.get('name')}")

                # --- Создание или обновление основного товара ---
                # update_or_create ищет товар по product_url. Если находит - обновляет. Если нет - создает.

                # --- Очищаем основные данные перед созданием ---
                clean_name = unescape(product_data.get('name', ''))
                clean_description = unescape(product_data.get('description', ''))

                product, created = Product.objects.update_or_create(
                    product_url=product_data.get('product_url'),
                    defaults={
                        'name': clean_name,
                        'base_price': product_data.get('price', 0.0),
                        'description': clean_description,
                    }
                )
                if created:
                    self.stdout.write(f'    -> Создан новый товар: {product.name}')
                else:
                    self.stdout.write(f'    -> Обновлен существующий товар: {product.name}')

                # --- Создание галереи изображений ---
                for image_url in product_data.get('gallery_images', []):
                    ProductImage.objects.create(product=product, image_url=image_url)

                # --- Создание опций ---
                options_data = product_data.get('options', {})
                for group_name, option_details in options_data.items():
                    # Создаем группу опций
                    option_group, _ = OptionGroup.objects.get_or_create(
                        product=product,
                        name=group_name,
                        defaults={'option_type': option_details.get('type', 'radio')}
                    )

                    # Создаем варианты для этой группы
                    for variant_data in option_details.get('variants', []):
                        OptionVariant.objects.create(
                            group=option_group,
                            value=variant_data.get('value'),
                            text=variant_data.get('text'),
                            image_url=variant_data.get('image'),
                            price_modifier=variant_data.get('price_modifier'),
                            is_default=variant_data.get('is_default', False)
                        )

        self.stdout.write(self.style.SUCCESS(f'--- Успешно загружено {len(all_products_data)} товаров ---'))
