from rest_framework import serializers
from api.models import Vendor, PurchaseOrder

class VendorPerformanceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Vendor
        fields = ["on_time_delivery_rate", "quality_rating_avg", "average_response_time", "fulfillment_rate"]
class VendorProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Vendor
        fields = ["name", "contact_details", "address","vendor_code"]

class PurchaseOrderTrackSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ["po_number","vendor", "order_date", "items","quantity", "status"]

class PurchaseOrderTrackSerializer2(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ["acknowledgment_date"]

