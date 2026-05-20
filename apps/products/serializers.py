from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import (
    Product,
    ProductImage,
    Category,
    ProductInventory,
    StockBatch,
)
from django.db.models import Avg


# Existing serializers from controllers/store/products




from datetime import date as date_type, timedelta, datetime


class StockBatchSerializer(ModelSerializer):
    """
    FEFO-aware batch serializer.
    status     : fresh | near_expiry | critical | expired | no_expiry
    days_until_expiry : integer (negative = already expired)
    sold_count : initial_quantity - current quantity
    """
    status            = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    sold_count        = serializers.SerializerMethodField()

    class Meta:
        model = StockBatch
        fields = [
            'id', 'batch_number',
            'quantity', 'initial_quantity', 'sold_count',
            'production_date', 'expiry_date',
            'status', 'days_until_expiry',
            'created_at',
        ]

    def get_status(self, obj):
        if not obj.expiry_date:
            return 'no_expiry'
        
        expiry_date = obj.expiry_date
        if isinstance(expiry_date, str):
            try:
                expiry_date = datetime.strptime(expiry_date.split('T')[0], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return 'no_expiry'

        days = (expiry_date - date_type.today()).days
        if days < 0:
            return 'expired'
        if days <= 7:
            return 'critical'
        if days <= 30:
            return 'near_expiry'
        return 'fresh'

    def get_days_until_expiry(self, obj):
        if not obj.expiry_date:
            return None
        
        expiry_date = obj.expiry_date
        if isinstance(expiry_date, str):
            try:
                expiry_date = datetime.strptime(expiry_date.split('T')[0], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        return (expiry_date - date_type.today()).days

    def get_sold_count(self, obj):
        return max(0, (obj.initial_quantity or 0) - obj.quantity)


class ProductInventorySerializer(ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = ['id', 'sku']




class ProductCategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", 'name', 'image', 'description', 'business_type', 'default_best_before_days', 'expiry_strategy']


class ProductImageSerializer(ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

    def get_image(self, obj):
        """This method MUST be named get_<field_name>"""
        if obj.image:
            return obj.image.url
        return None


class ProductSerializer(ModelSerializer):
    images        = ProductImageSerializer(many=True, read_only=True)
    category      = ProductCategorySerializer(read_only=True)
    inventory     = ProductInventorySerializer(read_only=True, allow_null=True)
    # Batches ordered FEFO: soonest-expiring first (NULLs last)
    batches       = serializers.SerializerMethodField()
    stock_status  = serializers.SerializerMethodField()
    batch_summary = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'stock', 'unit_price',
            'category', 'is_active', 'created_at',
            'production_date', 'expiry_date', 'best_before_days',
            'predicted_expiry_date', 'is_expired',
            'stock_status', 'batch_summary',
            'inventory', 'images', 'batches',
        ]

    def get_batches(self, obj):
        """Return live batches ordered FEFO (expired batches listed last)."""
        from django.db.models import Case, When, Value, IntegerField
        batches = obj.batches.annotate(
            has_expiry=Case(
                When(expiry_date__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('has_expiry', 'expiry_date')
        return StockBatchSerializer(batches, many=True).data

    def get_stock_status(self, obj):
        """High-level product stock health: out_of_stock | low | expiry_risk | ok"""
        if obj.stock == 0:
            return 'out_of_stock'
        inventory = getattr(obj, 'inventory', None)
        threshold = inventory.low_stock_threshold if inventory else 5
        if obj.stock <= threshold:
            return 'low'
        if obj.expiry_date:
            days = (obj.expiry_date - date_type.today()).days
            if days < 0:
                return 'expired'
            if days <= 30:
                return 'expiry_risk'
        return 'ok'

    def get_batch_summary(self, obj):
        """Quick counts for the product card / list view."""
        today = date_type.today()
        all_batches = obj.batches.filter(quantity__gt=0)
        return {
            'total_batches': all_batches.count(),
            'fresh':         all_batches.filter(expiry_date__gt=today + timedelta(days=30)).count(),
            'near_expiry':   all_batches.filter(expiry_date__range=[today + timedelta(days=8), today + timedelta(days=30)]).count(),
            'critical':      all_batches.filter(expiry_date__range=[today, today + timedelta(days=7)]).count(),
            'expired':       all_batches.filter(expiry_date__lt=today).count(),
            'no_expiry':     all_batches.filter(expiry_date__isnull=True).count(),
        }


class CategorySerializer(ModelSerializer):
    product_count = serializers.SerializerMethodField()
    products = ProductSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'image', 'description',
            'business_type', 'business_type_display',
            'default_best_before_days', 'expiry_strategy',
            'product_count', 'products',
        ]

    def get_product_count(self, obj):
        return obj.products.count()

    def get_image(self, obj):
        """This method MUST be named get_<field_name>"""
        if obj.image:
            return obj.image.url
        return None


# Serializers from controllers/inventory/products
class ProductCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category'
    )
    production_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    best_before_days = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'stock', 'category_id',
            'unit_price',
            'production_date', 'expiry_date', 'best_before_days'
        ]

    def create(self, validated_data):
        product = Product.objects.create(**validated_data)
        return product


class ProductInventoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = '__all__'



class ProductImageWriteSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

    def get_image(self, obj):
        """This method MUST be named get_<field_name>"""
        if obj.image:
            return obj.image.url
        return None
