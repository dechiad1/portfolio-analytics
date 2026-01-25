## Feature: add user functionality & OAuth2 login flow to the project

Remember to read the content in CLAUDE.md, .claude/agents & .claude/reference FIRST to understand the coding conventions, desired repository structures & goal of the project

### Completion
when all the tasks are fully complete & tested, print just DONEZO. 

DO NOT SKIP THIS STEP. IT IS REQUIRED WHEN FULLY COMPLETE


### Description
This application will have users that persit data over time. We want to keep track of users & user information in our database but not handle log in flow. We want to integrate with google & apple OAuth2 flows so that a user can create an account on this application with their google or apple account. After the user creates an account, they will then be able to login with it when they return. For local development, we should use a trusted image that acts as an identity provider playing the role of google/apple that is ephemeral & fully contained in our local environment.

We should follow standard OAuth2 flow: we have a login screen, redirect the user to the IDP & passing the IDP a url to return the user to, validating the signature of the token the IDP provided.

We want the handoff between OAuth2 flow & our application to be after we validate the token. We should save the username, user email in our table. We should also set up a claim for our application in the local IDP container: AdminUser. Give this to the dechiada@gmail.com user.

### AC
- IDP container running locally as part of portfolio analytics docker compose
- IDP container all users in the application database
- IDP container's volume persists so we can kill the container & restart it easily
- Task exists in Taskfile.yml to create a new user in the IDP
- Login page has a "sign in with" flow
- Login page does not allow logging in directly to the application; user must create an account with IDP
	- in local that is the local dev container
	- in the dev, prod environments this will be apple, google
- Playwright tests account for the OAuth2 flow
- The user database is properly populated on create user flow after successful token validation
- LastLogin time is updated whenever a user logs in

### Testing
- you have access to run tests
- you have access to run playwright
- the UI dev server is running on port 3001
- the app server is running on port 8001

---

## Implementation Plan

### Design Decisions
- **Local IDP**: mock-oauth2-server (lightweight, ~128MB)
- **Session Management**: JWT in httpOnly cookie
- **Admin Claim**: Placeholder for future; `is_admin` already exists in users table
- **Production OAuth**: Architecture only - Google/Apple not implemented now

---

## Phase 1: Database & Domain Layer

### 1.1 Database Migration
**File**: `api/alembic/versions/<timestamp>_add_oauth_fields.py`

Add to `users` table:
- `last_login` (TIMESTAMPTZ) - Updated on each login
- `oauth_provider` (VARCHAR 50) - e.g., "mock-oauth2", "google"
- `oauth_subject` (VARCHAR 255) - The `sub` claim from IDP
- Make `password_hash` nullable (OAuth users won't have one)
- Add index on `(oauth_provider, oauth_subject)`

### 1.2 Update User Model
**File**: `api/domain/models/user.py`

Add fields: `last_login`, `oauth_provider`, `oauth_subject`; make `password_hash` optional.

### 1.3 Create OAuth Port
**File**: `api/domain/ports/oauth_provider.py`

Interface with methods:
- `get_authorization_url(state, nonce) -> str`
- `exchange_code_for_tokens(code) -> OAuthTokens`
- `validate_id_token(id_token, nonce) -> OAuthUserInfo`

### 1.4 Update UserRepository Port
**File**: `api/domain/ports/user_repository.py`

Add methods:
- `get_by_oauth_subject(provider, subject) -> User | None`
- `update_last_login(user_id, timestamp) -> None`

### 1.5 Create OAuth Service
**File**: `api/domain/services/oauth_service.py`

Core logic:
- `generate_state_and_nonce()` - CSRF protection
- `get_authorization_url(state, nonce)` - Build redirect URL
- `handle_callback(code, nonce, provider)` - Exchange code, validate token, find/create user, update last_login, create session JWT
- `verify_session_token(token)` - Validate JWT from cookie
- Admin email check: `dechiada@gmail.com` gets `is_admin=True`

---

## Phase 2: Adapter Layer

### 2.1 Mock OAuth2 Provider Adapter
**File**: `api/adapters/oauth/mock_oauth_provider.py`

Implements `OAuthProvider` port:
- Uses `httpx` for token exchange
- Uses `PyJWKClient` for JWKS-based ID token validation (RS256)
- Configurable issuer_url, client_id, client_secret, redirect_uri

### 2.2 Update User Repository
**File**: `api/adapters/postgres/user_repository.py`

Add implementations for new port methods.

---

## Phase 3: API Layer

### 3.1 OAuth Router
**File**: `api/api/routers/oauth.py`

Endpoints:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/oauth/login` | GET | Redirects to IDP with state/nonce cookies |
| `/oauth/callback` | GET | Handles IDP callback, validates state, sets session cookie, redirects to app |
| `/oauth/logout` | POST | Clears session cookie |
| `/oauth/me` | GET | Returns current user from session cookie |

Cookie settings: `httponly=True`, `samesite=lax`, `secure=True` (in prod)

### 3.2 Update Dependencies
**File**: `api/dependencies.py`

Add:
- `OAuthConfig` model (issuer_url, client_id, client_secret, redirect_uri)
- Add `oauth: Optional[OAuthConfig]` to `AppConfig`
- `get_oauth_provider()` factory
- `get_oauth_service()` factory

### 3.3 Config Updates
**File**: `api/config/local.yaml`

Add OAuth section:
```yaml
oauth:
  issuer_url: http://localhost:8080/default
  client_id: portfolio-analytics
  client_secret: portfolio-secret
  redirect_uri: http://localhost:8001/oauth/callback
```

### 3.4 Register Router
**File**: `api/main.py`

Include OAuth router, update CORS for credentials.

---

## Phase 4: Docker Infrastructure

### 4.1 Add mock-oauth2-server
**File**: `docker/docker-compose.yml`

```yaml
mock-oauth2:
  image: ghcr.io/navikt/mock-oauth2-server:2.1.1
  container_name: portfolio-analytics-oauth
  ports:
    - "8080:8080"
  environment:
    JSON_CONFIG: |
      {
        "interactiveLogin": true,
        "tokenCallbacks": [{
          "issuerId": "default",
          "tokenExpiry": 3600,
          "requestMappings": [{
            "requestParam": "scope",
            "match": "*",
            "claims": {
              "sub": "@@subject@@",
              "email": "@@email@@",
              "email_verified": true
            }
          }]
        }]
      }
  volumes:
    - oauth_data:/tmp/mock-oauth2-server
  restart: unless-stopped
```

Add `oauth_data` volume.

### 4.2 Taskfile Commands
**File**: `Taskfile.yml`

Add tasks:
- `oauth:create-user` - Create test user with EMAIL, PASSWORD, SUBJECT vars
- `oauth:create-admin` - Create admin user (dechiada@gmail.com)

---

## Phase 5: Frontend Changes

### 5.1 Update API Client
**File**: `web/src/shared/api/client.ts`

Add `credentials: 'include'` to all fetch calls for cookie transmission.
Remove localStorage token handling.

### 5.2 Update Auth API
**File**: `web/src/shared/api/authApi.ts`

- `getOAuthLoginUrl()` - Returns `/oauth/login` URL
- `logout()` - POST to `/oauth/logout`
- `getCurrentUser()` - GET `/oauth/me`
- Remove `login()`, `register()` functions

### 5.3 Update Auth Context
**File**: `web/src/shared/contexts/AuthContext.tsx`

- Remove token state, login/register methods
- Keep: `user`, `isLoading`, `isAuthenticated`, `logout`, `refreshUser`
- `refreshUser()` calls `/oauth/me` to check session

### 5.4 Redesign Login Page
**File**: `web/src/pages/auth/LoginPage.tsx`

- Remove email/password form
- Single "Sign in with Identity Provider" button
- Button redirects to `getOAuthLoginUrl()`

### 5.5 Update Routes
**File**: `web/src/App.tsx`

- Remove `/register` route
- Keep `/login` route

---

## Phase 6: Playwright Tests

### 6.1 OAuth Flow Tests
**File**: `web/e2e/oauth.spec.ts`

Test cases:
1. Login click redirects to OAuth provider (localhost:8080)
2. Complete OAuth flow and access protected route
3. Logout clears session and redirects to login
4. Session persists across page refresh
5. Unauthenticated access redirects to login

### 6.2 Update Existing Tests
**File**: `web/e2e/portfolio.spec.ts`

Update test setup to use OAuth flow instead of registration.

---

## Critical Files

| File | Change Type |
|------|-------------|
| `api/alembic/versions/*_add_oauth_fields.py` | Create |
| `api/domain/models/user.py` | Modify |
| `api/domain/ports/oauth_provider.py` | Create |
| `api/domain/ports/user_repository.py` | Modify |
| `api/domain/services/oauth_service.py` | Create |
| `api/adapters/oauth/mock_oauth_provider.py` | Create |
| `api/adapters/postgres/user_repository.py` | Modify |
| `api/api/routers/oauth.py` | Create |
| `api/dependencies.py` | Modify |
| `api/config/local.yaml` | Modify |
| `api/main.py` | Modify |
| `docker/docker-compose.yml` | Modify |
| `Taskfile.yml` | Modify |
| `web/src/shared/api/client.ts` | Modify |
| `web/src/shared/api/authApi.ts` | Modify |
| `web/src/shared/contexts/AuthContext.tsx` | Modify |
| `web/src/pages/auth/LoginPage.tsx` | Modify |
| `web/src/App.tsx` | Modify |
| `web/e2e/oauth.spec.ts` | Create |

---

## Verification

1. **Docker**: `task docker:up` starts both postgres and mock-oauth2
2. **API**: `task run:api` starts without errors, `/oauth/login` redirects to IDP
3. **Frontend**: `npm run dev` in web/, login button redirects to mock-oauth2
4. **Full Flow**:
   - Click "Sign in" -> redirected to mock-oauth2 (port 8080)
   - Enter email/subject in mock form -> redirected back to app
   - Session cookie set, user created in DB with last_login
   - Refresh page -> still authenticated
   - Logout -> cookie cleared, redirected to login
5. **Playwright**: `npx playwright test` passes all OAuth flow tests
6. **Admin Check**: Login with dechiada@gmail.com sets is_admin=True in DB

---

## Notes

- Old `/auth/login`, `/auth/register` endpoints can be deprecated/removed after OAuth is working
- Production OAuth (Google/Apple) follows same adapter pattern - just swap provider config
- No PKCE implemented (mock-oauth2-server handles this; add for production if needed)
