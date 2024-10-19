from django.urls import reverse_lazy
from django.views.generic import TemplateView, View
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, InventoryItemForm
from inventory_management.settings import LOW_QUANTITY
from .models import InventoryItem, Requisition, RequisitionItem
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Sum



class Index(TemplateView):
	template_name = 'auth/index.html'

class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        requisitions = Requisition.objects.filter(user=request.user).order_by('-date_created')
        return render(request, 'inventory/dashboard.html',{'requisitions': requisitions})
    
class RequisitionDetailView(LoginRequiredMixin, View):
    def get(self, request, requisition_id):
        requisition = get_object_or_404(Requisition, id=requisition_id, user=request.user)
        return render(request, 'inventory/requisition_detail.html', {'requisition': requisition})

    
class RequisitionView(LoginRequiredMixin, View):
    def get(self, request):
        items = InventoryItem.objects.order_by('id')

        low_inventory_ids = InventoryItem.objects.filter(
			quantity__lte=LOW_QUANTITY
		).values_list('id', flat=True)
        
        return render(request, 'inventory/requisition.html', {'items': items, 'low_inventory_ids': low_inventory_ids})
    

class SubmitRequisition(LoginRequiredMixin, View):
    def post(self, request):
        quantities = {}
        for key, value in request.POST.items():
            if key.startswith('quantities_'):
                item_id = key.split('_')[1]  # Extract item ID
                try:
                    quantity = int(value)
                    print(quantity)
                    if quantity > 0:
                        quantities[int(item_id)] = quantity  # Store the item ID and quantity
                except ValueError:
                    continue  # Ignore invalid quantities

        if not quantities:
            messages.error(request, "No items were selected.")
            return redirect('requisition')

        # Create the requisition
        requisition = Requisition.objects.create(user=request.user)

        # Create requisition items
        for item_id, quantity in quantities.items():
            try:
                item = InventoryItem.objects.get(id=item_id)
                RequisitionItem.objects.create(requisition=requisition, inventory_item=item, quantity_requested=quantity)
            except InventoryItem.DoesNotExist:
                continue  # Handle case where item doesn't exist

        messages.success(request, "Requisition submitted successfully!")
        return redirect('dashboard')


@method_decorator(staff_member_required, name='dispatch')
class ApproveRequisitionView(LoginRequiredMixin, View):
    def get(self, request, requisition_id):
        requisition = get_object_or_404(Requisition, id=requisition_id)

        # Check if the requisition status is approved or rejected
        if requisition.status in ['Approved', 'Rejected']:
            messages.error(request, "This requisition has already been approved or rejected and cannot be edited.")
            return redirect('requisition_list')  # Redirect to requisition list

        return render(request, 'inventory/approve_requisition.html', {'requisition': requisition})

    def post(self, request, requisition_id):
        requisition = get_object_or_404(Requisition, id=requisition_id)

        # Check if the requisition status is approved or rejected
        if requisition.status in ['Approved', 'Rejected']:
            messages.error(request, "This requisition has already been approved or rejected and cannot be edited.")
            return redirect('requisition_list')  # Redirect to requisition list

        # Process approved quantities and update inventory
        for item in requisition.items.all():
            approved_quantity = request.POST.get(f'approved_quantity_{item.id}')
            if approved_quantity is not None:
                try:
                    approved_quantity = int(approved_quantity)
                    if approved_quantity >= 0:
                        item.quantity_approved = approved_quantity  # Update the approved quantity
                        item.save()
                        
                        # Subtract approved quantity from the actual inventory
                        inventory_item = get_object_or_404(InventoryItem, id=item.inventory_item.id)
                        inventory_item.quantity -= approved_quantity  # Subtract approved quantity
                        inventory_item.save()
                except ValueError:
                    continue  # Ignore invalid inputs

        requisition.status = 'Approved'
        requisition.save()
        messages.success(request, "Requisition approved successfully!")
        return redirect('requisition_list')  # Redirect to the requisition list page

class RequisitionListView(LoginRequiredMixin, View):
    def get(self, request):
        requisitions = Requisition.objects.all().order_by('-date_created')
        return render(request, 'admin/requisition_list.html', {'requisitions': requisitions})

@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        # Get all requisitions
        requisitions = Requisition.objects.all().order_by('-date_created')
        return render(request, 'admin/admin_dashboard.html', {'requisitions': requisitions})



@method_decorator(staff_member_required, name='dispatch')
class AddInventoryItemView(LoginRequiredMixin, View):
    def get(self, request):
        form = InventoryItemForm()
        return render(request, 'admin/add_inventory_item.html', {'form': form})

    def post(self, request):
        form = InventoryItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "New inventory item added successfully!")
            return redirect('admin_dashboard')  # Redirect to admin dashboard or another page
        return render(request, 'admin/add_inventory_item.html', {'form': form})


class StatisticsView(View):
    def get(self, request):
        # Query to get total approved quantity per inventory item
        item_stats = RequisitionItem.objects.filter(
            requisition__status='Approved'
        ).values('inventory_item__id', 'inventory_item__name')\
         .annotate(total_approved=Sum('quantity_approved'))\
         .order_by('inventory_item__name')

        return render(request, 'admin/statistics.html', {'item_stats': item_stats})
    
class StatItemDetailView(View):
    def get(self, request, item_id):
        # Get the specific inventory item
        item = get_object_or_404(InventoryItem, id=item_id)
        
        # Query to get approved quantities per user for this specific item
        user_approved_stats = RequisitionItem.objects.filter(
            requisition__status='Approved',
            inventory_item=item
        ).values('requisition__user__username')\
         .annotate(total_approved=Sum('quantity_approved'))\
         .order_by('requisition__user__username')

        return render(request, 'admin/stat_details.html', {
            'item': item,
            'user_approved_stats': user_approved_stats
        })

class SignUpView(View):
	def get(self, request):
		form = UserRegisterForm()
		return render(request, 'auth/signup.html', {'form': form})

	def post(self, request):
		form = UserRegisterForm(request.POST)

		if form.is_valid():
			form.save()
			user = authenticate(
				username=form.cleaned_data['username'],
				password=form.cleaned_data['password1']
			)

			login(request, user)
			return redirect('index')

		return render(request, 'auth/signup.html', {'form': form})
