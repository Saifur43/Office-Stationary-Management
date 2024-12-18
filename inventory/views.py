from django.urls import reverse_lazy
from django.views.generic import TemplateView, View
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, InventoryItemForm, ReportForm, AddInventoryItemForm
from inventory_management.settings import LOW_QUANTITY
from .models import InventoryItem, Requisition, RequisitionItem, UpdateLog, RequisitionApprovalLog
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
from django.template.loader import get_template
from django.db.models import Q
from .models import Requisition, User
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
import logging
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)


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
            return redirect('requisition_list')  

        return render(request, 'admin/approve_requisition.html', {'requisition': requisition})

    def post(self, request, requisition_id):
        requisition = get_object_or_404(Requisition, id=requisition_id)

        # Check if the requisition status is approved or rejected
        if requisition.status in ['Approved', 'Rejected']:
            messages.error(request, "This requisition has already been approved or rejected and cannot be edited.")
            return redirect('requisition_list') 

        # Process approved quantities and update inventory
        for item in requisition.items.all():
            approved_quantity = request.POST.get(f'approved_quantity_{item.id}')
            if approved_quantity is not None:
                try:
                    approved_quantity = int(approved_quantity)
                    if approved_quantity >= 0:
                        item.quantity_approved = approved_quantity 
                        item.save()

                        # Subtract approved quantity from the actual inventory
                        inventory_item = get_object_or_404(InventoryItem, id=item.inventory_item.id)
                        inventory_item.quantity -= approved_quantity
                        inventory_item.save()
                except ValueError:
                    continue  # Ignore invalid inputs

        requisition.status = 'Approved'
        requisition.save()
        
        RequisitionApprovalLog.objects.create(
            requisition=requisition,
            approved_by=request.user,
        )
        
        messages.success(request, "Requisition approved successfully!")
        return redirect('requisition_list') 


class RequisitionListView(LoginRequiredMixin, View):
    def get(self, request):
        requisitions = Requisition.objects.all().order_by('-date_created')
        
        # Filter by Requisition ID
        requisition_id = request.GET.get('requisition_id')
        if requisition_id:
            requisitions = requisitions.filter(requisition_id=requisition_id)
        
        # Filter by User
        user_id = request.GET.get('user')
        if user_id:
            requisitions = requisitions.filter(user_id=user_id)
        
        # Filter by Status
        status = request.GET.get('status')
        if status:
            requisitions = requisitions.filter(status=status)
        
        # Filter by Date Range
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if date_from and date_to:
            requisitions = requisitions.filter(date_created__range=[date_from, date_to])

        # Pass the list of users for the filter dropdown
        users = User.objects.all().exclude(is_staff=True)  # Exclude staff users
        
        return render(request, 'admin/requisition_list.html', {
            'requisitions': requisitions,
            'users': users,
        })

@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        # Get all requisitions
        requisitions = Requisition.objects.all().order_by('-date_created')
        return render(request, 'admin/admin_dashboard.html', {'requisitions': requisitions})



@method_decorator(staff_member_required, name='dispatch')
class AddInventoryItemView(LoginRequiredMixin, View):
    def get(self, request):
        form = AddInventoryItemForm()
        return render(request, 'admin/add_inventory_item.html', {'form': form})

    def post(self, request):
        form = AddInventoryItemForm(request.POST, request.FILES)
        if form.is_valid():
            # Process form data and save the item with updated quantity
            item = form.cleaned_data['existing_item']
            additional_quantity = form.cleaned_data['quantity']
            reference_no = form.cleaned_data['reference_no']
            reference_pdf = form.cleaned_data['reference_pdf'] 
            old_item = item.quantity
            item.quantity += additional_quantity
            item.save()
            
            # Create a log entry
            log_entry = UpdateLog.objects.create(
                item=item,
                quantity_added=additional_quantity,
                reference_no=reference_no,
                updated_by=request.user,
                reference_pdf=reference_pdf  # Save the uploaded PDF with the log entry
            )
            
            messages.success(request, f"{old_item} + {additional_quantity} = {item.quantity}, Quantity added to the inventory item successfully!")
        
        # Render the form again if it is invalid
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

class ReportView(View):
    def get(self, request):
        form = ReportForm()
        return render(request, 'admin/report.html', {'form': form})

    def post(self, request):
        form = ReportForm(request.POST)
        
        if form.is_valid():
            user = form.cleaned_data.get('user')
            item_name = form.cleaned_data.get('item')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')

            # Filter requisition items based on the provided form inputs
            requisition_items = RequisitionItem.objects.filter(requisition__status='Approved')
            
            # Filter by user if selected
            if user:
                requisition_items = requisition_items.filter(requisition__user=user)
            
            # Filter by item name if selected
            if item_name:
                requisition_items = requisition_items.filter(inventory_item__name=item_name)
            
            # Filter by date range if provided
            if date_from:
                requisition_items = requisition_items.filter(requisition__date_created__gte=date_from)
            if date_to:
                requisition_items = requisition_items.filter(requisition__date_created__lte=date_to)

            # Generate a report as PDF if 'generate_pdf' button is clicked
            if 'generate_pdf' in request.POST:
                return self.generate_pdf(requisition_items, user, item_name, date_from, date_to)

            # Render the filtered results
            return render(request, 'admin/report.html', {
                'form': form,
                'requisition_items': requisition_items
            })

        # If the form is invalid, re-render the page with the form (and error messages)
        return render(request, 'admin/report.html', {'form': form})

    def generate_pdf(self, requisition_items, user, item_name, date_from, date_to):

        html_string = render_to_string('admin/report_pdf.html', {
            'requisition_items': requisition_items,
            'user': user,
            'item': item_name,
            'date_from': date_from,
            'date_to': date_to
        })
        
         # Configure fonts
        font_config = FontConfiguration()
            
            # Generate PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf(font_config=font_config)

            # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report.pdf"'
            
        return response


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


class RequisitionPDFView(LoginRequiredMixin, View):
    def get(self, request, requisition_id):
        try:
            # Get requisition
            requisition = get_object_or_404(Requisition, id=requisition_id)
            if requisition.status == 'Approved':
                approval = get_object_or_404(RequisitionApprovalLog, requisition=requisition)
            else:
                approval = None
            # Fetch items
            requisition_items = requisition.items.all()
            labels = ["চাহিদাকারী বিভাগ কপি", "হিসাব বিভাগ কপি", "ভান্ডার উপবিভাগ কপি"]

            # Render HTML
            html_string = render_to_string('inventory/rqpdfu.html', {
                'requisition': requisition,
                'requisition_items': requisition_items,
                 "labels": labels,
                 "user": request.user,
                 "approval":approval
            })

            # Configure fonts
            font_config = FontConfiguration()
            
            # Generate PDF
            html = HTML(string=html_string)
            pdf = html.write_pdf(font_config=font_config)

            # Create response
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="requisition_{requisition.id}.pdf"'
            
            return response

        except Exception as e:
            logger.error(f'Error generating PDF: {str(e)}')
            return HttpResponse('Error generating PDF', status=500)        

"""
class RequisitionPDFView(LoginRequiredMixin, View):
    def get(self, request, requisition_id):
        requisition = Requisition.objects.get(id=requisition_id)
        
        if requisition.status != 'Approved':
            return HttpResponse("Requisition is not approved yet.", status=403)

        # Fetch requisition items
        requisition_items = requisition.items.all()

        # Render the HTML template with requisition details
        template = get_template('admin/rqpdf.html')
        context = {
            'requisition': requisition,
            'requisition_items': requisition_items
        }
        html = template.render(context)

        # Generate PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="requisition_{requisition.id}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse('Error occurred while generating PDF', status=500)

        return response
"""


"""

class RequisitionPDFView(LoginRequiredMixin, View):
    def get(self, request, requisition_id):
        requisition = Requisition.objects.get(id=requisition_id)

        if requisition.status != 'Approved':
            return HttpResponse("Requisition is not approved yet.", status=403)

        # Fetch requisition items
        requisition_items = requisition.items.all()

        # Generate and return the PDF
        return generate_requisition_pdf(requisition, requisition_items)
"""
