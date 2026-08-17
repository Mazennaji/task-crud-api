from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from auth import admin_client, get_current_user
from supabase_client import supabase

app = FastAPI(title="Auth Login & Protect API", version="1.0")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


class Credentials(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


@app.get("/public/info", description="Public endpoint — no authentication required.")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.post("/auth/signup", status_code=201, description="Create a new user account via Supabase Auth.")
def signup(creds: Credentials):
    if not creds.email or not creds.password:
        raise HTTPException(status_code=400, detail="email and password are required")

    try:
        result = supabase.auth.sign_up({"email": creds.email, "password": creds.password})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"user": result.user}


@app.post("/auth/login", description="Authenticate and receive a JWT access token.")
def login(creds: Credentials):
    if not creds.email or not creds.password:
        raise HTTPException(status_code=400, detail="email and password are required")

    try:
        result = supabase.auth.sign_in_with_password({"email": creds.email, "password": creds.password})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "user": result.user,
    }


@app.post(
    "/auth/logout",
    status_code=204,
    description="Terminate the current session. Protected — requires a valid bearer token.",
)
def logout(auth=Depends(get_current_user)):
    _, token = auth
    if admin_client:
        try:
            admin_client.auth.admin.sign_out(token)
        except Exception:
            pass
    return Response(status_code=204)


@app.get(
    "/protected/profile",
    description="Read the verified user's own profile. Protected — requires a valid bearer token.",
)
def profile(auth=Depends(get_current_user)):
    user, _ = auth
    return {"id": user.id, "email": user.email, "created_at": str(user.created_at)}


@app.get(
    "/protected/dashboard",
    description="Second protected route — proves the auth dependency is reusable across endpoints.",
)
def dashboard(auth=Depends(get_current_user)):
    user, _ = auth
    return {"message": f"Welcome back, {user.email}", "id": user.id}