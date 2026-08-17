import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(
        "Warning: SUPABASE_URL or SUPABASE_KEY is not set. "
        "Auth routes will fail until you configure .env — see .env.example."
    )

supabase: Client = create_client(
    SUPABASE_URL or "https://placeholder.supabase.co",
    SUPABASE_KEY or "placeholder-key",
)