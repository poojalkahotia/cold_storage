from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('client-details/add/', views.client_details_create, name='client_details_create'),
    path('client-details/edit/<path:pk>/', views.client_details_update, name='client_details_update'),
    path('client-details/delete/<path:pk>/', views.client_details_delete, name='client_details_delete'),
    
    # Item URLs
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.item_create, name='item_create'),
    path('items/edit/<str:pk>/', views.item_update, name='item_update'),
    path('items/delete/<str:pk>/', views.item_delete, name='item_delete'),

    # Incoming URLs
    path('incoming/', views.incoming_list, name='incoming_list'),
    path('incoming/add/', views.incoming_create, name='incoming_create'),
    path('incoming/edit/<str:pk>/', views.incoming_update, name='incoming_update'),
    path('incoming/delete/<str:pk>/', views.incoming_delete, name='incoming_delete'),

    # Final Year URLs
    path('finalyear/', views.finalyear_list, name='finalyear_list'),
    path('finalyear/add/', views.finalyear_create, name='finalyear_create'),
    path('finalyear/edit/<int:pk>/', views.finalyear_update, name='finalyear_update'),
    path('finalyear/delete/<int:pk>/', views.finalyear_delete, name='finalyear_delete'),

    # GatePass URLs
    path('gatepass/', views.gp_list, name='gp_list'),
    path('gatepass/add/', views.gp_create, name='gp_create'),
    path('gatepass/edit/<str:pk>/', views.gp_update, name='gp_update'),
    path('gatepass/delete/<str:pk>/', views.gp_delete, name='gp_delete'),

    # Payment URLs
    path('payment/', views.payment_list, name='payment_list'),
    path('payment/add/', views.payment_create, name='payment_create'),
    path('payment/edit/<str:pk>/', views.payment_update, name='payment_update'),
    path('payment/delete/<str:pk>/', views.payment_delete, name='payment_delete'),

    # Hamali Entry URLs
    path('hamali-entry/', views.hamali_entry_list, name='hamali_entry_list'),
    path('hamali-entry/add/', views.hamali_entry_create, name='hamali_entry_create'),
    path('hamali-entry/edit/<int:pk>/', views.hamali_entry_update, name='hamali_entry_update'),
    path('hamali-entry/delete/<int:pk>/', views.hamali_entry_delete, name='hamali_entry_delete'),
]
