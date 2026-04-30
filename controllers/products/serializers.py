from rest_framework import serializers
from products.models import Product, ProductInventory, Category, ProductSpecification, Feature, ProductImage

class ProductCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category'
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'stock', 'category_id',
            'original_price', 'sale_price', 'is_on_sale'
        ]

    def create(self, validated_data):
        merchant = self.context['request'].user.merchant
        product = Product.objects.create(**validated_data, merchant=merchant)
        return product


class ProductInventoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = '_all__'


class ProductSpecificationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['title', 'body', 'id']


class ProductFeatureWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feature
        fields = ['name']


class ProductImageWriteSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = ProductImage
        fields = ['id', 'image',  'is_primary']
    
    def get_image(self, obj):
        """This method MUST be named get_<field_name>"""
        if obj.image:
            return obj.image.url
        return None
