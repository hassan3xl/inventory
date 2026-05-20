from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    ProductInventoryView,
    ProductImagesViewSet,
    CategoryViewSet,
    InventoryStatsView,
    BatchReceiveView,
    BatchDetailView,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"", ProductViewSet, basename="products")

urlpatterns = [
    path('stats/', InventoryStatsView.as_view(), name="inventory-stats"),
    path('', include(router.urls)),

    # (get & patch): product inventories
    path(
        "<uuid:pk>/inventory/", 
        ProductInventoryView.as_view(), 
        name="product-inventory"
    ),

    path(
        "<uuid:product_id>/images/",
        ProductImagesViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="product-images"
    ),

    path(
        "<uuid:product_id>/images/<int:pk>/",
        ProductImagesViewSet.as_view({
            "delete": "destroy",
        }),
        name="delete-product-images"
    ),

    path(
        "<uuid:product_id>/images/<int:pk>/set-primary/",
        ProductImagesViewSet.as_view({
            "post": "set_primary",
        }),
        name="set-primary"
    ),

    # Batch management (FEFO stock receiving)
    path(
        "<uuid:product_id>/batches/",
        BatchReceiveView.as_view(),
        name="product-batches"
    ),
    path(
        "<uuid:product_id>/batches/<uuid:pk>/",
        BatchDetailView.as_view(),
        name="product-batch-detail"
    ),
]
