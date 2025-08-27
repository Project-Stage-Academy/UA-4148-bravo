# Contributing to API Documentation

This guide explains how to contribute new API documentation to the `docs/API.md` file in a consistent and maintainable way.

## Recent Updates (Startup Investor API)

The following functionality has been implemented and documented:

- **Startup Model Enhancements**: Added fields `name`, `industry`, `stage`, `funding_needed`, `team_size`.
- **Startup Serializer**: Controls which fields are visible to investors.
- **Startup API Endpoints**:
  - `GET /api/v1/startups/` — list of startups (with filtering support).
  - `GET /api/v1/startups/{id}/` — details of a specific startup.
  - `GET /api/v1/startups/search/?q=<keyword>` — keyword search in startup profiles.
- **Filtering**: Implemented using `django-filters`. Available filters include `industry`, `min_team_size`, `funding_needed__lte`.
- **Permissions**: Access restricted to authenticated users with the `investor` role.
- **Tests**: Unit tests cover list, detail, filtering, and access rules.
- **Documentation**: Swagger and `API.md` updated with new endpoints.

---

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