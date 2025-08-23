# Forum Project Stage CC WebAPI Documentation

This document describes the available endpoints, request formats, response structures, and validation rules for the **Forum Project Stage CC WebAPI**.  
It is organized by module to allow each developer to maintain and extend their respective sections.

---

## Authentication

All endpoints require JWT authentication.  
Include the token in the `Authorization` header using the following format:

Authorization: Bearer <your_access_token>

---

### 🔐 JWT Logout

The `POST /api/users/auth/jwt/logout/` endpoint logs out a user by **blacklisting the refresh token**.

### ✅ Requirements

- The **refresh token must be included** in the request body.
- The **client must delete both access and refresh tokens** from local storage (or other storage) after a successful logout.

### 📤 Example Request

```http
POST /api/users/auth/jwt/logout/
Content-Type: application/json

{
  "refresh": "<your_refresh_token>"
}
```

## Startup API

### Endpoints

- `GET /api/profiles/startups/` — Retrieve a list of all startup profiles
- `POST /api/profiles/startups/` — Create a new startup profile
- `GET /api/profiles/startups/{id}/` — Retrieve details of a specific startup profile
- `PATCH /api/profiles/startups/{id}/` — Update an existing startup profile
- `DELETE /api/profiles/startups/{id}/` — Delete a startup profile

## Investor API

### Endpoints

- `GET /api/profiles/investors/` — Retrieve a list of all investors
- `POST /api/profiles/investors/` — Create a new investor  
  ...

### Request Example: Create Startup Profile

```json
{
  "company_name": "GreenTech",
  "description": "Eco-friendly solutions",
  "website": "https://greentech.ua",
  "startup_logo": null
}
```

### Response Example: Created Startup Profile (201 Created)

```json
{
  "id": 1,
  "company_name": "GreenTech",
  "description": "Eco-friendly solutions",
  "website": "https://greentech.ua",
  "startup_logo": null,
  "projects": [],
  "created_at": "2025-08-05T00:00:00Z",
  "updated_at": "2025-08-05T00:00:00Z"
}
```

---

## Project API

### Endpoints

- `GET /api/projects/` — Retrieve a list of all projects
- `POST /api/projects/` — Create a new project
- `GET /api/projects/{id}/` — Retrieve details of a specific project
- `PATCH /api/projects/{id}/` — Update an existing project
- `DELETE /api/projects/{id}/` — Delete a project

---

### Request Example: Create Project

```json
{
  "startup": 1,
  "title": "AI Platform",
  "description": "Smart analytics for business",
  "status": "draft",
  "duration": 30,
  "funding_goal": "100000.00",
  "current_funding": "5000.00",
  "category": 2,
  "email": "project@example.com",
  "has_patents": true,
  "is_participant": false,
  "is_active": true
}
```

### Response Example: Created Project (201 Created)

```json
{
  "id": 1,
  "startup": 1,
  "title": "AI Platform",
  "description": "Smart analytics for business",
  "status": "draft",
  "duration": 30,
  "funding_goal": "100000.00",
  "current_funding": "5000.00",
  "category": 2,
  "email": "project@example.com",
  "has_patents": true,
  "is_participant": false,
  "is_active": true,
  "created_at": "2025-08-05T00:00:00Z",
  "updated_at": "2025-08-05T00:00:00Z"
}
```

---

## Validation Rules

### Startup Profile

- company_name: required, unique
- description: required
- website: optional
- startup_logo: optional

### Project

- startup: required (must reference existing profile)
- title: required
- funding_goal: required if is_participant is true
- current_funding: must not exceed funding_goal
- business_plan: required if status is completed
- email: required, must be valid

---

## Token Refresh

Use `/api/token/refresh/` to obtain a new access token.

### Response Example

```json
{
  "refresh": "<your_refresh_token>",
  "access": "<your_new_access_token>"
}
```

# OAuth Authentication API Documentation

## Part 1
## Overview
This document describes the OAuth authentication endpoints for Google and GitHub integration.

---

## POST /users/oauth/login/

### Description
Authenticate users using Google or GitHub OAuth providers. The endpoint exchanges OAuth provider tokens for application JWT tokens and returns user information.

## Request

- **Headers:**  
  `Content-Type: application/json`

- **Body:**
  ```json
  {
    "provider": "google" | "github",
    "token": "<OAuth token>"
  }
  ```
  - **Response**
  ```json
  {
    "refresh": "jwt_refresh_token",
    "access": "jwt_access_token",
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "username": "username123",
      "first_name": "John",
      "last_name": "Doe",
      "user_phone": "+1234567890",
      "title": "Software Developer",
      "role": "user"
    }
  }
  ```

**Status codes:**

| Status Code | Description |
|-------------|-------------|
| `400 Bad Request` | Invalid request parameters or malformed data |
| `401 Unauthorized` | Authentication failed or invalid credentials |
| `403 Forbidden` | Authenticated but insufficient permissions |
| `404 Not Found` | Requested resource doesn't exist |
| `408 Request Timeout` | Provider API timeout |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error |
| `502 Bad Gateway` | Provider API communication failed |

## Part 2
## Callback URLs
The OAuth callback URLs are configured to handle redirects after successful authentication with the OAuth provider. These URLs are used by the frontend to receive authorization codes or tokens.

### Configured Callback URLs
- **Production**: ----
- **Development**: `http://127.0.0.1:8000/oauth/callback/`

## Usage Instructions
1. **Initiate OAuth Flow**:
   - Redirect users to the OAuth provider's authorization endpoint (e.g., `https://provider.com/oauth/authorize`).
   - Include the appropriate `redirect_uri` parameter matching one of the configured callback URLs

2. **Handle Callback**:
   - After authentication, the OAuth provider will redirect the user to the specified callback URL with an authorization code or token in the query parameters (e.g., `https://yourapp.com/auth/callback?code=abc123`).
   - The frontend should extract the `code` from the URL query parameters using `URLSearchParams`.

3. **Extracting Query Parameters**:
   - Example of JavaScript to extract parameters from the callback URL:
     ```javascript
     const urlParams = new URLSearchParams(window.location.search);
     const code = urlParams.get('code');
     const state = urlParams.get('state');
     const error = urlParams.get('error');
     ```

4. **ExchangeCode for Token**:
  -Send the authorization code to your backend API `/users/oauth/login/` to exchange it for an access token.

## Notifications API (Communications)

All endpoints require authentication and are available under the base path: `/api/v1/communications/`.

### Endpoints

- `GET /notifications/` — List current user's notifications.
- `GET /notifications/unread_count/` — Get unread notifications count.
- `POST /notifications/{notification_id}/mark_as_read/` — Mark notification as read.
- `POST /notifications/{notification_id}/mark_as_unread/` — Mark notification as unread.
- `POST /notifications/mark_all_as_read/` — Mark all notifications as read.
- `POST /notifications/mark_all_as_unread/` — Mark all notifications as unread.
- `GET /notifications/{notification_id}/resolve/` — Get only redirect payload for a notification.
- `DELETE /notifications/{notification_id}/` — Delete a notification.

Creation of notifications via public API is disabled.

### Query Parameters (GET /notifications/)

- `is_read` — true | false (filter by read state: true = read, false = unread)
- `type` — notification type code (slug)
- `priority` — low | medium | high
- `created_after` — ISO datetime (e.g., 2025-08-05T00:00:00Z)
- `created_before` — ISO datetime

### Response Example (GET /notifications/)

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "notification_id": "b6b9e6f4-8f5a-4e58-9e7f-2d3b1f7ac111",
      "notification_type": {
        "id": 3,
        "code": "message_new",
        "name": "New Message",
        "description": "A new message was received",
        "is_active": true
      },
      "title": "You have a new message",
      "message": "Investor John Doe sent you a message",
      "is_read": false,
      "priority": "medium",
      "priority_display": "Medium",
      "actor": {
        "type": "investor",
        "user_id": 42,
        "investor_id": 7,
        "display_name": "Acme Ventures"
      },
      "redirect": {
        "kind": "message",
        "id": 99,
        "url": "/messages/99"
      },
      "created_at": "2025-08-05T12:34:56Z",
      "updated_at": "2025-08-05T12:34:56Z",
      "expires_at": null
    }
  ]
}
```

### Actions Responses

- `POST /notifications/{id}/mark_as_read/` → `{ "status": "notification marked as read" }`
- `POST /notifications/{id}/mark_as_unread/` → `{ "status": "notification marked as unread" }`
- `POST /notifications/mark_all_as_read/` → `{ "status": "marked <n> notifications as read" }`
- `POST /notifications/mark_all_as_unread/` → `{ "status": "marked <n> notifications as unread" }`
- `GET /notifications/{id}/resolve/` → `{ "redirect": { ... } }`
