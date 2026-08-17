import os
from typing import Optional, Tuple

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from supabase_client import SUPABASE_URL, supabase

SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

admin_client = None
if SUPABASE_URL and SERVICE_ROLE_KEY:
    from supabase import create_client

    admin_client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Tuple[object, str]:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Access token required")

    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
        user = response.user if response else None
    except Exception:
        user = None

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user, token