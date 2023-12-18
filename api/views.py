from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from api.models import Vendor, PurchaseOrder
from api.serializers import PurchaseOrderTrackSerializer2, VendorProfileSerializer, PurchaseOrderTrackSerializer
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from rest_framework.decorators import api_view
from rest_framework import status
from django.db import models

#Vendor Performance Evaluation
class VendorPerformanceViewSet(APIView):
    def get(self, request, vendor_id):
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
            performance_metrics = {
                'on_time_delivery_rate': vendor.on_time_delivery_rate,
                'quality_rating_avg': vendor.quality_rating_avg,
                'average_response_time': vendor.average_response_time,
                'fulfillment_rate': vendor.fulfillment_rate,
            }
            return Response(performance_metrics)
        except Vendor.DoesNotExist:
            return Response({'message': 'Vendor not found'}, status=404)
        
#Vendor Profile Management
class VendorProfileViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorProfileSerializer

#Purchase Order Tracking
class PurchaseOrderTrackViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderTrackSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        vendor_id = self.request.query_params.get('vendor', None)
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        return queryset
    

#Backend Logic for Performance Metrics
@receiver(post_save, sender=PurchaseOrder)  
def update_vendor_metrics_on_save(sender, instance, created, **kwargs):
    if created or instance.status == 'completed':
        vendor = instance.vendor
        completed_orders = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
        delivered_on_time = completed_orders.filter(delivery_date__lte=models.F('delivery_date')).count()
        vendor.on_time_delivery_rate = (delivered_on_time / completed_orders.count()) * 100 if completed_orders.count() else 0

        completed_with_rating = completed_orders.exclude(quality_rating__isnull=True)
        quality_sum = completed_with_rating.aggregate(models.Sum('quality_rating'))['quality_rating__sum'] or 0
        vendor.quality_rating_avg = quality_sum / completed_with_rating.count() if completed_with_rating.count() else 0

        vendor.save()

@receiver(pre_save, sender=PurchaseOrder)
def update_response_time(sender, instance, **kwargs):
    if instance.status == 'acknowledged':
        vendor = instance.vendor
        total_response_time = vendor.average_response_time * PurchaseOrder.objects.filter(vendor=vendor, status='acknowledged').count()
        total_response_time += (instance.acknowledgment_date - instance.issue_date).total_seconds()
        vendor.average_response_time = total_response_time / PurchaseOrder.objects.filter(vendor=vendor, status='acknowledged').count()
        vendor.save()


@receiver(post_save, sender=PurchaseOrder)
def update_fulfilment_rate(sender, instance, created, **kwargs):
    if created or instance.status:
        vendor = instance.vendor
        fulfilled_orders = PurchaseOrder.objects.filter(vendor=vendor, status='completed', issue_date__isnull=False)
        vendor.fulfillment_rate = (fulfilled_orders.count() / PurchaseOrder.objects.filter(vendor=vendor).count()) * 100 if PurchaseOrder.objects.filter(vendor=vendor).count() else 10
        vendor.save()


#POST /api/purchase_orders/{po_id}/acknowledge/
@api_view(['POST'])
def acknowledge_purchase_order(request, po_id):
    try:
        purchase_order = PurchaseOrder.objects.get(pk=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response({"message": "Purchase Order does not exist"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        serializer = PurchaseOrderTrackSerializer2(purchase_order, data=request.data, partial=True, context={'request': request} )
        if serializer.is_valid():
            a = serializer.validated_data
            serializer.save(acknowledgment_date=serializer.validated_data.get('acknowledgment_date'))
            print(a)
            purchase_order.refresh_from_db()
            purchase_order.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

