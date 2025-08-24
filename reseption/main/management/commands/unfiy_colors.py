
from decimal import Decimal
import re
from main.models import Product, ProductImage, OptionGroup

import os
from urllib.parse import urlparse
from pathlib import Path
from django.core.management.base import BaseCommand
from main.models import ProductImage, OptionVariant # Замените myapp на имя вашего приложения
from django.core.files import File
from django.conf import settings
from django.db import transaction

class Command(BaseCommand):
    help = 'Unify all color variant names'

    def replace_str(self, str):
        str = str.strip()
        s = str.replace(',', '')
        replacements = ['\\' , '+']

        for r in replacements:
            s = s.replace(r, '/')
        
        subs = s.split('/')
        
        ret = ""
        idx = 0
        for s in subs:
            z = s.strip().capitalize()
            ret = ret + z + (" / " if idx < len(subs) - 1 else "")
            idx += 1
        return ret

    def handle(self, *args, **options):
        groups = OptionGroup.objects.filter(name='Chose color').prefetch_related('variants')
        
        for g in groups:
            for v in g.variants.all():
                old = v.value
                new_val = self.replace_str(v.value or '')
                v.value = new_val
                v.save(update_fields=['value'])
                print(old, " => ",new_val)