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

## Startup API

### Endpoints

- `GET /api/v1/startups/profiles/` — Retrieve a list of all startup profiles  
- `GET /api/v1/startups/profiles/{id}/` — Retrieve detailed startup profile  
- `GET /api/v1/startups/profiles/{id}/short/` — Retrieve short version of startup profile  
- `GET /api/v1/startups/search/` — Search startups using Elasticsearch  

**Supports filtering by:**  
industries__name, location__country, funding_stage, company_size, is_active, projects__status, projects__category__name

**Supports search by:**  
company_name, description, investment_needs, projects__title, projects__description

**Supports ordering by:**  
company_name, funding_stage, company_size, created_at

### Request Example: Create Startup Profile

```json
{
  "company_name": "GreenTech",
  "description": "Eco-friendly solutions",
  "website": "https://greentech.ua",
  "logo": null,
  "funding_stage": "Seed",
  "investment_needs": "Looking for angel investors",
  "company_size": "1-10",
  "location": 1,
  "industries": [2, 3]
}
```

### Response Example: Created Startup Profile (201 Created)

```json
{
  "id": 1,
  "company_name": "GreenTech",
  "description": "Eco-friendly solutions",
  "website": "https://greentech.ua",
  "logo": null,
  "funding_stage": "Seed",
  "investment_needs": "Looking for angel investors",
  "company_size": "1-10",
  "location": {
    "id": 1,
    "country": "Ukraine"
  },
  "industries": [
    {"id": 2, "name": "CleanTech"},
    {"id": 3, "name": "Energy"}
  ],
  "projects": [],
  "created_at": "2025-08-05T00:00:00Z",
  "updated_at": "2025-08-05T00:00:00Z"
}
```

---

## Project API

### Endpoints

- `GET /api/v1/projects/` — Retrieve a list of all projects  
- `POST /api/v1/projects/` — Create a new project  
- `GET /api/v1/projects/{id}/` — Retrieve details of a specific project  
- `PATCH /api/v1/projects/{id}/` — Update an existing project  
- `DELETE /api/v1/projects/{id}/` — Delete a project  

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
  "category": {
    "id": 2,
    "name": "Artificial Intelligence"
  },
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
