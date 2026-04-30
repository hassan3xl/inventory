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




class StockBatchSerializer(ModelSerializer):
    class Meta:
        model = StockBatch
        fields = ['id', 'batch_number', 'quantity', 'production_date', 'expiry_date', 'created_at']


class ProductInventorySerializer(ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = ['id', 'sku']




class ProductCategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", 'name', 'image', 'description', 'default_best_before_days', 'expiry_strategy']


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
    images = ProductImageSerializer(many=True, read_only=False, required=False)
    category = ProductCategorySerializer(read_only=True)
    inventory = ProductInventorySerializer(read_only=False, required=False, allow_null=True)
    batches = StockBatchSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'stock', 'created_at',
              'unit_price', 'category', 'production_date', 'expiry_date', 'best_before_days', 
              'predicted_expiry_date', 'is_expired',
              'inventory', "is_active", 'images', 'batches']

    def get_average_rating(self, obj):
        return 0.0


class CategorySerializer(ModelSerializer):
    product_count = serializers.SerializerMethodField()
    products = ProductSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'description', 'default_best_before_days', 'expiry_strategy', 'product_count', 'products']

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
