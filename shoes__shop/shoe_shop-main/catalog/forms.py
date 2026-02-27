from django import forms
from .models import Product, Category, Manufacturer, Supplier, Unit
from PIL import Image
import os

class ProductForm(forms.ModelForm):
    """Форма для добавления и редактирования товаров"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'stock_quantity', 'discount',
            'category', 'manufacturer', 'supplier', 'unit', 'photo'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Заполняем выпадающие списки
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].widget.attrs.update({'class': 'form-select'})
        
        self.fields['manufacturer'].queryset = Manufacturer.objects.all()
        self.fields['manufacturer'].widget.attrs.update({'class': 'form-select'})
        
        self.fields['supplier'].queryset = Supplier.objects.all()
        self.fields['supplier'].widget.attrs.update({'class': 'form-select'})
        
        self.fields['unit'].queryset = Unit.objects.all()
        self.fields['unit'].widget.attrs.update({'class': 'form-select'})
        
        self.fields['photo'].widget.attrs.update({'class': 'form-control'})
        
        # Делаем поля обязательными
        self.fields['category'].required = True
        self.fields['manufacturer'].required = True
        self.fields['supplier'].required = True
        self.fields['unit'].required = True
    
    def clean_price(self):
        """Проверка цены"""
        price = self.cleaned_data.get('price')
        if price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной')
        return price
    
    def clean_stock_quantity(self):
        """Проверка количества"""
        quantity = self.cleaned_data.get('stock_quantity')
        if quantity < 0:
            raise forms.ValidationError('Количество не может быть отрицательным')
        return quantity
    
    def clean_discount(self):
        """Проверка скидки"""
        discount = self.cleaned_data.get('discount')
        if discount < 0 or discount > 100:
            raise forms.ValidationError('Скидка должна быть от 0 до 100%')
        return discount
    
    def clean_photo(self):
        """Обработка фото"""
        photo = self.cleaned_data.get('photo')
        
        if photo and hasattr(photo, 'size'):
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Размер фото не должен превышать 5MB')
        
        return photo