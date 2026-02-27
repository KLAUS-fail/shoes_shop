from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Product, Supplier
from .forms import ProductForm
from orders.models import OrderItem
import os

def product_list(request):
    """Отображение списка товаров с фильтрацией и сортировкой"""
    
    products = Product.objects.select_related(
        'category', 'manufacturer', 'supplier', 'unit'
    ).all()
    
    search_query = request.GET.get('search', '')
    supplier_id = request.GET.get('supplier', '')
    sort_by = request.GET.get('sort', '')
    
    user_role = None
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        user_role = request.user.role.name if request.user.role else None
    
    if user_role in ['Менеджер', 'Администратор']:
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(manufacturer__name__icontains=search_query) |
                Q(supplier__name__icontains=search_query)
            )
        
        # Фильтр по поставщику
        if supplier_id and supplier_id != 'all':
            products = products.filter(supplier_id=supplier_id)
        
        # Сортировка
        if sort_by == 'stock_asc':
            products = products.order_by('stock_quantity')
        elif sort_by == 'stock_desc':
            products = products.order_by('-stock_quantity')
    
    suppliers = Supplier.objects.all()
    
    context = {
        'products': products,
        'suppliers': suppliers,
        'search_query': search_query,
        'selected_supplier': supplier_id,
        'selected_sort': sort_by,
        'user_role': user_role,
        'is_admin': user_role == 'Администратор',
        'is_manager': user_role == 'Менеджер',
    }
    return render(request, 'catalog/product_list.html', context)

@login_required
def product_add(request):
    """Добавление нового товара (только для админа)"""
    
    # Проверяем права доступа
    if not (hasattr(request.user, 'role') and request.user.role and request.user.role.name == 'Администратор'):
        messages.error(request, 'У вас нет прав для добавления товаров')
        return redirect('product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.name}" успешно добавлен')
            return redirect('product_list')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = ProductForm()
    
    return render(request, 'catalog/product_form.html', {
        'form': form,
        'title': 'Добавление товара'
    })

@login_required
def product_edit(request, pk):
    """Редактирование товара (только для админа)"""
    
    # Проверяем права доступа
    if not (hasattr(request.user, 'role') and request.user.role and request.user.role.name == 'Администратор'):
        messages.error(request, 'У вас нет прав для редактирования товаров')
        return redirect('product_list')
    
    product = get_object_or_404(Product, pk=pk)
    old_photo = product.photo
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Если загружено новое фото, удаляем старое
            if 'photo' in request.FILES and old_photo:
                if os.path.isfile(old_photo.path):
                    os.remove(old_photo.path)
            
            product = form.save()
            messages.success(request, f'Товар "{product.name}" успешно обновлен')
            return redirect('product_list')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'catalog/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Редактирование товара: {product.name}'
    })

@login_required
def product_delete(request, pk):
    """Удаление товара (только для админа)"""
    
    # Проверяем права доступа
    if not (hasattr(request.user, 'role') and request.user.role and request.user.role.name == 'Администратор'):
        messages.error(request, 'У вас нет прав для удаления товаров')
        return redirect('product_list')
    
    product = get_object_or_404(Product, pk=pk)
    
    # Проверяем, есть ли товар в заказах
    if OrderItem.objects.filter(product=product).exists():
        messages.error(request, f'Товар "{product.name}" нельзя удалить, так как он присутствует в заказах')
        return redirect('product_list')
    
    if request.method == 'POST':
        # Удаляем фото
        if product.photo:
            if os.path.isfile(product.photo.path):
                os.remove(product.photo.path)
        
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успешно удален')
        return redirect('product_list')
    
    return render(request, 'catalog/product_confirm_delete.html', {
        'product': product
    })