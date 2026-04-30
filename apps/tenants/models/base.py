from django.db import models
from utils.tenant_context import get_current_tenant

class TenantQuerySet(models.QuerySet):
    def filter_by_tenant(self):
        tenant = get_current_tenant()
        if tenant:
            return self.filter(tenant=tenant)
        return self

class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db).filter_by_tenant()

class TenantBaseModel(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)

    objects = TenantManager()
    plain_objects = models.Manager() # For cases where we need all records (e.g. platform admin)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
        super().save(*args, **kwargs)
