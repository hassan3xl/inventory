from rest_framework import viewsets, generics
from apps.products.models import Product, Category, StockBatch
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
        
        # Self-healing: Update stock for products whose earliest expiry date has passed but still show stock
        expired_with_stock = Product.objects.filter(expiry_date__lt=now, stock__gt=0)
        for p in expired_with_stock:
            p.update_stock_from_batches()
            
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
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated, HasTenantAccess]
    lookup_field = 'name'

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Category.plain_objects.all()
        if tenant:
            # Return global preset categories (tenant=None) + tenant's own categories
            # both scoped to the tenant's business type
            from django.db.models import Q
            qs = qs.filter(
                Q(business_type=tenant.business_type) | Q(business_type='general')
            ).filter(
                Q(tenant=tenant) | Q(tenant__isnull=True)
            )
        return qs.order_by('name')

    @action(detail=False, methods=['get'], url_path='presets')
    def presets(self, request):
        """
        Return the built-in category presets for the tenant's business type.
        GET /api/inventory/products/categories/presets/
        """
        tenant = getattr(request, 'tenant', None)
        business_type = tenant.business_type if tenant else 'general'
        preset_list = Category.PRESETS.get(business_type, Category.PRESETS['general'])
        return Response({
            'business_type': business_type,
            'categories': preset_list,
        })


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer

    def get_queryset(self):
        """
        Supported query params:
          ?expiring_in=<days>  — products whose earliest expiry is within N days
          ?expired=true        — products already past expiry
          ?low_stock=true      — products at or below their low-stock threshold (default 5)
          ?status=<value>      — shorthand: expired | critical | near_expiry | low | out_of_stock | ok
          ?search=<text>       — filter by product name (case-insensitive)
          ?category=<name>     — filter by category name
        """
        from django.utils import timezone as tz
        now = tz.now().date()

        # Self-healing: Update stock for products whose earliest expiry date has passed but still show stock
        expired_with_stock = Product.objects.filter(expiry_date__lt=now, stock__gt=0)
        for p in expired_with_stock:
            p.update_stock_from_batches()

        qs = Product.objects.all()
        p = self.request.query_params

        # Text search
        if search := p.get('search'):
            qs = qs.filter(name__icontains=search)

        # Category filter
        if category := p.get('category'):
            qs = qs.filter(category__name__iexact=category)

        # Expiry filters
        if p.get('expired', '').lower() == 'true':
            qs = qs.filter(expiry_date__lt=now)

        elif expiring_in := p.get('expiring_in'):
            try:
                days = int(expiring_in)
                qs = qs.filter(
                    expiry_date__isnull=False,
                    expiry_date__range=[now, now + timezone.timedelta(days=days)]
                )
            except ValueError:
                pass

        # Stock filters
        if p.get('low_stock', '').lower() == 'true':
            qs = qs.filter(stock__gt=0, stock__lte=5)

        if p.get('out_of_stock', '').lower() == 'true':
            qs = qs.filter(stock=0)

        # Shorthand status filter
        if status_param := p.get('status'):
            if status_param == 'expired':
                qs = qs.filter(expiry_date__lt=now)
            elif status_param == 'critical':
                qs = qs.filter(expiry_date__range=[now, now + timezone.timedelta(days=7)])
            elif status_param == 'near_expiry':
                qs = qs.filter(expiry_date__range=[now + timezone.timedelta(days=8), now + timezone.timedelta(days=30)])
            elif status_param == 'low':
                qs = qs.filter(stock__gt=0, stock__lte=5)
            elif status_param == 'out_of_stock':
                qs = qs.filter(stock=0)

        return qs.order_by('-created_at')


class BatchReceiveView(APIView):
    """
    Receive a new stock delivery for an existing product.
    Creates a StockBatch and updates the product's aggregate stock.

    POST /api/inventory/products/<product_id>/batches/
    {
        "batch_number": "BATCH-2025-003",   // optional, auto-generated if blank
        "quantity": 80,
        "production_date": "2025-05-01",    // optional
        "expiry_date": "2025-08-01"          // optional; computed from category default if omitted
    }
    """
    permission_classes = [IsAuthenticated, IsTenantManager]

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)

        quantity = request.data.get('quantity')
        if not quantity:
            return Response({'error': 'quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({'error': 'quantity must be a positive integer'}, status=status.HTTP_400_BAD_REQUEST)

        # Auto-generate batch number if not provided
        batch_number = request.data.get('batch_number') or f"{product.name[:6].upper().replace(' ', '')}-{StockBatch.objects.filter(product=product).count() + 1:04d}"

        batch = StockBatch(
            product=product,
            batch_number=batch_number,
            quantity=quantity,
            initial_quantity=quantity,
            production_date=request.data.get('production_date') or None,
            expiry_date=request.data.get('expiry_date') or None,
        )
        batch.save()  # triggers expiry auto-calc + product stock update

        from apps.products.serializers import StockBatchSerializer as _BS
        return Response({
            'message': f"Batch '{batch_number}' received successfully.",
            'batch': _BS(batch).data,
            'product_stock': product.stock,
        }, status=status.HTTP_201_CREATED)

    def get(self, request, product_id):
        """List all batches for this product, FEFO ordered."""
        product = get_object_or_404(Product, pk=product_id)
        from django.db.models import Case, When, Value, IntegerField
        batches = product.batches.annotate(
            has_expiry=Case(
                When(expiry_date__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('has_expiry', 'expiry_date')
        from apps.products.serializers import StockBatchSerializer as _BS
        return Response(_BS(batches, many=True).data)


class BatchDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantManager]

    def patch(self, request, product_id, pk):
        batch = get_object_or_404(StockBatch, product_id=product_id, pk=pk)

        # Update batch fields
        if 'batch_number' in request.data:
            batch.batch_number = request.data['batch_number']
        if 'quantity' in request.data:
            batch.quantity = int(request.data['quantity'])
        if 'initial_quantity' in request.data:
            batch.initial_quantity = int(request.data['initial_quantity'])
        if 'production_date' in request.data:
            batch.production_date = request.data['production_date'] or None
        if 'expiry_date' in request.data:
            batch.expiry_date = request.data['expiry_date'] or None

        batch.save()  # triggers recalculation and save

        from apps.products.serializers import StockBatchSerializer as _BS
        return Response(_BS(batch).data)

    def delete(self, request, product_id, pk):
        batch = get_object_or_404(StockBatch, product_id=product_id, pk=pk)
        batch.delete()  # triggers overridden delete which recalculates totals
        return Response({"status": "success", "message": "Batch deleted successfully"}, status=status.HTTP_200_OK)


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



    