#!/usr/bin/env python
# scripts/create_test_users.py
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoeproject.settings')
django.setup()

from accounts.models import User, Role

def create_users():
    """Создание тестовых пользователей"""
    
    print("=" * 60)
    print("👥 СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 60)
    
    # Получаем или создаем роли
    admin_role, _ = Role.objects.get_or_create(name='Администратор')
    manager_role, _ = Role.objects.get_or_create(name='Менеджер')
    client_role, _ = Role.objects.get_or_create(name='Авторизированный клиент')
    
    # Создаем администратора
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Админ',
            'last_name': 'Админов',
            'middle_name': 'Админович',
            'role': admin_role,
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print("  ✅ Создан администратор: admin / admin123")
    else:
        print("  ✅ Администратор уже существует: admin / admin123")
    
    # Создаем менеджера
    manager, created = User.objects.get_or_create(
        username='manager',
        defaults={
            'first_name': 'Менеджер',
            'last_name': 'Менеджеров',
            'middle_name': 'Менеджерович',
            'role': manager_role,
            'email': 'manager@example.com',
        }
    )
    if created:
        manager.set_password('manager123')
        manager.save()
        print("  ✅ Создан менеджер: manager / manager123")
    else:
        print("  ✅ Менеджер уже существует: manager / manager123")
    
    # Создаем клиента
    client, created = User.objects.get_or_create(
        username='client',
        defaults={
            'first_name': 'Клиент',
            'last_name': 'Клиентов',
            'middle_name': 'Клиентович',
            'role': client_role,
            'email': 'client@example.com',
        }
    )
    if created:
        client.set_password('client123')
        client.save()
        print("  ✅ Создан клиент: client / client123")
    else:
        print("  ✅ Клиент уже существует: client / client123")

def list_users():
    """Список всех пользователей"""
    print("\n📋 Список всех пользователей:")
    print("-" * 80)
    print(f"{'Логин':<15} {'Пароль':<15} {'Роль':<20} {'ФИО':<30}")
    print("-" * 80)
    
    for user in User.objects.all():
        role_name = user.role.name if user.role else 'Нет роли'
        password_info = 'admin123' if user.username == 'admin' else 'manager123' if user.username == 'manager' else 'client123' if user.username == 'client' else '******'
        print(f"{user.username:<15} {password_info:<15} {role_name:<20} {user.get_full_name():<30}")
    
    print("-" * 80)

def create_from_excel_users():
    """Создание пользователей из Excel (если их еще нет)"""
    print("\n📦 Проверка пользователей из Excel...")
    
    # Данные из user_import.xlsx
    excel_users = [
        # Администраторы
        ('Никифорова Весения Николаевна', '94d5ous@gmail.com', 'uzWC67', 'Администратор'),
        ('Сазонов Руслан Германович', 'uth4iz@mail.com', '2L6KZG', 'Администратор'),
        ('Одинцов Серафим Артёмович', 'yzls62@outlook.com', 'JlFRCZ', 'Администратор'),
        
        # Менеджеры
        ('Степанов Михаил Артёмович', '1diph5e@tutanota.com', '8ntwUp', 'Менеджер'),
        ('Ворсин Петр Евгеньевич', 'tjde7c@yahoo.com', 'YOyhfR', 'Менеджер'),
        ('Старикова Елена Павловна', 'wpmrc3do@tutanota.com', 'RSbvHv', 'Менеджер'),
        
        # Клиенты
        ('Михайлюк Анна Вячеславовна', '5d4zbu@tutanota.com', 'rwVDh9', 'Авторизированный клиент'),
        ('Ситдикова Елена Анатольевна', 'ptec8ym@yahoo.com', 'LdNyos', 'Авторизированный клиент'),
        ('Ворсин Петр Евгеньевич', '1qz4kw@mail.com', 'gynQMT', 'Авторизированный клиент'),
        ('Старикова Елена Павловна', '4np6se@mail.com', 'AtnDjr', 'Авторизированный клиент'),
    ]
    
    roles = {
        'Администратор': Role.objects.get(name='Администратор'),
        'Менеджер': Role.objects.get(name='Менеджер'),
        'Авторизированный клиент': Role.objects.get(name='Авторизированный клиент'),
    }
    
    created_count = 0
    for full_name, login, password, role_name in excel_users:
        name_parts = full_name.split()
        last_name = name_parts[0] if len(name_parts) > 0 else ''
        first_name = name_parts[1] if len(name_parts) > 1 else ''
        middle_name = name_parts[2] if len(name_parts) > 2 else ''
        
        user, created = User.objects.get_or_create(
            username=login,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'middle_name': middle_name,
                'role': roles[role_name],
                'email': login,
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            created_count += 1
            print(f"  ✅ Создан: {full_name} ({login} / {password})")
    
    print(f"  Создано пользователей из Excel: {created_count}")

if __name__ == '__main__':
    create_users()
    create_from_excel_users()
    list_users()