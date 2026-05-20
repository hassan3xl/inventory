# Tenant API Documentation

## Overview

The tenant API provides endpoints for multi-tenant management. Tenants can now be created and managed entirely through the API.

## Endpoints

### 1. Register Tenant (Public - No Auth Required)

**POST** `/api/tenants/register/`

Create a new tenant and associate an admin user.

**Request:**

```json
{
  "business_name": "My Store",
  "business_type": "retail",
  "admin_email": "admin@mystore.com"
}
```

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Store",
  "business_type": "retail",
  "admin_email": "admin@mystore.com",
  "message": "Tenant registered successfully!"
}
```

**Response (First Time User - 201 Created):**

```json
{
  "message": "Tenant registered successfully. User created with temporary password.",
  "temporary_password": "Ab3Cd5Ef7Gh9",
  "admin_email": "admin@mystore.com",
  "note": "User should change password after first login"
}
```

---

### 2. Tenant Dashboard (Authenticated)

**GET** `/api/tenants/dashboard/`

Get dashboard stats for the user's current tenant.

**Headers:**

```
Authorization: Bearer <token>
```

**Response (200 OK):**

```json
{
  "business_name": "My Store",
  "business_type": "Retail",
  "total_products": 42,
  "total_staff": 5
}
```

---

### 3. List/Create Tenants (Authenticated)

**GET** `/api/tenants/list/` - List all tenants
**POST** `/api/tenants/list/` - Create a new tenant

**POST Request:**

```json
{
  "name": "Another Store",
  "business_type": "grocery"
}
```

**Response (201 Created):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Another Store",
  "business_type": "grocery",
  "is_active": true,
  "created_at": "2026-05-18T18:30:00Z"
}
```

---

### 4. Tenant Users (Authenticated)

**GET** `/api/tenants/users/`

List all users in the current tenant context.

**Headers:**

```
Authorization: Bearer <token>
```

---

## Migration from Subdomain

### Before (Old Flow - Subdomain Required)

1. Register tenant with subdomain
2. Access via `subdomain.localhost:8000`
3. Login with tenant context

### After (New Flow - No Subdomain)

1. Register tenant via `/api/tenants/register/`
2. Access API directly from `localhost:8000/api/`
3. Login without subdomain, get `tenant_id` in response
4. Use `tenant_id` for frontend routing

## Login Response Includes Tenant Info

After successful login, the response now includes:

```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": { ... },
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_name": "My Store",
    "available_tenants": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "My Store",
            "role": "Administrator"
        }
    ]
}
```

## Future: Enable Subdomain Routing

When you're ready to deploy with subdomain routing, add to your settings:

```python
# settings/prod.py
from utils.subdomain_handler import enable_subdomain_routing

enable_subdomain_routing(
    main_domain='example.com',
    main_subdomains=['www', 'api', 'admin']
)
```

No other code changes needed!

## Quick Start for Frontend

### Registration

```javascript
// Register a new tenant
const response = await fetch("/api/tenants/register/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    business_name: "My Shop",
    business_type: "retail",
    admin_email: "admin@myshop.com",
  }),
});
```

### Login

```javascript
// Login returns tenant_id in response
const response = await fetch("/api/auth/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "admin@myshop.com",
    password: "password123",
  }),
});

const data = await response.json();
const tenantId = data.tenant_id; // Use this for tenant context
```

### Using Tenant Context in Subsequent Requests

```javascript
// Option 1: Pass tenant_id in X-Tenant header
fetch("/api/products/", {
  headers: {
    Authorization: `Bearer ${token}`,
    "X-Tenant": tenantId,
  },
});

// Option 2: Store in session/context and pass with each request
```
