# Contributing to API Documentation

This guide explains how to contribute new API documentation to the `docs/API.md` file in a consistent and maintainable way.

## Where to Add

All API documentation is maintained in `docs/API.md`. Each endpoint should be documented as a separate section using the following structure.

## Format Guidelines

Please follow this format for each new endpoint:

### Endpoint

<HTTP_METHOD> <URL_PATH>

**Example:**  
`POST /api/users/auth/jwt/logout/`

### Description

Briefly describe what the endpoint does and who should use it.

### Request Headers

List required headers, if any.

```
Content-Type: application/json  
Authorization: Bearer <access_token>
```

### Request Body

Provide a JSON example of the request payload.

```json
{
  "refresh": "<your_refresh_token>"
}
```

### Response

Describe the expected response format and status codes.

```json
{
  "detail": "Successfully logged out."
}
```

**Status codes:**

- `200 OK` – Successful operation  
- `401 Unauthorized` – Invalid or missing token  
- `400 Bad Request` – Malformed input  

### Notes

Include any additional notes, such as:

- Required permissions  
- Rate limits  
- Side effects (e.g., token blacklisting)  

## Writing Tips

- Be concise but clear.  
- Use triple backticks for code blocks.  
- Use consistent indentation and formatting.  
- Prefer present tense: "Returns a list of..." instead of "Will return..."  

## Submitting Changes

- Make your edits in a new branch.  
- Ensure formatting is consistent with existing entries.  
- Open a Pull Request referencing the related issue (if any).  
- Request review from at least one core contributor.

---

## Project Follow Notifications Implementation Guide

### Overview

The Project Follow Notifications feature allows investors to follow startup projects and receive notifications. This section documents the implementation details for developers.

### Architecture Components

1. **Model**: `ProjectFollow` in `investors/models.py`
2. **Signals**: Django signals in `communications/signals.py` 
3. **API Views**: DRF views in `investors/views.py`
4. **Serializers**: Located in `investors/serializers/project_follow.py`
5. **Admin**: Admin interface in `investors/admin.py`
6. **Tests**: Comprehensive tests in `tests/investors/test_project_follow.py`

### Database Migration

Run the following command to create the ProjectFollow table:

```bash
python manage.py migrate investors
```

### Signal Integration

The notification system uses Django's `post_save` signal to automatically trigger notifications when investors follow projects. The signal handler `notify_project_followed` is registered in `communications/signals.py`.

### Key Features

- **Unique Constraints**: Prevents duplicate follows per investor-project pair
- **Soft Deletion**: Uses `is_active` field instead of hard deletion
- **Self-Follow Prevention**: Investors cannot follow their own startup's projects
- **Notification Deduplication**: Prevents duplicate notifications within the same second
- **Transaction Safety**: Follow operations don't break if notification creation fails

### Business Rules

1. Only authenticated investors can follow projects
2. Investors cannot follow their own startup's projects
3. Each investor can follow a project only once (active follow)
4. Unfollowing sets `is_active=False` (soft delete)
5. Notifications are sent to startup owners when their projects are followed

### Admin Interface

Access the admin interface at `/admin/investors/projectfollow/` to:
- View all project follows with filtering and search
- Bulk activate/deactivate follows
- See notification counts and related information

### Testing

Run the comprehensive test suite:

```bash
python manage.py test tests.investors.test_project_follow
```

### Troubleshooting

**Common Issues:**

1. **Migration Errors**: Ensure all dependencies are migrated first
2. **Signal Not Firing**: Verify signal registration in `communications/apps.py`
3. **Permission Denied**: Verify user has investor profile and active company account
4. **Duplicate Follow Errors**: Database constraint should prevent this automatically

**Debug Commands:**

```bash
# Check signal registration
python manage.py shell -c "from communications import signals; print(signals._handlers)"

# Test notification creation
python manage.py shell -c "from investors.models import ProjectFollow; print(ProjectFollow.objects.count())"
```