# Forum-Project-Stage-CC
Forum Project Stage CC Template Repo

**Project Vision Statement:**

*"Empowering Innovation: Bridging Startups and Investors for Ukraine's Economic Growth"*

**Overview:**

In the dynamic world of entrepreneurship, the path from a transformative idea to a successful venture is often complex and challenging. Our WebAPI application, developed using the Django Rest Framework, is designed to be a cornerstone in simplifying this journey. We aim to create a robust and secure digital platform that caters to two pivotal groups in the business ecosystem: innovative startups with compelling ideas and forward-thinking investors seeking valuable opportunities.

All technical documentation is located in the `docs/` folder at the root of the repository:

- [`API.md`](docs/API.md): Detailed description of available endpoints and request/response formats.
- [`CONTRIBUTING_DOCS.md`](docs/CONTRIBUTING_DOCS.md): Guidelines and instructions for contributors and developers.



**Goals:**

1. **Fostering Collaborative Opportunities:** Our platform bridges startups and investors, enabling startups to showcase their groundbreaking proposals and investors to discover and engage with high-potential ventures.

2. **Seamless User Experience:** We prioritize intuitive navigation and interaction, ensuring that startups and investors can easily connect, communicate, and collaborate.

3. **Secure and Trustworthy Environment:** Security is at the forefront of our development, ensuring the confidentiality and integrity of all shared information and communications.

4. **Supporting Economic Growth:** By aligning startups with the right investors, our platform not only cultivates individual business success but also contributes significantly to the growth and diversification of Ukraine's economy.

**Commitment:**

We are committed to delivering a platform that is not just a marketplace for ideas and investments but a thriving community that nurtures innovation fosters economic development, and supports the aspirations of entrepreneurs and investors alike. Our vision is to see a world where every transformative idea has the opportunity to flourish and where investors can confidently fuel the engines of progress and innovation.

![image](https://github.com/mehalyna/Forum-Project-Stage-CC/assets/39273210/54b0de76-f6e3-4bf3-bf38-fb5bf1d1d63d)



### Basic Epics

0. **As a user of the platform**, I want the ability to represent both as a startup and as an investor company, so that I can engage in the platform's ecosystem from both perspectives using a single account.

   - Features:
     - implement the functionality for users to select and switch roles.

2. **As a startup company,** I want to create a profile on the platform, so that I can present my ideas and proposals to potential investors.
   
   - Features:
     -  user registration functionality for startups.
     -  profile setup page where startups can add details about their company and ideas.

3. **As an investor,** I want to view profiles of startups, so that I can find promising ideas to invest in.
   
   - Features:
     -  feature for investors to browse and filter startup profiles.
     -  viewing functionality for detailed startup profiles.

4. **As a startup company,** I want to update my project information, so that I can keep potential investors informed about our progress and milestones.
   
   - Features:
     -  functionality for startups to edit and update their project information.
     -  system to notify investors about updates to startups they are following.

5. **As an investor,** I want to be able to contact startups directly through the platform, so that I can discuss investment opportunities.
   
   - Features:
     -  secure messaging system within the platform for communication between startups and investors.
     -  privacy and security measures to protect the communication.

6. **As a startup company,** I want to receive notifications about interested investors, so that I can engage with them promptly.
   
   - Features:
     -  notification functionality for startups when an investor shows interest or contacts them.
     -  dashboard for startups to view and manage investor interactions.

7. **As an investor,** I want to save and track startups that interest me, so that I can manage my investment opportunities effectively.
   
   - Features:
     -  feature for investors to save and track startups.
     -  dashboard for investors to manage their saved startups and investment activities.

### Additional Features

- **Security and Data Protection**: Ensure that user data, especially sensitive financial information, is securely handled.
  
- **User Feedback System**: Create a system for users to provide feedback on the platform, contributing to continuous improvement.

- **Analytical Tools**: Implement analytical tools for startups to understand investor engagement and for investors to analyze startup potential.

### Agile Considerations

- Each user story can be broken down into smaller tasks and developed in sprints.
- Regular feedback from both user groups (startups and investors) should be incorporated.

---

### General Git Flow

1. Clone the repo and create your own feature branch from `main`.
2. Make sure to follow naming conventions below.
3. Commit frequently with clear, concise messages.
4. Push to remote and open a Pull Request (PR).
5. Wait for at least **3 code review approvals** before merging to `main`.

### Branch Naming Convention

Branch names should follow this format:

```

issue-\<ISSUE\_NUMBER>-<short-task-summary>

```

Examples:
```
- `issue-23-add-multimodal-upload`
- `issue-17-fix-langchain-vectorbug`
- `issue-12-improve-prompt-formatting`
```

> _Tip: Reference the GitHub Issue in your PR for context._

---

## Pull Request Guidelines

- Always link the related issue (e.g., "Closes #17").
- Add a clear title and description of your changes.
- Include screenshots or examples if UI-related.
- Run all tests before submitting a PR.
- Mark as **"Ready for Review"** only when complete.

---
## 🔐 Environment Variables

This project uses environment variables defined in a `.env` file at the root of the project.

### How it's loaded

- ✅ When using Docker Compose, the `.env` file is loaded automatically via the `env_file` directive.
- ✅ Inside Django, the variables are accessed using `python-decouple` (`config('SECRET_KEY')` etc).

### Hybrid Django + FastAPI Setup

This project integrates **Django** and **FastAPI** into a single ASGI application to support both traditional Django views and modern asynchronous FastAPI endpoints.

#### ASGI Application Structure

- `core/asgi.py` mounts both apps using `Starlette`'s `Mount` routing:
  - Django app is mounted at `/`
  - FastAPI app is mounted at `/api/fastapi`

#### Running Locally

```bash
uvicorn core.asgi:application --reload
```


### Elasticsearch Integration

This project integrates Django with Elasticsearch to provide powerful search and filtering capabilities.

🚀 Technologies:
Django: The core web framework.
Elasticsearch: The search and analytics engine.
django-elasticsearch-dsl & django-elasticsearch-dsl-drf: Libraries for seamless Elasticsearch integration with Django.
drf-spectacular: Tool for automatic API documentation (Swagger/OpenAPI).

💻 Getting Started:
This guide will get your local development environment up and running.

Prerequisites:
Ensure you have Docker installed to run Elasticsearch locally.
1. Run Elasticsearch: Start the Elasticsearch container using Docker Compose.
```
docker-compose up -d elasticsearch
```
2. Install Dependencies: Install the required Python packages from your requirements.txt file.
```
pip install -r requirements.txt
```
3. Index Data: Build your Elasticsearch indexes and sync them with your database. This is a crucial step to ensure all your data is searchable.
```
python manage.py search_index --rebuild
```
4. Run the Django Server: Start the development server to access the API.
```
python manage.py runserver
```

🔍 API Endpoints:
All API endpoints now support advanced search and filtering via Elasticsearch.

API Documentation:
Swagger UI and ReDoc documentation are automatically generated for all endpoints.
- Swagger UI: /api/schema/swagger-ui/
- ReDoc: /api/schema/redoc/

Startups Endpoint:
- URL: /api/startups/
- Method: GET
Description: Perform full-text search, filtering, and ordering on startup data.

Query Parameters:
- search or q: Full-text keyword to match in company_name and description.
- industries.name: Filters by industry name (e.g., Fintech).
- location.country: Filters by the country (e.g., USA).
- funding_stage: Filters by funding stage (e.g., Seed, Series A).
- ordering: Sorts results. Use a minus sign for descending order (e.g., -funding_stage).

Example:
```
curl "http://localhost:8000/api/startups/?search=ai&funding_stage=seed&ordering=-funding_stage"
```

Projects Endpoint:
- URL: /api/projects/
- Method: GET
Description: Search and filter project data.

Query Parameters:
- search or q: Full-text keyword to match in title and description.
- category.name: Filters by the project's category name.
- startup.company_name: Filters by the name of the associated startup.

Example:
```
curl "http://localhost:8000/api/projects/?search=solar&category.name=Tech"
```

# OAuth Authentication Setup

This project supports authentication using **OAuth providers** (**Google** and **GitHub**).

## 🔹 Google OAuth Setup

### Create Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Navigate to **APIs & Services → Credentials**.
4. Click **Create Credentials → OAuth 2.0 Client ID**.
5. If prompted, configure the consent screen.
6. Add **Authorized Redirect URIs**:  `http://yourdomain.com/oauth/callback/`(example)
7. Copy the **Client ID** and **Client Secret**.

### Environment Variables
Add the following to `.env` file:

```text
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```
## 🔹 GitHub OAuth Setup

### Create GitHub OAuth App
1. Go to [GitHub Developer Settings](https://github.com/settings/developers).
2. Click **New OAuth App**.
3. Fill in application details.
4. Set **Authorization Callback URL**:  `http://yourdomain.com/oauth/callback/`
5. Copy the **Client ID** and generate a **Client Secret**.

### Environment Variables
Add these to `.env` file:

```text
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
```

## 🔐 Authentication Flow

### OAuth Login Process

#### Client-Side OAuth Flow
1. Frontend redirects users to **Google/GitHub OAuth consent screen**.
2. After consent, provider redirects back with **authorization code**.
3. Frontend exchanges code for **access token** using provider's token endpoint.

#### Backend Token Validation
Example request:

```http
POST api/v1/auth/oauth/login/
Content-Type: application/json

{
  "provider": "google",  // or "github"
  "access_token": "oauth_provided_access_token"
}
```
#### Backend Processing
1. Validates access token with provider's API.
2. Retrieves user profile information.
3. Creates or updates local user record.
4. Issues JWT tokens for authentication(Only for users with is_active=True).

#### Response
```json
{
  "access": "jwt_access_token",
    "user": {
    "id": "user_123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_phone": "",
    "title": "",
    "role": "user"
  }
}
```
### JWT Token Issuance
The system uses Django REST Framework Simple JWT for token management:
- Access Token: Short-lived (default 5 minutes) for API authentication
- Refresh Token - set in HTTP-only cookie: Longer-lived (default 24 hours) for obtaining new access tokens.
- Automatic User Creation: New users are automatically created with data from OAuth providers.
### Troubleshooting
Common Errors
|    Error Message                        |      HTTP Status    |                    Cause                   |                     Solution                          |
|-----------------------------------------|---------------------|--------------------------------------------|-------------------------------------------------------|
| "Invalid provider"                      | 400 Bad Request     | provider missing/invalid                   | Ensure both `provider` and `access_token` are strings.|
| "access_token is missing"               | 400 Bad Request     | Missing token                              | Provide access_token                                  |
| "Unsupported provider"                  | 400 Bad Request     | Provider other than Google/GitHub          | Use only `"google"` or `"github"` as provider value.  |
| "OAuth authentication failed"           | 400 Bad Request     | Expired, malformed, or revoked token       | Re-authenticate with provider                         |
| "No verified primary email found"       | 403 Forbidden       | GitHub account lacks verified email        | User must add/verify email in GitHub settings.        |
