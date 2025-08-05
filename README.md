# Forum-Project-Stage-CC
Forum Project Stage CC Template Repo

**Project Vision Statement:**

*"Empowering Innovation: Bridging Startups and Investors for Ukraine's Economic Growth"*

**Overview:**

In the dynamic world of entrepreneurship, the path from a transformative idea to a successful venture is often complex and challenging. Our WebAPI application, developed using the Django Rest Framework, is designed to be a cornerstone in simplifying this journey. We aim to create a robust and secure digital platform that caters to two pivotal groups in the business ecosystem: innovative startups with compelling ideas and forward-thinking investors seeking valuable opportunities.

All technical documentation is located in the [docs/](docs/) folder.

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

---
## Authentication API Guide

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