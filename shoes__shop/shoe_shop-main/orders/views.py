from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Order, OrderItem
from .forms import OrderForm, OrderItemFormSet
from catalog.models import Product

@login_required
def order_list(request):
    """Список заказов (для менеджера и админа)"""
    
    # Проверяем права
    user_role = None
    if hasattr(request.user, 'role') and request.user.role:
        user_role = request.user.role.name
    
    if user_role not in ['Менеджер', 'Администратор']:
        messages.error(request, 'У вас нет прав для просмотра заказов')
        return redirect('product_list')
    
    # Получаем все заказы с связанными данными
    orders = Order.objects.all().select_related('user').prefetch_related('items__product')
    
    # Поиск по заказам
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(user__last_name__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Фильтр по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Сортировка (по умолчанию - новые сверху)
    orders = orders.order_by('-order_date')
    
    context = {
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'is_admin': user_role == 'Администратор',
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail(request, pk):
    """Детали заказа"""
    
    user_role = None
    if hasattr(request.user, 'role') and request.user.role:
        user_role = request.user.role.name
    
    if user_role not in ['Менеджер', 'Администратор']:
        messages.error(request, 'У вас нет прав для просмотра заказов')
        return redirect('product_list')
    
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'is_admin': user_role == 'Администратор',
    })


@login_required
def order_add(request):
    """Добавление заказа (только админ)"""
    
    # Проверка прав
    if not (hasattr(request.user, 'role') and request.user.role and request.user.role.name == 'Администратор'):
        messages.error(request, 'У вас нет прав для добавления заказов')
        return redirect('order_list')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            formset = OrderItemFormSet(request.POST, instance=order)
            
            if formset.is_valid():
                # Сохраняем позиции заказа
                formset.save()
                
                # Обновляем количество товаров на складе
                for item in order.items.all():
                    product = item.product
                    if product.stock_quantity >= item.quantity:
                        product.stock_quantity -= item.quantity
                        product.save()
                    else:
                        # Если товара недостаточно, удаляем заказ и показываем ошибку
                        order.delete()
                        messages.error(request, f'Недостаточно товара "{product.name}" на складе')
                        return redirect('order_add')
                
                messages.success(request, f'Заказ №{order.id} успешно создан')
                return redirect('order_detail', pk=order.pk)
            else:
                # Если форма невалидна, удаляем созданный заказ
                order.delete()
        else:
            # Если форма невалидна, показываем ошибки
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
    
    return render(request, 'orders/order_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Создание нового заказа'
    })


@login_required
def order_edit(request, pk):
    """Редактирование заказа (только админ)"""
    
    # Проверка прав
    if not (hasattr(request.user, 'role') and request.user.role and request.user.role.name == 'Администратор'):
        messages.error(request, 'У вас нет прав для редактирования заказов')
        return redirect('order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            # Сохраняем изменения в заказе
            order = form.save()
            
            # Получаем текущие позиции до обновления
            old_items = {item.product_id: item.quantity for item in order.items.all()}
            
            formset = OrderItemFormSet(request.POST, instance=order)
            if formset.is_valid():
                # Возвращаем товары на склад (откатываем старые изменения)
                for product_id, quantity in old_items.items():
                    try:
                        product = Product.objects.get(pk=product_id)
                        product.stock_quantity += quantity
                        product.save()
                    except Product.DoesNotExist:
                        pass
                
                # Сохраняем новые позиции
                formset.save()
                
                # Обновляем количество товаров на складе с новыми значениями
                for item in order.items.all():
                    product = item.product
                    if product.stock_quantity >= item.quantity:
                        product.stock_quantity -= item.quantity
                        product.save()
                    else:
                        # Если товара недостаточно, показываем ошибку
                        messages.error(request, f'Недостаточно товара "{product.name}" на складе')
                        return redirect('order_edit', pk=order.pk)
                
                messages.success(request, f'Заказ №{order.id} успешно обновлен')
                return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    
    return render(request, 'orders/order_form.html', {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f'Редактирование заказа №{order.id}'
    })


@login_required
def order_delete(request, pk):
    """Удаление заказа (только админ)"""
    
    # Проверка прав
    if not (hasattr(request.user, 'role') and request.user.role and request.user.role.name == 'Администратор'):
        messages.error(request, 'У вас нет прав для удаления заказов')
        return redirect('order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        # Возвращаем товары на склад
        for item in order.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save()
        
        # Удаляем заказ
        order.delete()
        messages.success(request, f'Заказ №{order.id} успешно удален')
        return redirect('order_list')
    
    return render(request, 'orders/order_confirm_delete.html', {'order': order})


@login_required
def order_status_update(request, pk):
    """Быстрое обновление статуса заказа (для менеджера и админа)"""
    
    user_role = None
    if hasattr(request.user, 'role') and request.user.role:
        user_role = request.user.role.name
    
    if user_role not in ['Менеджер', 'Администратор']:
        messages.error(request, 'У вас нет прав для изменения статуса заказов')
        return redirect('order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save()
            messages.success(
                request, 
                f'Статус заказа №{order.id} изменен с "{order.get_status_display(old_status)}" на "{order.get_status_display()}"'
            )
        else:
            messages.error(request, 'Некорректный статус')
    
    return redirect('order_detail', pk=order.pk)

@login_required
def order_status_update(request, pk):
    """Быстрое обновление статуса заказа"""
    
    user_role = None
    if hasattr(request.user, 'role') and request.user.role:
        user_role = request.user.role.name
    
    if user_role not in ['Менеджер', 'Администратор']:
        messages.error(request, 'У вас нет прав для изменения статуса заказов')
        return redirect('order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Получаем человекочитаемое название статуса
            status_display = dict(Order.STATUS_CHOICES).get(new_status, new_status)
            
            messages.success(
                request, 
                f'Статус заказа №{order.id} изменен на "{status_display}"'
            )
        else:
            messages.error(request, 'Некорректный статус')
    
    return redirect('order_detail', pk=order.pk)