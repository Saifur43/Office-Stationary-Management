from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    reference_no = models.CharField(max_length=200)
    unit = models.CharField(max_length=100)
    quantity = models.IntegerField()
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)
    date_created = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    reference_pdf = models.FileField(upload_to='inventory_pdfs/', blank=True, null=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=200)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'categories'
        
    def __str__(self):
        return self.name


class Requisition(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    requisition_id = models.CharField(max_length=20, unique=True, editable=False, blank=True)  # New field

    def save(self, *args, **kwargs):
        if not self.requisition_id:  # Ensure custom_id is only set once
            current_year = timezone.now().year
            current_month = timezone.now().month
            # Get the latest requisition ID for this month and year, if it exists
            latest_requisition = Requisition.objects.filter(
                date_created__year=current_year,
                date_created__month=current_month
            ).order_by('-id').first()
            if latest_requisition:
                next_id = latest_requisition.id + 1
            else:
                next_id = 1  # Start counting if no requisitions exist this month
            self.requisition_id = f"{current_year}-{str(current_month).zfill(2)}-{str(next_id).zfill(3)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Requisition {self.requisition_id} by {self.user.username} - {self.status}"

class RequisitionItem(models.Model):
    requisition = models.ForeignKey(Requisition, related_name='items', on_delete=models.CASCADE)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity_requested = models.PositiveIntegerField()
    quantity_approved = models.PositiveIntegerField(null=True, blank=True)  # New field for approved quantity

    def __str__(self):
        return f"{self.quantity_requested} of {self.inventory_item.name} (Requisition {self.requisition.requisition_id})"
    
    
class UpdateLog(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity_added = models.PositiveIntegerField()
    reference_no = models.CharField(max_length=200)
    updated_at = models.DateField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reference_pdf = models.FileField(upload_to='inventory_pdfs/', blank=True, null=True)

    def __str__(self):
        return f"{self.item.name} - {self.quantity_added} added on {self.updated_at.strftime('%Y-%m-%d')}"
    
    
class RequisitionApprovalLog(models.Model):
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE)
    approved_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Requisition {self.requisition.requisition_id} approved by {self.approved_by.username} on {self.approved_at}"
