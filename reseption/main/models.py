# myapp/models.py
from django.db import models

class Product(models.Model):
    """
    Main model for a product.
    """
    name = models.CharField("Product Name", max_length=255)
    base_price = models.DecimalField("Base Price", max_digits=10, decimal_places=2)
    description = models.TextField("Description", blank=True)
    product_url = models.URLField("Product Page URL", max_length=1024, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']

class ProductImage(models.Model):
    """
    Model to store gallery images, related to a Product.
    One-to-many relationship: one product can have many images.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name="Product"
    )
    image = models.ImageField(
        "Product Image",
        upload_to='product_gallery/%Y/%m/%d/', 
        blank=True,
        null=True
    )

    def __str__(self):
        return self.image.url

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Gallery Images"
        ordering = ['id']


class OptionGroup(models.Model):
    """
    A group of options for a product. E.g., "Chose color" or "Width".
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='options', # Allows access via: product.options.all()
        verbose_name="Product"
    )
    name = models.CharField("Option Group Name", max_length=100)
    option_type = models.CharField(
        "Option Type",
        max_length=10,
        choices=[('radio', 'Radio Button'), ('select', 'Dropdown')],
        default='radio'
    )

    def __str__(self):
        return f"{self.name} for {self.product.name}"

    class Meta:
        verbose_name = "Option Group"
        verbose_name_plural = "Option Groups"
        # Ensures that a product won't have two option groups with the same name
        unique_together = ('product', 'name')
        ordering = ['id']

class OptionVariant(models.Model):
    """
    A specific variant within an option group. E.g., "Light cement" or "17.7\"".
    """
    group = models.ForeignKey(
        OptionGroup,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name="Option Group"
    )
    value = models.CharField("Value", max_length=255)
    image = models.ImageField(
        "Variant Image",
        upload_to='variant_images/%Y/%m/%d/',
        blank=True,
        null=True
    )
    text = models.CharField("Display Text (for select)", max_length=255, blank=True, null=True)
    price_modifier = models.DecimalField(
        "Price Modifier",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_default = models.BooleanField("Is Default", default=False)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = "Option Variant"
        verbose_name_plural = "Option Variants"
        ordering = ['id']
