from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from catalog.models import Product

class Order(models.Model):
    """Заказы"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name="Пользователь"
    )
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    delivery_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата доставки")
    pickup_point = models.CharField(max_length=255, blank=True, null=True, verbose_name="Пункт выдачи")
    delivery_address = models.CharField(max_length=500, blank=True, null=True, verbose_name="Адрес доставки")
    pickup_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Код получения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        db_table = 'orders'
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Заказ №{self.id} от {self.order_date.strftime('%d.%m.%Y')}"
    
    @property
    def total_amount(self):
        """Общая сумма заказа"""
        return sum(item.total_price for item in self.items.all())

class OrderItem(models.Model):
    """Позиции заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', verbose_name="Товар")
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Количество")
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена в момент заказа")
    
    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        db_table = 'order_items'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        """Стоимость позиции"""
        return self.price_at_order * self.quantity
    
    def save(self, *args, **kwargs):
        # При создании позиции сохраняем текущую цену товара
        if not self.pk and not self.price_at_order:  # если это новый объект и цена не указана
            self.price_at_order = self.product.final_price
        super().save(*args, **kwargs)