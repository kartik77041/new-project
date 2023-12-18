from django.contrib import admin
from django.urls import path, include
from api.views import acknowledge_purchase_order, VendorPerformanceViewSet, VendorProfileViewSet, PurchaseOrderTrackViewSet
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'vendors', VendorProfileViewSet)
router.register(r'purchase_orders', PurchaseOrderTrackViewSet)

urlpatterns = [
     path('purchase_orders/<int:po_id>/acknowledge/', views.acknowledge_purchase_order, name='acknowledge_purchase_order'),
    path('vendors/<int:vendor_id>/performance/', VendorPerformanceViewSet.as_view()),
    path('',include(router.urls)),
]
