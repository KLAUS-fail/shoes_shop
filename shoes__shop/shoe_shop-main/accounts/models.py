from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    """Роли пользователей"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")
    
    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
        db_table = 'roles'  # явное имя таблицы
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    """Пользователь системы"""
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отчество")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, verbose_name="Роль")
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        db_table = 'users'
    
    def get_full_name(self):
        """Возвращает ФИО пользователя"""
        full_name = f"{self.last_name} {self.first_name}"
        if self.middle_name:
            full_name += f" {self.middle_name}"
        return full_name.strip()
    
    def __str__(self):
        return self.get_full_name() or self.username