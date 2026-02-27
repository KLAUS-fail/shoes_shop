from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Role, User

def login_view(request):
    """Страница входа"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name()}!')
            return redirect('product_list')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')

def guest_login(request):
    """Вход как гость"""
    guest_role, _ = Role.objects.get_or_create(name='Гость')
    
    guest_user, created = User.objects.get_or_create(
        username='guest',
        defaults={
            'first_name': 'Гостевой',
            'last_name': 'Пользователь',
            'role': guest_role,
            'is_active': True
        }
    )
    
    if created:
        guest_user.set_unusable_password()
        guest_user.save()
    
    from django.contrib.auth import backends
    guest_user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, guest_user)
    
    messages.info(request, 'Вы вошли как гость')
    return redirect('product_list')