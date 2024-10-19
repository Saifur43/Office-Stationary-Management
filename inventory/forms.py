from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import InventoryItem
from django.forms.widgets import DateInput
from django.contrib.auth.forms import AuthenticationForm

class UserRegisterForm(UserCreationForm):
	email = forms.EmailField()

	class Meta:
		model = User
		fields = ['username', 'email', 'password1', 'password2']


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'reference_no', 'unit', 'quantity', 'category', 'date_created', 'remarks', 'reference_pdf']
        widgets = {
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }




