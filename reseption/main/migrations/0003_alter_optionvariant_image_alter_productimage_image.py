# Generated by Django 5.2.2 on 2025-06-29 02:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_optionvariant_image_productimage_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='optionvariant',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Variant Image'),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Product Image'),
        ),
    ]
