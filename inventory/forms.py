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

class ReportForm(forms.Form):
    # Exclude staff members from the user dropdown
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),  # Exclude staff members
        required=False,
        label="User",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Use the full queryset but display only the item names in the dropdown
    item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.all(),  # Full queryset
        required=False,
        label="Item",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Add date fields
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label="From Date"
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label="To Date"
    )

class AddInventoryItemForm(forms.Form):
    existing_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.all(),
        required=True,
        label="Select Item",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reference_no = forms.CharField(
        max_length=200,
        required=True,
        label="Reference Number",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        label="Quantity to Add",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )








