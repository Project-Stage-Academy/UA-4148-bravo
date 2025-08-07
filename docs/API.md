# Forum Project Stage CC WebAPI Documentation

This document describes the available endpoints, request formats, response structures, and validation rules for the **Forum Project Stage CC WebAPI**.  
It is organized by module to allow each developer to maintain and extend their respective sections.

---

## Authentication

All endpoints require JWT authentication.  
Include the token in the `Authorization` header using the following format:

Authorization: Bearer <your_access_token>

---

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