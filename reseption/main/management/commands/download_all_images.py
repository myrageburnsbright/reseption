import os
import requests
from urllib.parse import urlparse
from pathlib import Path
from django.core.management.base import BaseCommand
from main.models import ProductImage, OptionVariant # Замените myapp на имя вашего приложения
from django.core.files import File
from django.conf import settings

class Command(BaseCommand):
    help = 'Downloads all unique images by path from ProductImage and OptionVariant models.'

    def handle(self, *args, **options):

        def collect_urls(queryset, url_field_name):
            self.stdout.write(f"Собираю URL из модели {queryset.model.__name__}...")
            count = 0
            for instance in queryset:
                count += 1
                url = getattr(instance, url_field_name)
                if url:
                    path = os.path.join(settings.BASE_DIR, 'save',  urlparse(url).path.lstrip('/'))
                    #print(path)
                    with open(path, 'rb') as f:
                        django_file = File(f)

                        print(django_file.name.split('/')[-1])
                        instance.image.save(django_file.name.split('/')[-1], django_file, save=True)
                        #print(f"Файл успешно сохранен! Путь в БД: {instance.image.path} = > {url}")
            self.stdout.write(f"Обработано {count} записей.")

        # 1. Собираем все URL из всех моделей
        product_image_qs = ProductImage.objects.filter(image_url__isnull=False).exclude(image_url__exact='')
        collect_urls(product_image_qs, 'image_url')

        variant_qs = OptionVariant.objects.filter(image_url__isnull=False).exclude(image_url__exact='')
        collect_urls(variant_qs, 'image_url')

        self.stdout.write(self.style.SUCCESS("\n🎉 Процесс скачивания завершен!"))

        