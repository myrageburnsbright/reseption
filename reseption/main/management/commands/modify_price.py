
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
    help = 'Modify price'
    
    def count_volume(self, str):
        s = str.replace('(in)', '')
        s = s.replace('")', '')
        s = s.replace('х', 'x')
        s = s.replace('X', 'x')
        s = s.replace('Х', 'x')
        
        split = s.split('x')
        t = [ Decimal(x) for x in split]
        return t[0] * t[1] * t[2]

    def handle(self, *args, **options):

        groups = OptionGroup.objects.filter(name='WWHD(in)').prefetch_related('variants')
        for g in groups:
            base_price = g.product.base_price
            print("ID:", g.product.id)
            base_value = self.count_volume(g.variants.filter(is_default=True).first().value) + Decimal(1500)
            percent_rate = base_price * Decimal("0.035")
            additional_percent = percent_rate + Decimal("0")
            extra_percent1 = base_price * Decimal("0.006")
            extra_percent2 = base_price * Decimal("0.007")
            extra_percent3 = base_price * Decimal("0.004")
            for v in g.variants.all():
                if v.is_default:
                    continue
                current_value = self.count_volume(v.value)

                v.price_modifier = additional_percent
                print(base_price,"additioning",percent_rate, v.price_modifier)
                if current_value > base_value + Decimal(2500):
                    v.price_modifier += extra_percent2
                if current_value > base_value + Decimal(4500):
                    v.price_modifier += extra_percent2
                if current_value > base_value + Decimal(9500):
                    v.price_modifier += extra_percent1
                if current_value > base_value + Decimal(14500):
                    v.price_modifier += extra_percent1
                if current_value > base_value + Decimal(20000):
                    v.price_modifier += extra_percent3
                if current_value > base_value + Decimal(40000):
                    v.price_modifier += extra_percent3
                if current_value > base_value + Decimal(30000):
                    v.price_modifier += extra_percent3
                additional_percent += percent_rate
                v.price_modifier = round(v.price_modifier, 0)
                v.save(update_fields=['price_modifier'])
                print(base_value, " => ",current_value, "::::", base_price," midified to",v.price_modifier)