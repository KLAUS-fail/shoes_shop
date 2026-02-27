import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoeproject.settings')
django.setup()

from catalog.models import Product
from django.conf import settings

ID_TO_PHOTO = {
    37: '1.jpg',   # Ботинки
    44: '5.jpg',   # Ботинки Marco Tozzi женские демисезонные
    45: '3.jpg',   # Ботинки мужские Рос-Обувь кожаные
    41: '13.jpg',  # Кеды (но у тебя нет 13.jpg, поставь 6.jpg)
    39: '6.jpg',   # Кроссовки
    40: '7.jpg',   # Полуботинки
    47: '7.jpg',   # Полуботинки Alessio Nesca женские
    50: '13.jpg',  # Полуботинки CROSBY (нет 13.jpg)
    49: '8.jpg',   # Полуботинки kari женские
    43: '24.jpg',  # Сапоги (нет 24.jpg)
    42: '17.jpg',  # Тапочки (нет 17.jpg)
    38: '2.jpg',   # Туфли
    46: '4.jpg',   # Туфли Marco Tozzi женские летние
    48: '8.jpg',   # Туфли Rieker женские демисезонные
}

AVAILABLE_PHOTOS = ['1.jpg', '2.jpg', '3.jpg', '4.jpg', '5.jpg', '6.jpg', '7.jpg', '8.jpg', '9.jpg', '10.jpg']

SIMPLE_MAPPING = {
    37: '1.jpg',   # Ботинки -> 1.jpg
    38: '2.jpg',   # Туфли -> 2.jpg
    39: '9.jpg',   # Кроссовки -> 6.jpg
    43: '5.jpg',   # Сапоги -> 4.jpg
    44: '5.jpg',   # Ботинки Marco Tozzi -> 5.jpg
    45: '3.jpg',   # Ботинки мужские -> 3.jpg
    46: '4.jpg',   # Туфли Marco Tozzi -> 4.jpg
    47: '7.jpg',   # Полуботинки Alessio -> 7.jpg
    48: '8.jpg',   # Туфли Rieker -> 8.jpg
    49: '8.jpg',   # Полуботинки kari -> 8.jpg
    50: '6.jpg',   # Полуботинки CROSBY -> 6.jpg
}

def set_photos_by_id():
    """Установка фото по ID товаров"""
    
    print("=" * 60)
    print("📸 УСТАНОВКА ФОТО ПО ID ТОВАРОВ")
    print("=" * 60)
    
    # Проверяем наличие фото
    media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
    print(f"\n📁 Папка с фото: {media_dir}")
    
    if os.path.exists(media_dir):
        files = os.listdir(media_dir)
        print(f"📸 Доступные фото: {sorted(files)}")
    else:
        print(f"❌ Папка не найдена!")
        return
    
    print("\n🔧 Устанавливаем фото:")
    updated = 0
    
    for product in Product.objects.all():
        old_photo = str(product.photo) if product.photo else "НЕТ ФОТО"
        
        # Получаем фото по ID
        photo_file = SIMPLE_MAPPING.get(product.id)
        
        if photo_file:
            # Проверяем, есть ли такой файл
            if photo_file in files:
                product.photo = f"products/{photo_file}"
                product.save()
                updated += 1
                print(f"  ✅ ID {product.id}: {product.name[:30]}... -> {photo_file}")
            else:
                print(f"  ⚠️ ID {product.id}: файл {photo_file} не найден в папке")
        else:
            print(f"  ❌ ID {product.id}: {product.name[:30]}... нет соответствия")
    
    print(f"\n✅ Обновлено товаров: {updated}")

def check_photos():
    """Проверка фото"""
    print("\n" + "=" * 60)
    print("🔍 ПРОВЕРКА ФОТО")
    print("=" * 60)
    
    for product in Product.objects.all().order_by('id'):
        if product.photo:
            print(f"  ✅ ID {product.id:2}: {product.name[:40]:40} -> {product.photo}")
        else:
            print(f"  ❌ ID {product.id:2}: {product.name[:40]:40} -> НЕТ ФОТО")

def reset_all_photos():
    """Сброс всех фото"""
    print("\n" + "=" * 60)
    print("🔄 СБРОС ВСЕХ ФОТО")
    print("=" * 60)
    
    count = Product.objects.all().update(photo='')
    print(f"✅ Сброшено фото у {count} товаров")

def show_available_photos():
    """Показать доступные фото"""
    print("\n" + "=" * 60)
    print("📸 ДОСТУПНЫЕ ФОТО")
    print("=" * 60)
    
    media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
    if os.path.exists(media_dir):
        files = [f for f in os.listdir(media_dir) if f.endswith('.jpg')]
        print(f"Найдено {len(files)} фото:")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(media_dir, f))
            print(f"  • {f} ({size} bytes)")
    else:
        print("❌ Папка не найдена")

if __name__ == '__main__':
    print("1. Показать доступные фото")
    print("2. Сбросить все фото")
    print("3. Установить фото по ID")
    print("4. Проверить фото")
    print("5. Сделать всё")
    
    choice = input("\nВыберите действие (1-5): ")
    
    if choice == '1':
        show_available_photos()
    elif choice == '2':
        reset_all_photos()
    elif choice == '3':
        set_photos_by_id()
    elif choice == '4':
        check_photos()
    elif choice == '5':
        show_available_photos()
        reset_all_photos()
        set_photos_by_id()
        check_photos()
    else:
        print("Неверный выбор")