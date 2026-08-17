# Auth Login & Protect API

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![Supabase](https://img.shields.io/badge/auth-Supabase-3ECF8E.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

A FastAPI backend that authenticates users through Supabase Auth and protects specific routes with bearer-token verification.

---

## Table of Contents

- [Overview](#overview)
- [The Trust Triangle](#the-trust-triangle)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Example Usage](#example-usage)
- [Error Format](#error-format)
- [Interactive Docs (Swagger UI)](#interactive-docs-swagger-ui)
- [How Auth Verification Was Tested](#how-auth-verification-was-tested)
- [AI vs Me](#ai-vs-me)
- [License](#license)

---

## Overview

This API doesn't manage passwords or sessions itself — Supabase does that. The server's job is narrower: hand off signup/login to Supabase, then verify the JWT Supabase issues on every request to a protected route.

## The Trust Triangle

1. **Sign up / log in** — the client sends credentials directly to this API, which forwards them to Supabase.
2. **The token** — Supabase validates the credentials and returns a JWT access token.
3. **The request** — the client sends that token back on later requests, in the `Authorization: Bearer <token>` header.
4. **Verification** — this server calls Supabase to check the token is real and unexpired before opening a protected route.

## Getting Started

### Prerequisites

- Python 3.10+
- A free [Supabase](https://supabase.com) account with a project created

### Setup

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env
# edit .env with your Project URL and anon key from
# Supabase Dashboard -> Project Settings -> API
```

### Run

```bash
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Environment Variables

| Variable                     | Required | Purpose                                                        |
|-------------------------------|----------|-------------------------------------------------------------------|
| `SUPABASE_URL`                 | Yes      | Your project's API URL                                          |
| `SUPABASE_KEY`                 | Yes      | Your project's anon/public key                                  |
| `PORT`                          | No       | Documented for reference; uvicorn's `--port` flag controls this in practice |
| `SUPABASE_SERVICE_ROLE_KEY`     | No       | Enables `/auth/logout` to force-revoke a specific token server-side |

Without `SUPABASE_SERVICE_ROLE_KEY`, logout still verifies the token and returns `204` — it just can't force that exact token to stop working before it naturally expires. The anon key has no permission to revoke tokens; only the service role key does.

## API Reference

| Method | Path                  | Auth required | Description                              | Success | Errors     |
|--------|------------------------|:---:|---------------------------------------------|---------|------------|
| GET    | `/public/info`          | No  | Public, unauthenticated data                | `200`   | —          |
| POST   | `/auth/signup`          | No  | Create a new user account                   | `201`   | `400`      |
| POST   | `/auth/login`           | No  | Authenticate, receive JWT tokens            | `200`   | `400`, `401` |
| POST   | `/auth/logout`          | **Yes** | Terminate the session                    | `204`   | `401`      |
| GET    | `/protected/profile`    | **Yes** | Read the verified user's own profile     | `200`   | `401`      |
| GET    | `/protected/dashboard`  | **Yes** | Second protected route, same auth check  | `200`   | `401`      |

## Example Usage

**Sign up**
```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

**Log in**
```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```
Response includes `access_token` — copy it for the next calls.

**Access a protected route**
```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN>"
```

**Log out**
```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN>"
```

## Error Format

Every error returns a JSON body with a single `error` key:

```json
{ "error": "Invalid or expired token" }
```

| Status | Meaning       | When it happens                                     |
|--------|---------------|---------------------------------------------------------|
| `400`  | Bad Request   | Missing email/password on signup or login                |
| `401`  | Unauthorized  | Wrong login credentials, missing token, or invalid/expired token |

## Interactive Docs (Swagger UI)

FastAPI auto-generates the OpenAPI spec, and the `HTTPBearer` security dependency used on every protected route makes the **Authorize** padlock appear automatically — no manual spec-writing needed.

To test a protected route in the browser: log in via `/auth/login` in Swagger's "Try it out", copy the `access_token` from the response, click **Authorize** at the top of the page, paste it in, then try `/protected/profile`.

Screenshot placeholder — replace with your own image of `http://localhost:8000/docs` showing the padlock icons.

## How Auth Verification Was Tested

1. Called `/protected/profile` and `/protected/dashboard` with no `Authorization` header — both returned `401 {"error": "Access token required"}`.
2. Called both with a syntactically-invalid bearer token — both returned `401 {"error": "Invalid or expired token"}`.
3. Logged in via `/auth/login`, copied the real `access_token`, and confirmed both protected routes returned `200` with real user data.
4. Changed one character of a valid token and confirmed it was rejected with `401` again.
5. Inspected `/openapi.json` directly and confirmed the `HTTPBearer` security scheme is attached to exactly `/auth/logout`, `/protected/profile`, and `/protected/dashboard` — not to the public or signup/login routes.

## AI vs Me

**My prompt** (written from memory, without copying the assignment text):

> Build a FastAPI backend in Python that uses Supabase for user authentication. I need these routes:
> - `POST /auth/signup` — takes `email` and `password` as JSON, creates a Supabase user, returns 201 with the user object. Return 400 if email or password is missing.
> - `POST /auth/login` — logs in with Supabase, returns the access token and refresh token with status 200. Return 401 if login fails, 400 if fields are missing.
> - `POST /auth/logout` — requires a valid Supabase token in the Authorization header as a Bearer token, logs the user out, returns 204.
> - `GET /protected/profile` — requires a valid bearer token, returns the user's id, email, and created_at. Return 401 if there's no token or it's invalid.
> - `GET /public/info` — returns a public message, no auth needed.
> - Use one reusable dependency for checking the token so I'm not repeating that logic in every protected route.
> - Set up Swagger UI at /docs with a working "Authorize" button for bearer tokens.
> - Read the Supabase URL and key from a .env file.

The generated code lives in `ai-version/main.py`, untouched, next to this hand-built version. Running `python -c "import main"` on it, without editing anything, surfaces two real bugs before any request is even possible:

1. **Crashes on startup with no `.env` configured.** `create_client(SUPABASE_URL, SUPABASE_KEY)` runs at import time with no guard, so if the environment variables aren't set it throws `SupabaseException: supabase_url is required` and the whole app fails to start — no warning, no partial functionality. My version prints a warning and starts anyway, using a placeholder URL, so `/public/info` and the 401 paths still work even before Supabase is configured.
2. **`Depends` is used but never imported.** Both `logout` and `profile` reference `Depends(get_current_user)`, but `fastapi.Depends` was never imported — only `FastAPI`, `Header`, and `HTTPException` were. This is a `NameError` at import time, confirmed by actually running it. The AI wrote code that calls a function it forgot to import.

**Where the AI did reasonably well:**
- Token extraction: `authorization.split(" ")[1]` does pull the token out of `Bearer <token>` for a well-formed header — I understand exactly why it works and where it breaks (see below).
- The overall route shape and status codes it aimed for (201/200/204/401/400) matched my prompt closely.

**Security and correctness gaps, once the two crashes above are fixed:**
- `authorization.split(" ")[1]` throws an unhandled `IndexError` (→ an ugly 500, not a clean 401) if the header exists but has no space in it, e.g. `Authorization: sometoken`. My version checks `.startswith("Bearer ")` first and only proceeds if that's true, so a malformed header still cleanly returns `401 {"error": "Access token required"}`.
- `if not user:` in `get_current_user` is checking truthiness of the whole Supabase response object, which is very unlikely to ever evaluate to `False` even when the token is invalid — the actual failure mode from `supabase.auth.get_user()` on a bad token is an exception, which this code doesn't catch at all. My version wraps the call in `try/except` and checks `response.user is None`, which is what actually distinguishes a valid token from an invalid one.
- Errors return FastAPI's default `{"detail": "..."}` shape instead of the `{"error": "..."}` the assignment spec asks for — never addressed in the AI's version.
- No second protected route (`/protected/dashboard`) was generated, so there's nothing proving the auth dependency is genuinely reusable across more than one endpoint — my prompt asked for a "reusable dependency" but never explicitly asked for a second route to prove it, which is on me, not the AI.
- No handling for `SUPABASE_SERVICE_ROLE_KEY` or any equivalent — `logout()` calls `supabase.auth.sign_out()` with the anon client, which (per Supabase's actual API surface) doesn't force-revoke the token a specific client presented. It silently does something that looks like logout but has no real effect on that token's validity.

**What my prompt forgot to specify, and what the AI silently decided instead:**
- I never specified the error response *shape* (`{"error": ...}` vs `{"detail": ...}`) — the AI defaulted to FastAPI's built-in `HTTPException` behavior rather than asking or guessing at a convention.
- I never said what should happen on a malformed (spaceless) `Authorization` header — the AI silently assumed it would always be well-formed, which is exactly the kind of client input a server should never trust.
- I didn't mention exception handling around the Supabase SDK calls at all — the AI wrote the "happy path" only and left every external call unguarded.

**One rematch, in one sentence:** adding "wrap every Supabase call in try/except and return the specific status code on failure, and use `response.user is None` rather than a general truthiness check to detect an invalid token" to the prompt would likely have caught most of these — importing `Depends` remains a coin flip either way, which is the real argument for running the code rather than just reading it.

## License

MIT.