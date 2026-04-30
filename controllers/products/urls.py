from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet
from .views import (
    ProductInventoryView,
    ProductImagesViewSet,
    CategoryViewSet,
    InventoryStatsView,
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

]
