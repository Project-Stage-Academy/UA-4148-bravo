# Forum Project Stage CC WebAPI Documentation

This document describes the available endpoints, request formats, response structures, and validation rules for the **Forum Project Stage CC WebAPI**.  
It is organized by module to allow each developer to maintain and extend their respective sections.

---

## Authentication

All endpoints require JWT authentication.  
Include the token in the `Authorization` header using the following format:

Authorization: Bearer <your_access_token>

Use `/api/token/refresh/` to obtain a new access token.

### Response Example

```json
{
  "refresh": "<your_refresh_token>",
  "access": "<your_new_access_token>"
}
```

---

###  JWT Logout

The `POST /api/users/auth/jwt/logout/` endpoint logs out a user by **blacklisting the refresh token**.

###  Requirements

- The **refresh token must be included** in the request body.
- The **client must delete both access and refresh tokens** from local storage (or other storage) after a successful logout.

###  Example Request

```http
POST /api/users/auth/jwt/logout/
Content-Type: application/json

{
  "refresh": "<your_refresh_token>"
}
```

---

# OAuth Authentication API Documentation

## Overview
This document describes the OAuth authentication endpoints for Google and GitHub integration.

### Endpoint: POST /users/oauth/login/

**Description:**  
Authenticate users using Google or GitHub OAuth providers. The endpoint exchanges OAuth provider tokens for application JWT tokens and returns user information.

#### Request

- **Headers:**  
  `Content-Type: application/json`

- **Body:**
  ```json
  {
    "provider": "google" | "github",
    "token": "<OAuth token>"
  }
  ```

#### Response
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

### Callback URLs

The OAuth callback URLs are configured to handle redirects after successful authentication.

- **Development**: `http://127.0.0.1:8000/oauth/callback/`

**Usage:**  
1. Redirect user to provider’s authorization page  
2. Handle redirect back to your `callback_url`  
3. Extract `code` and exchange at `/users/oauth/login/`  

---

## Startup API

### Endpoints

- `GET /api/v1/startups/profiles/` — Retrieve a list of all startup profiles  
- `POST /api/v1/startups/profiles/` — Create a new startup profile  
- `GET /api/v1/startups/profiles/{id}/` — Retrieve detailed startup profile  
- `PATCH /api/v1/startups/profiles/{id}/` — Update an existing startup profile  
- `DELETE /api/v1/startups/profiles/{id}/` — Delete a startup profile  
- `GET /api/v1/startups/profiles/{id}/short/` — Retrieve short version of startup profile  
- `GET /api/v1/startups/search/` — Search startups using Elasticsearch  

**Supports filtering by:**  
industries__name, location__country, funding_stage, company_size, is_active, projects__status, projects__category__name

**Supports search by:**  
company_name, description, investment_needs, projects__title, projects__description

**Supports ordering by:**  
company_name, funding_stage, company_size, created_at

---

## Project API

### Endpoints

- `GET /api/v1/projects/` — Retrieve a list of all projects  
- `POST /api/v1/projects/` — Create a new project  
- `GET /api/v1/projects/{id}/` — Retrieve details of a specific project  
- `PATCH /api/v1/projects/{id}/` — Update an existing project  
- `DELETE /api/v1/projects/{id}/` — Delete a project  

---

## Validation Rules

### Startup Profile

- company_name: required, unique  
- description: required  
- website: optional, must be valid URL  
- logo: optional, must be image (jpg, png, ≤10MB)  
- funding_stage: required, must be one of predefined choices  
- investment_needs: optional  
- company_size: optional, must match predefined choices  
- location: required, must reference existing location  
- industries: optional, must reference existing industries  

### Project

- startup: required (must reference existing profile)  
- title: required  
- funding_goal: required if is_participant is true  
- current_funding: must not exceed funding_goal  
- business_plan: required if status is completed  
- email: required, must be valid  
- category: required  
- status: must be one of allowed enum values  

---

## Search API (Elasticsearch)

### Endpoint

- `GET /api/v1/startups/search/`

### Parameters

- search: full-text search across company_name, description, investment_needs  
- funding_stage, location.country, industries.name, company_size, is_active: filter fields  
- ordering: sort by company_name, funding_stage, created_at, etc.

### Response Example

```json
[
  {
    "id": 1,
    "company_name": "GreenTech",
    "description": "Eco-friendly solutions",
    "funding_stage": "Seed",
    "investment_needs": "Looking for angel investors",
    "company_size": "1-10",
    "is_active": true,
    "location": {
      "id": 1,
      "country": "Ukraine"
    },
    "industries": ["CleanTech", "Energy"]
  }
]
```

---

## Schema & Documentation

- `GET /api/schema/` — OpenAPI schema (JSON)  
- `GET /api/schema/swagger-ui/` — Swagger UI  
- `GET /api/schema/redoc/` — Redoc documentation  

---

## Healthcheck

- `GET /health/elasticsearch/` — Returns 200 OK if Elasticsearch is available, 503 otherwise  

---

## Notes

- All timestamps are in UTC and ISO 8601 format  
- All IDs are integers  
- All list endpoints support pagination via limit and offset query parameters  
- All endpoints are versioned under `/api/v1/` for future compatibility  

