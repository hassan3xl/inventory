from rest_framework import viewsets, generics
from apps.products.models import Product, Category
from apps.products.api import (
    ProductCategorySerializer,
    ProductSerializer,
    ProductCreateSerializer,
    ProductImageWriteSerializer,
    ProductInventoryWriteSerializer,
)
from apps.products.models import ProductImage

# from ..config.permissions import IsMerchantUser, IsActiveVerifiedMerchant
from apps.tenants.permissions.tenant_roles import HasTenantAccess, IsTenantAdmin, IsTenantManager, IsTenantStaff
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action

from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from django.db.models import Sum, F, Q
from django.utils import timezone

class InventoryStatsView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        now = timezone.now().date()
        
        # Total value calculation: Sum(stock * unit_price)
        total_value = Product.objects.all().aggregate(
            total=Sum(F('stock') * F('unit_price'))
        )['total'] or 0

        total_items = Product.objects.all().aggregate(
            total=Sum('stock')
        )['total'] or 0

        low_stock_count = Product.objects.filter(stock__lte=5).count() # Static threshold for now
        out_of_stock_count = Product.objects.filter(stock=0).count()
        
        expired_count = Product.objects.filter(expiry_date__lt=now).count()
        near_expiry_count = Product.objects.filter(
            expiry_date__range=[now, now + timezone.timedelta(days=30)]
        ).count()

        return Response({
            "total_value": total_value,
            "total_items": total_items,
            "product_count": Product.objects.count(),
            "low_stock": low_stock_count,
            "out_of_stock": out_of_stock_count,
            "expired": expired_count,
            "near_expiry": near_expiry_count,
        })

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated, HasTenantAccess]
    lookup_field = 'name'
    
    def get_serializer_class(self):
        # We might want a different serializer for detail vs list if needed
        return ProductCategorySerializer

    
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasTenantAccess]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer

    def get_queryset(self):
        return Product.objects.all()


class ProductInventoryView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        serializer = ProductInventoryWriteSerializer(
            data=request.data,
        )
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(
                {"message": "Inventory updated successfully"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ProductImagesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, HasTenantAccess]
    from rest_framework.parsers import MultiPartParser, FormParser
    parser_classes = (MultiPartParser, FormParser)

    # GET /products/<product_id>/images/
    def list(self, request, product_id=None):
        product = get_object_or_404(Product, id=product_id)
        images = product.images.all()
        serializer = ProductImageWriteSerializer(images, many=True)
        return Response(serializer.data)

    # POST /products/<product_id>/images/
    def create(self, request, product_id=None):
        product = get_object_or_404(Product, id=product_id)

        file = request.FILES.get("image")
        if not file:
            return Response({"error": "No image provided"}, status=400)

        image = ProductImage.objects.create(product=product, image=file)

        return Response({"status": "success", "id": image.id}, status=201)

    # DELETE /products/<product_id>/images/<image_id>/
    def destroy(self, request, product_id=None, pk=None):
        product = get_object_or_404(Product, id=product_id)
        image = get_object_or_404(ProductImage, id=pk, product=product)

        image.delete()
        return Response({"status": "image deleted"}, status=200)

    # POST /products/<product_id>/images/<image_id>/set-primary/
    @action(detail=True, methods=["post"])
    def set_primary(self, request, product_id=None, pk=None):
        product = get_object_or_404(Product, id=product_id)
        image = get_object_or_404(ProductImage, id=pk, product=product)

        # remove primary from all images first
        product.images.update(is_primary=False)

        image.is_primary = True
        image.save()

        return Response({"status": "primary image set", "image_id": image.id})



    