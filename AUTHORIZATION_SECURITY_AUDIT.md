# Authorization Security Audit Report

**Language/Stack:** Python/Django REST Framework  
**Project:** Forum Project Stage CC WebAPI - Startup funding platform with user authentication

## 1) EXECUTIVE ONE-LINER
**CRITICAL: Frontend logout implementation fails to send refresh token for blacklisting, allowing indefinite session persistence even after logout.**

## 2) FINDINGS (ordered by severity)

### FINDING-1
- **Severity:** Critical
- **Location:** `frontend/src/provider/AuthProvider/authProvider.jsx:171`
- **Title:** Logout function fails to blacklist refresh token
- **Explanation:** The logout function calls `/api/v1/auth/jwt/blacklist/` without sending the required refresh token in the request body. This means refresh tokens remain valid indefinitely after logout, allowing session hijacking if tokens are compromised.
- **Suggested fix:** Include refresh token in logout request body. The API expects `{"refresh": "<token>"}` but the frontend sends an empty POST request.
- **Code example:**
```javascript
async function logout() {
    const refreshToken = localStorage.getItem('refresh'); // Get stored token
    await api.post("/api/v1/auth/jwt/blacklist/", { 
        refresh: refreshToken 
    }).catch(() => {
        console.log('User not found');
    });
    setAccessToken(null);
    setUser(null);
    localStorage.removeItem('refresh'); // Clear stored tokens
}
```
- **Test to add:** `test_frontend_logout_blacklists_refresh_token` - verify refresh token becomes invalid after logout

### FINDING-2
- **Severity:** Major
- **Location:** `users/urls.py:24,33`
- **Title:** Duplicate logout endpoints with different implementations
- **Explanation:** Two different logout endpoints exist (`jwt/logout/` and `auth/jwt/logout/`) pointing to different view classes, creating confusion and potential security gaps where clients might use the wrong endpoint.
- **Suggested fix:** Remove duplicate endpoint and standardize on one logout URL with proper documentation.
- **Code example:**
```python
# Remove line 33, keep only:
path('jwt/logout/', JWTLogoutView.as_view(), name='jwt-logout'),
```
- **Test to add:** `test_single_logout_endpoint_exists` - verify only one logout endpoint is available

### FINDING-3
- **Severity:** Major
- **Location:** `projects/permissions.py:6`
- **Title:** Insufficient ownership validation in project permissions
- **Explanation:** The `IsOwnerOrReadOnly` permission only checks `obj.startup.user == request.user` without validating the user's actual relationship to the startup, potentially allowing unauthorized access if startup ownership is manipulated.
- **Suggested fix:** Add explicit startup ownership validation and check user permissions on the startup object.
- **Code example:**
```python
def has_object_permission(self, request, view, obj):
    if request.method in permissions.SAFE_METHODS:
        return True
    startup = obj.startup
    return (startup.user == request.user and 
            request.user.is_active and
            startup.user.is_active)
```
- **Test to add:** `test_project_permission_validates_startup_ownership` - ensure proper ownership chain validation

### FINDING-4
- **Severity:** Major
- **Location:** `users/views.py:1000-1059` (OAuthTokenObtainPairView)
- **Title:** Missing OAuth token validation and expiry checks
- **Explanation:** OAuth tokens from Google/GitHub are accepted without validating expiry, revocation status, or proper scopes, potentially allowing access with stale or compromised OAuth tokens.
- **Suggested fix:** Add OAuth token validation including expiry and revocation checks before generating JWT tokens.
- **Code example:**
```python
def validate_oauth_token(self, access_token, provider):
    # Add token introspection/validation
    if provider == 'google':
        response = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?access_token={access_token}'
        )
        if response.status_code != 200:
            raise ValidationError("Invalid or expired OAuth token")
    return True
```
- **Test to add:** `test_oauth_token_validation_rejects_expired_tokens` - verify expired OAuth tokens are rejected

### FINDING-5
- **Severity:** Minor
- **Location:** `core/settings.py:124-134`
- **Title:** JWT signing algorithm not explicitly specified
- **Explanation:** While SimpleJWT defaults to HS256, the algorithm is not explicitly configured, potentially allowing algorithm confusion attacks if not properly validated.
- **Suggested fix:** Explicitly specify the JWT signing algorithm in SIMPLE_JWT settings.
- **Code example:**
```python
SIMPLE_JWT = {
    'ALGORITHM': 'HS256',  # Explicitly specify algorithm
    'SIGNING_KEY': SECRET_KEY,
    # ... other settings
}
```
- **Test to add:** `test_jwt_algorithm_is_hs256` - verify JWT tokens use HS256 algorithm

### FINDING-6
- **Severity:** Minor
- **Location:** `core/settings.py:299` (missing)
- **Title:** Missing secure cookie and HTTPS enforcement
- **Explanation:** No configuration found for secure cookie flags or HTTPS enforcement, potentially allowing token theft over insecure connections.
- **Suggested fix:** Add secure cookie configuration and HTTPS enforcement for production.
- **Code example:**
```python
# Add to settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
```
- **Test to add:** `test_production_security_headers_enabled` - verify security headers in production

## 3) SECURITY CHECKLIST

- **JWT signed correctly (alg, secret storage)?:** Y — Uses HS256 algorithm with SECRET_KEY from environment, but algorithm not explicitly configured
- **Token expiry present and enforced?:** Y — Access tokens expire in 30 minutes, refresh tokens in 1 day (core/settings.py:124-126)  
- **Token revocation or blacklist?:** PARTIAL — Blacklist is configured (`BLACKLIST_AFTER_ROTATION: True`) but frontend logout doesn't use it
- **Proper use of HTTP-only & Secure cookies (if using cookies)?:** N — No evidence of secure cookie configuration found
- **Role checks implemented on server-side (not only client-side)?:** Y — Server-side role checks in users/permissions.py and users/models.py with UserRole model
- **Principle of least privilege applied?:** PARTIAL — Role-based permissions exist but some endpoints may be over-permissive

## 4) SUGGESTED TEST CASES

1. **test_logout_blacklists_refresh_token** - Verify that after logout, the refresh token cannot be used to generate new access tokens
2. **test_expired_oauth_tokens_rejected** - Ensure OAuth tokens past their expiry time are rejected during authentication
3. **test_project_access_requires_valid_ownership** - Confirm users can only access projects they legitimately own through valid startup ownership
4. **test_jwt_token_algorithm_consistency** - Verify all JWT tokens use the expected signing algorithm and cannot be tampered with
5. **test_inactive_user_tokens_invalid** - Ensure tokens for deactivated users are immediately invalidated
6. **test_role_based_access_enforcement** - Verify role-based permissions are enforced on protected endpoints

## 5) QUICK PATCH (Top 1 fix)

**Fix for FINDING-1 (Critical logout issue):**

```diff
--- a/frontend/src/provider/AuthProvider/authProvider.jsx
+++ b/frontend/src/provider/AuthProvider/authProvider.jsx
@@ -168,7 +168,12 @@ function AuthProvider({ children }) {
      * Res: 205
      */
     async function logout() {
-        await api.post("/api/v1/auth/jwt/blacklist/").catch(() => {
+        const refreshToken = localStorage.getItem('refresh') || 
+                           sessionStorage.getItem('refresh');
+        await api.post("/api/v1/auth/jwt/blacklist/", {
+            refresh: refreshToken
+        }).catch(() => {
             console.log('User not found');
         });
         setAccessToken(null);
         setUser(null);
+        localStorage.removeItem('refresh');
+        sessionStorage.removeItem('refresh');
     }
```

This critical fix ensures refresh tokens are properly blacklisted during logout, preventing indefinite session persistence after logout.