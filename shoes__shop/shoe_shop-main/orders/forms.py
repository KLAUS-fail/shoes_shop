from django import forms
from .models import Order, OrderItem
from catalog.models import Product
from accounts.models import User

class OrderForm(forms.ModelForm):
    """Форма для создания/редактирования заказа"""
    
    class Meta:
        model = Order
        fields = ['user', 'status']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['user'].label = 'Клиент'
        self.fields['status'].label = 'Статус'

class OrderItemForm(forms.ModelForm):
    """Форма для позиции заказа"""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(stock_quantity__gt=0)
        self.fields['product'].label = 'Товар'
        self.fields['quantity'].label = 'Количество'
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')
        
        if product and quantity:
            if quantity > product.stock_quantity:
                raise forms.ValidationError(
                    f'Доступно только {product.stock_quantity} {product.unit.name}'
                )
        return quantity

OrderItemFormSet = forms.inlineformset_factory(
    Order, 
    OrderItem, 
    form=OrderItemForm,
    extra=3, 
    can_delete=True, 
    min_num=1, 
    validate_min=True
)