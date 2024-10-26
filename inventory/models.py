from django.db import models
from django.contrib.auth.models import User

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user making the requisition
    date_created = models.DateTimeField(auto_now_add=True)  # Automatically set to the current timestamp
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Requisition {self.id} by {self.user.username} - {self.status}"

class RequisitionItem(models.Model):
    requisition = models.ForeignKey(Requisition, related_name='items', on_delete=models.CASCADE)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity_requested = models.PositiveIntegerField()
    quantity_approved = models.PositiveIntegerField(null=True, blank=True)  # New field for approved quantity

    def __str__(self):
        return f"{self.quantity_requested} of {self.inventory_item.name} (Requisition {self.requisition.id})"
    
    
class UpdateLog(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity_added = models.PositiveIntegerField()
    reference_no = models.CharField(max_length=200)
    updated_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.item.name} - {self.quantity_added} added on {self.updated_at.strftime('%Y-%m-%d %H:%M')}"
