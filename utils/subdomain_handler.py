"""
Subdomain Handler Module

This module provides utilities for subdomain-based routing and tenant resolution.
It's separated from the main middleware to allow easy configuration and updates
without disrupting the core middleware logic.

Usage:
    from utils.subdomain_handler import SubdomainHandler
    
    handler = SubdomainHandler()
    tenant = handler.get_tenant_from_request(request)
"""

from django.conf import settings
from apps.tenants.models import Tenant


class SubdomainHandler:
    """
    Handles subdomain-based tenant resolution.
    
    Configuration can be added to settings:
        SUBDOMAIN_CONFIG = {
            'enabled': True,
            'main_domain': 'example.com',
            'main_subdomains': ['www', 'api', 'admin'],  # Excluded from tenant resolution
        }
    """
    
    def __init__(self):
        self.config = getattr(settings, 'SUBDOMAIN_CONFIG', {
            'enabled': False,
            'main_domain': None,
            'main_subdomains': ['www', 'api', 'admin'],
        })
    
    def get_subdomain_from_host(self, host):
        """
        Extract subdomain from hostname.
        
        Examples:
            'shop1.example.com' -> 'shop1'
            'example.com' -> None
            'shop1.localhost' -> 'shop1'
            'localhost:8000' -> None
        """
        if not host:
            return None
        
        # Remove port if present
        host = host.split(':')[0]
        parts = host.split('.')
        
        # Handle localhost-style development
        if len(parts) == 2 and parts[1] == 'localhost':
            return parts[0]
        
        # Handle production domains (e.g., subdomain.example.com)
        if len(parts) > 2:
            subdomain = parts[0]
            
            # Skip main subdomains
            if subdomain not in self.config['main_subdomains']:
                return subdomain
        
        return None
    
    def get_tenant_from_subdomain(self, subdomain):
        """
        Get tenant by subdomain.
        
        Args:
            subdomain: The subdomain string
            
        Returns:
            Tenant object or None if not found
        """
        if not subdomain:
            return None
        
        try:
            return Tenant.objects.get(subdomain=subdomain, is_active=True)
        except Tenant.DoesNotExist:
            return None
    
    def get_tenant_from_request(self, request):
        """
        Get tenant from request using subdomain.
        
        Args:
            request: Django request object
            
        Returns:
            Tenant object or None
        """
        if not self.config.get('enabled', False):
            return None
        
        host = request.get_host()
        subdomain = self.get_subdomain_from_host(host)
        return self.get_tenant_from_subdomain(subdomain)
    
    def enable_subdomain_routing(self):
        """Enable subdomain-based routing."""
        self.config['enabled'] = True
    
    def disable_subdomain_routing(self):
        """Disable subdomain-based routing."""
        self.config['enabled'] = False
    
    def set_main_domain(self, domain):
        """Set the main domain for subdomain extraction."""
        self.config['main_domain'] = domain
    
    def set_main_subdomains(self, subdomains):
        """Set list of main subdomains to exclude from tenant resolution."""
        self.config['main_subdomains'] = subdomains


# Global instance for easy access
subdomain_handler = SubdomainHandler()


def enable_subdomain_routing(main_domain=None, main_subdomains=None):
    """
    Enable subdomain-based routing with optional configuration.
    
    Usage in settings:
        from utils.subdomain_handler import enable_subdomain_routing
        enable_subdomain_routing(
            main_domain='example.com',
            main_subdomains=['www', 'api', 'admin']
        )
    """
    subdomain_handler.enable_subdomain_routing()
    if main_domain:
        subdomain_handler.set_main_domain(main_domain)
    if main_subdomains:
        subdomain_handler.set_main_subdomains(main_subdomains)
