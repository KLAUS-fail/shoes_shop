from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import os

class Category(models.Model):
    """Категории товаров"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        db_table = 'categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Manufacturer(models.Model):
    """Производители"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название производителя")
    
    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"
        db_table = 'manufacturers'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    """Поставщики"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Название поставщика")
    
    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
        db_table = 'suppliers'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Unit(models.Model):
    """Единицы измерения"""
    name = models.CharField(max_length=20, unique=True, verbose_name="Единица измерения")
    
    class Meta:
        verbose_name = "Единица измерения"
        verbose_name_plural = "Единицы измерения"
        db_table = 'units'
    
    def __str__(self):
        return self.name

def product_photo_path(instance, filename):
    """Генерирует путь для сохранения фото товара"""
    # Получаем расширение файла
    ext = filename.split('.')[-1]
    # Генерируем имя файла: product_{id}.{ext}
    filename = f"product_{instance.pk or 'new'}.{ext}"
    # Возвращаем путь: photos/product_{id}.{ext}
    return os.path.join('photos', filename)

class Product(models.Model):
    """Товары (обувь)"""
    # Основная информация
    name = models.CharField(max_length=200, verbose_name="Наименование")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    # Цены и количество
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)], 
        verbose_name="Цена"
    )
    stock_quantity = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)], 
        verbose_name="Количество на складе"
    )
    discount = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)], 
        verbose_name="Скидка %"
    )
    
    # Фото
    photo = models.ImageField(
        upload_to=product_photo_path, 
        blank=True, 
        null=True,
        verbose_name="Фото"
    )
    
    # Связи с другими таблицами (внешние ключи)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='products',
        verbose_name="Категория"
    )
    manufacturer = models.ForeignKey(
        Manufacturer, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='products',
        verbose_name="Производитель"
    )
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='products',
        verbose_name="Поставщик"
    )
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='products',
        verbose_name="Единица измерения"
    )
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        db_table = 'products'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['supplier']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def final_price(self):
        """Возвращает цену со скидкой"""
        if self.discount > 0:
            return self.price * (1 - self.discount / 100)
        return self.price
    
    @property
    def has_discount(self):
        """Проверяет, есть ли скидка"""
        return self.discount > 0
    
    @property
    def is_out_of_stock(self):
        """Проверяет, есть ли товар в наличии"""
        return self.stock_quantity <= 0
    
    @property
    def big_discount(self):
        """Проверяет, превышает ли скидка 15%"""
        return self.discount > 15