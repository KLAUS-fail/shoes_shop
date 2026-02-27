import os
import sys
import django
import pandas as pd
from datetime import datetime, timedelta
import shutil

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoeproject.settings')
django.setup()

# Импорт моделей Django
from django.contrib.auth.hashers import make_password
from django.conf import settings
from accounts.models import Role, User
from catalog.models import Category, Manufacturer, Supplier, Unit, Product
from orders.models import Order, OrderItem

# ============================================
# КОНСТАНТЫ И ПУТИ
# ============================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'import')
MEDIA_PRODUCTS_DIR = os.path.join(settings.MEDIA_ROOT, 'products')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

FILES = {
    'users': os.path.join(DATA_DIR, 'user_import.xlsx'),
    'products': os.path.join(DATA_DIR, 'Tovar.xlsx'),
    'pickup': os.path.join(DATA_DIR, 'Пункты выдачи_import.xlsx'),
    'orders': os.path.join(DATA_DIR, 'Заказ_import.xlsx'),
}

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def print_header(text):
    """Вывод заголовка"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_success(text):
    """Вывод успешного сообщения"""
    print(f"  ✅ {text}")

def print_warning(text):
    """Вывод предупреждения"""
    print(f"  ⚠️ {text}")

def print_error(text):
    """Вывод ошибки"""
    print(f"  ❌ {text}")

def clean_text(text):
    """Очистка текста от NaN и лишних пробелов"""
    if pd.isna(text):
        return ''
    return str(text).strip()

def check_files():
    """Проверка наличия всех файлов"""
    print_header("ПРОВЕРКА ФАЙЛОВ")
    
    all_exist = True
    for name, path in FILES.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✓ {name}: {os.path.basename(path)} ({size} bytes)")
        else:
            print(f"  ✗ {name}: файл не найден по пути {path}")
            all_exist = False
    
    return all_exist

# ============================================
# 1. ИМПОРТ РОЛЕЙ
# ============================================

def import_roles():
    """Создание базовых ролей"""
    print_header("1. СОЗДАНИЕ РОЛЕЙ")
    
    roles_data = ['Администратор', 'Менеджер', 'Авторизированный клиент', 'Гость']
    created_count = 0
    
    for role_name in roles_data:
        role, created = Role.objects.get_or_create(name=role_name)
        if created:
            created_count += 1
            print_success(f"Создана роль: {role_name}")
    
    print_success(f"Всего ролей: {Role.objects.count()}")

# ============================================
# 2. ИМПОРТ ПОЛЬЗОВАТЕЛЕЙ
# ============================================

def import_users():
    """Импорт пользователей из Excel"""
    print_header("2. ИМПОРТ ПОЛЬЗОВАТЕЛЕЙ")
    
    try:
        df = pd.read_excel(FILES['users'])
        print(f"  Найдено записей: {len(df)}")
        
        # Получаем все роли
        roles = {role.name: role for role in Role.objects.all()}
        
        created_count = 0
        for idx, row in df.iterrows():
            try:
                role_name = clean_text(row.get('Роль сотрудника'))
                full_name = clean_text(row.get('ФИО'))
                login = clean_text(row.get('Логин'))
                password = clean_text(row.get('Пароль'))
                
                # Разбираем ФИО
                name_parts = full_name.split()
                last_name = name_parts[0] if len(name_parts) > 0 else ''
                first_name = name_parts[1] if len(name_parts) > 1 else ''
                middle_name = name_parts[2] if len(name_parts) > 2 else ''
                
                # Создаем пользователя
                user, created = User.objects.get_or_create(
                    username=login,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'middle_name': middle_name,
                        'role': roles.get(role_name),
                        'email': login,
                        'is_active': True,
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    created_count += 1
                    print_success(f"{full_name} ({role_name})")
                    
            except Exception as e:
                print_error(f"Строка {idx + 2}: {e}")
        
        print_success(f"Импортировано пользователей: {created_count}")
        
    except Exception as e:
        print_error(f"Ошибка при импорте пользователей: {e}")

# ============================================
# 3. ИМПОРТ ТОВАРОВ
# ============================================

def import_products():
    """Импорт товаров из Excel"""
    print_header("3. ИМПОРТ ТОВАРОВ")
    
    try:
        df = pd.read_excel(FILES['products'])
        print(f"  Найдено записей: {len(df)}")
        
        # Создаем единицу измерения
        unit, _ = Unit.objects.get_or_create(name='шт')
        
        # Словари для кэширования
        categories = {}
        manufacturers = {}
        suppliers = {}
        
        created_count = 0
        updated_count = 0
        
        # Соответствие артикулов и ID (будем заполнять)
        global article_product_map
        article_product_map = {}
        
        for idx, row in df.iterrows():
            try:
                # Категория
                cat_name = clean_text(row.get('Категория товара'))
                if cat_name not in categories:
                    cat, _ = Category.objects.get_or_create(name=cat_name)
                    categories[cat_name] = cat
                
                # Производитель
                man_name = clean_text(row.get('Производитель'))
                if man_name not in manufacturers:
                    man, _ = Manufacturer.objects.get_or_create(name=man_name)
                    manufacturers[man_name] = man
                
                # Поставщик
                sup_name = clean_text(row.get('Поставщик'))
                if sup_name not in suppliers:
                    sup, _ = Supplier.objects.get_or_create(name=sup_name)
                    suppliers[sup_name] = sup
                
                # Получаем артикул и название
                article = clean_text(row.get('Артикул'))
                name = clean_text(row.get('Наименование товара'))
                
                # Фото
                photo_file = clean_text(row.get('Фото', ''))
                photo_path = f"products/{photo_file}" if photo_file else ''
                
                # Цена и количество
                price = float(row.get('Цена', 0))
                stock = int(row.get('Кол-во на складе', 0))
                discount = float(row.get('Действующая скидка', 0))
                description = clean_text(row.get('Описание товара', ''))
                
                # Создаем или обновляем товар
                product, created = Product.objects.update_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'price': price,
                        'stock_quantity': stock,
                        'discount': discount,
                        'category': categories[cat_name],
                        'manufacturer': manufacturers[man_name],
                        'supplier': suppliers[sup_name],
                        'unit': unit,
                        'photo': photo_path,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                # Сохраняем соответствие артикула и ID товара
                if article:
                    article_product_map[article] = product.id
                
            except Exception as e:
                print_error(f"Строка {idx + 2}: {e}")
        
        print_success(f"Создано товаров: {created_count}")
        print_success(f"Обновлено товаров: {updated_count}")
        print_success(f"Всего товаров: {Product.objects.count()}")
        
    except Exception as e:
        print_error(f"Ошибка при импорте товаров: {e}")

# ============================================
# 4. КОПИРОВАНИЕ ФОТО
# ============================================

def copy_photos():
    """Копирование фото товаров из templates в media/products"""
    print_header("4. КОПИРОВАНИЕ ФОТО")
    
    # Создаем папку если её нет
    os.makedirs(MEDIA_PRODUCTS_DIR, exist_ok=True)
    
    # Ищем все фото в templates
    photo_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.JPG']
    photos_found = []
    
    for file in os.listdir(TEMPLATES_DIR):
        if any(file.lower().endswith(ext) for ext in photo_extensions):
            photos_found.append(file)
    
    print(f"  Найдено фото в templates: {len(photos_found)}")
    
    # Копируем каждое фото
    copied = 0
    for photo in photos_found:
        src = os.path.join(TEMPLATES_DIR, photo)
        dst = os.path.join(MEDIA_PRODUCTS_DIR, photo)
        
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            copied += 1
            print_success(f"Скопировано: {photo}")
    
    print_success(f"Скопировано новых фото: {copied}")
    print_success(f"Всего фото в media/products: {len(os.listdir(MEDIA_PRODUCTS_DIR))}")

# ============================================
# 5. ИМПОРТ ПУНКТОВ ВЫДАЧИ
# ============================================

def import_pickup_points():
    """Загрузка пунктов выдачи из Excel"""
    print_header("5. ЗАГРУЗКА ПУНКТОВ ВЫДАЧИ")
    
    try:
        df = pd.read_excel(FILES['pickup'], header=None)
        pickup_points = []
        
        for _, row in df.iterrows():
            address = clean_text(row[0])
            pickup_points.append(address)
        
        print_success(f"Загружено пунктов выдачи: {len(pickup_points)}")
        return pickup_points
        
    except Exception as e:
        print_error(f"Ошибка при загрузке пунктов выдачи: {e}")
        return []

# ============================================
# 6. ИМПОРТ ЗАКАЗОВ
# ============================================

def import_orders(pickup_points):
    """Импорт заказов с товарами и адресами"""
    print_header("6. ИМПОРТ ЗАКАЗОВ")
    
    try:
        df = pd.read_excel(FILES['orders'])
        print(f"  Найдено записей: {len(df)}")
        
        # Маппинг статусов
        status_map = {
            'Завершен': 'completed',
            'Новый': 'new',
            'В обработке': 'processing',
            'Отменён': 'cancelled'
        }
        
        # Получаем всех пользователей для быстрого поиска
        users = {}
        for user in User.objects.all():
            full_name = f"{user.last_name} {user.first_name} {user.middle_name or ''}".strip()
            users[full_name] = user
        
        print(f"  Пользователей в базе: {len(users)}")
        
        # Получаем все товары для быстрого поиска
        products = {p.id: p for p in Product.objects.all()}
        
        # Маппинг артикулов из Excel в ID товаров
        article_to_id = {
            'А112Т4': 37,  # Ботинки женские
            'F635R4': 44,  # Ботинки Marco Tozzi
            'H782T5': 38,  # Туфли мужские
            'G783F5': 45,  # Ботинки мужские Рос
            'J384T6': 40,  # Полуботинки мужские Rieker
            'D572U8': 39,  # Кроссовки мужские
            'F572H7': 46,  # Туфли Marco Tozzi женские
            'D329H3': 47,  # Полуботинки Alessio Nesca
            'B320R5': 48,  # Туфли Rieker женские
            'G432E4': 43,  # Сапоги
            'S213E3': 50,  # Полуботинки CROSBY
            'E482R4': 49,  # Полуботинки kari женские
        }
        
        # Удаляем старые заказы (если есть)
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        print("  Старые заказы удалены")
        
        order_count = 0
        item_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Получаем данные из строки
                excel_num = int(row.get('Номер заказа'))
                full_name = clean_text(row.get('ФИО авторизированного клиента'))
                items_str = row.get('Артикул заказа')
                order_date = row.get('Дата заказа')
                delivery_date = row.get('Дата доставки')
                pickup_idx = row.get('Адрес пункта выдачи')
                pickup_code = row.get('Код для получения')
                status = clean_text(row.get('Статус заказа'))
                
                # Получаем пользователя
                user = users.get(full_name)
                if not user:
                    print_warning(f"Пользователь не найден: {full_name}")
                    continue
                
                # Получаем адрес пункта выдачи
                address = ''
                if pickup_idx and str(pickup_idx).isdigit():
                    idx_num = int(pickup_idx) - 1
                    if 0 <= idx_num < len(pickup_points):
                        address = pickup_points[idx_num]
                
                # Обрабатываем даты
                if pd.isna(order_date):
                    order_date = datetime.now()
                if pd.isna(delivery_date):
                    delivery_date = None
                
                # Создаем заказ
                order = Order.objects.create(
                    id=excel_num,  # Используем ID из Excel
                    user=user,
                    order_date=order_date,
                    delivery_date=delivery_date,
                    pickup_point=address,
                    delivery_address=address,
                    pickup_code=str(pickup_code) if not pd.isna(pickup_code) else '',
                    status=status_map.get(status, 'new')
                )
                
                # Парсим товары
                parts = [p.strip() for p in str(items_str).split(',')]
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        article = parts[i]
                        quantity = int(parts[i + 1])
                        
                        # Получаем ID товара по артикулу
                        product_id = article_to_id.get(article)
                        if product_id and product_id in products:
                            product = products[product_id]
                            
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity,
                                price_at_order=product.price * (1 - product.discount/100)
                            )
                            item_count += 1
                        else:
                            print_warning(f"Товар не найден: {article}")
                
                order_count += 1
                print_success(f"Заказ №{order.id} для {full_name}")
                
            except Exception as e:
                print_error(f"Строка {idx + 2}: {e}")
        
        print_success(f"Импортировано заказов: {order_count}")
        print_success(f"Добавлено позиций: {item_count}")
        
    except Exception as e:
        print_error(f"Ошибка при импорте заказов: {e}")

# ============================================
# 7. СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================

def create_test_users():
    """Создание тестовых пользователей для входа"""
    print_header("7. СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")
    
    admin_role = Role.objects.get(name='Администратор')
    manager_role = Role.objects.get(name='Менеджер')
    client_role = Role.objects.get(name='Авторизированный клиент')
    
    # Администратор
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
        print_success("admin / admin123")
    
    # Менеджер
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
        print_success("manager / manager123")
    
    # Клиент
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
        print_success("client / client123")

# ============================================
# 8. ПРОВЕРКА РЕЗУЛЬТАТОВ
# ============================================

def check_results():
    """Проверка итогов импорта"""
    print_header("8. ПРОВЕРКА РЕЗУЛЬТАТОВ")
    
    print(f"\n📊 СТАТИСТИКА:")
    print(f"  • Ролей: {Role.objects.count()}")
    print(f"  • Пользователей: {User.objects.count()}")
    print(f"  • Категорий: {Category.objects.count()}")
    print(f"  • Производителей: {Manufacturer.objects.count()}")
    print(f"  • Поставщиков: {Supplier.objects.count()}")
    print(f"  • Товаров: {Product.objects.count()}")
    print(f"  • Заказов: {Order.objects.count()}")
    print(f"  • Позиций в заказах: {OrderItem.objects.count()}")
    
    print(f"\n📦 ПОСЛЕДНИЕ ЗАКАЗЫ:")
    for order in Order.objects.all().order_by('-id')[:5]:
        items_count = order.items.count()
        print(f"  • Заказ №{order.id}: {order.user.get_full_name()} - {items_count} товаров")
        
    print(f"\n🔑 ТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ:")
    print(f"  • Админ: admin / admin123")
    print(f"  • Менеджер: manager / manager123")
    print(f"  • Клиент: client / client123")

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Главная функция импорта"""
    print("\n" + "="*60)
    print(" 🚀 ПОЛНЫЙ ИМПОРТ ДАННЫХ МАГАЗИНА ОБУВИ")
    print("="*60)
    
    # Проверяем файлы
    if not check_files():
        print_error("\nНе все файлы найдены! Импорт прерван.")
        return
    
    # Выполняем все шаги
    import_roles()
    import_users()
    import_products()
    copy_photos()
    pickup_points = import_pickup_points()
    import_orders(pickup_points)
    create_test_users()
    check_results()
    
    print("\n" + "="*60)
    print(" ✅ ИМПОРТ УСПЕШНО ЗАВЕРШЕН!")
    print("="*60)
    print("\n🚀 Запусти сервер: python manage.py runserver")
    print("🌐 Открой браузер: http://127.0.0.1:8000/")
    print("👑 Войди как admin / admin123")

if __name__ == '__main__':
    main()