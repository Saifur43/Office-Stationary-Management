from django.contrib import admin
from .models import InventoryItem, Category, Requisition, RequisitionItem

admin.site.register(InventoryItem)
admin.site.register(Category)
admin.site.register(Requisition)
admin.site.register(RequisitionItem)