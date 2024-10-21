from django.contrib import admin
from django.urls import path
from .views import Index, SignUpView, Dashboard, RequisitionView, SubmitRequisition, ApproveRequisitionView, RequisitionListView
from .views import RequisitionDetailView, AdminDashboardView, AddInventoryItemView, StatisticsView, StatItemDetailView, ReportView
from .views import RequisitionPDFView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('requisition/<int:requisition_id>/', RequisitionDetailView.as_view(), name='requisition_detail'),
    path('requisition/', RequisitionView.as_view(), name='requisition'),
    path('submit-requisition/', SubmitRequisition.as_view(), name='submit_requisition'),
    path('approve-requisition/<int:requisition_id>/', ApproveRequisitionView.as_view(), name='approve_requisition'),
    path('requisition_list/', RequisitionListView.as_view(), name='requisition_list'),
    path('requisition/<int:requisition_id>/pdf/', RequisitionPDFView.as_view(), name='requisition_pdf'),
    path('add-inventory-item/', AddInventoryItemView.as_view(), name='add_inventory_item'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    path('statistics/item/<int:item_id>/', StatItemDetailView.as_view(), name='stat_item_detail'),
    path('report/', ReportView.as_view(), name='report'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html', next_page=reverse_lazy('index')), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='auth/logout.html'), name='logout'),
]
