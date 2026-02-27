import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoeproject.settings')
django.setup()

from django.db import connection
from django.conf import settings
import shutil

def clear_all_data():
    """Полная очистка всех данных в базе"""
    
    print("=" * 60)
    print("🧹 ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    # Подтверждение
    print("\n⚠️  ВНИМАНИЕ! Это удалит ВСЕ данные из базы!")
    print("Будут удалены:")
    print("  • Все пользователи (кроме суперпользователя)")
    print("  • Все товары")
    print("  • Все категории, производители, поставщики")
    print("  • Все заказы и позиции заказов")
    print("  • Все пункты выдачи")
    print("  • Все фото товаров из папки media/products/")
    
    response = input("\nПродолжить? (да/нет): ")
    if response.lower() not in ['да', 'yes', 'y', 'д']:
        print("❌ Операция отменена")
        return
    
    print("\n🔄 Начинаем очистку...")
    
    # Порядок удаления важен из-за внешних ключей
    try:
        # 1. Удаляем позиции заказов
        from orders.models import OrderItem
        count = OrderItem.objects.all().delete()[0]
        print(f"  ✓ Удалено позиций заказов: {count}")
        
        # 2. Удаляем заказы
        from orders.models import Order
        count = Order.objects.all().delete()[0]
        print(f"  ✓ Удалено заказов: {count}")
        
        # 3. Удаляем пункты выдачи
        from orders.models import PickupPoint
        count = PickupPoint.objects.all().delete()[0]
        print(f"  ✓ Удалено пунктов выдачи: {count}")
        
        # 4. Удаляем товары
        from catalog.models import Product
        count = Product.objects.all().delete()[0]
        print(f"  ✓ Удалено товаров: {count}")
        
        # 5. Удаляем категории
        from catalog.models import Category
        count = Category.objects.all().delete()[0]
        print(f"  ✓ Удалено категорий: {count}")
        
        # 6. Удаляем производителей
        from catalog.models import Manufacturer
        count = Manufacturer.objects.all().delete()[0]
        print(f"  ✓ Удалено производителей: {count}")
        
        # 7. Удаляем поставщиков
        from catalog.models import Supplier
        count = Supplier.objects.all().delete()[0]
        print(f"  ✓ Удалено поставщиков: {count}")
        
        # 8. Удаляем единицы измерения
        from catalog.models import Unit
        count = Unit.objects.all().delete()[0]
        print(f"  ✓ Удалено единиц измерения: {count}")
        
        # 9. Удаляем пользователей (кроме суперпользователя)
        from accounts.models import User
        # Сохраняем суперпользователя если он есть
        super_users = User.objects.filter(is_superuser=True)
        other_users = User.objects.filter(is_superuser=False)
        
        count = other_users.delete()[0]
        print(f"  ✓ Удалено обычных пользователей: {count}")
        print(f"  ✓ Сохранено суперпользователей: {super_users.count()}")
        
        # 10. Удаляем роли (кроме базовых)
        from accounts.models import Role
        # Сохраняем базовые роли
        base_roles = ['Администратор', 'Менеджер', 'Авторизированный клиент', 'Гость']
        roles_to_delete = Role.objects.exclude(name__in=base_roles)
        count = roles_to_delete.delete()[0]
        print(f"  ✓ Удалено дополнительных ролей: {count}")
        print(f"  ✓ Сохранено базовых ролей: {len(base_roles)}")
        
        # 11. Очищаем папку с фото товаров
        media_products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        if os.path.exists(media_products_dir):
            # Удаляем все файлы в папке
            for filename in os.listdir(media_products_dir):
                file_path = os.path.join(media_products_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"  ✓ Удален файл: {filename}")
                except Exception as e:
                    print(f"  ⚠ Не удалось удалить {filename}: {e}")
            
            # Создаем .gitkeep чтобы папка не была пустой в репозитории
            with open(os.path.join(media_products_dir, '.gitkeep'), 'w') as f:
                f.write('')
            print(f"  ✓ Очищена папка: {media_products_dir}")
        
        print("\n✅ Очистка базы данных успешно завершена!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при очистке: {e}")
        import traceback
        traceback.print_exc()

def clear_all_and_reset_ids():
    """Полная очистка и сброс автоинкремента"""
    
    print("=" * 60)
    print("🧹 ПОЛНАЯ ОЧИСТКА СО СБРОСОМ ID")
    print("=" * 60)
    
    # Сначала очищаем данные
    clear_all_data()
    
    # Сбрасываем последовательности (для PostgreSQL)
    if 'postgresql' in settings.DATABASES['default']['ENGINE']:
        print("\n🔄 Сброс последовательностей PostgreSQL...")
        with connection.cursor() as cursor:
            tables = [
                'users', 'roles',
                'products', 'categories', 'manufacturers', 'suppliers', 'units',
                'orders', 'order_items', 'pickup_points'
            ]
            for table in tables:
                try:
                    cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;")
                    print(f"  ✓ Сброшена последовательность для {table}")
                except:
                    pass
    
    print("\n✅ Полная очистка со сбросом ID завершена!")

if __name__ == '__main__':
    print("Выберите режим очистки:")
    print("1 - Обычная очистка (сохраняет структуру)")
    print("2 - Полная очистка со сбросом ID")
    
    choice = input("\nВаш выбор (1/2): ").strip()
    
    if choice == '2':
        clear_all_and_reset_ids()
    else:
        clear_all_data()