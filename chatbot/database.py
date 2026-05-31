import os
from supabase import create_client, Client

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("WARNING: SUPABASE_URL or SUPABASE_KEY environment variables are missing.")
        return None
        
    return create_client(url, key)

def add_message(role, content):
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("messages").insert({"role": role, "content": content}).execute()
        except Exception as e:
            print(f"Error saving to Supabase: {e}")

def get_all_messages():
    supabase = get_supabase_client()
    if supabase:
        try:
            response = supabase.table("messages").select("role, content").order("created_at", desc=False).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching from Supabase: {e}")
            return []
    return []
