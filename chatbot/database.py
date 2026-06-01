import os
import requests

def get_headers():
    key = os.environ.get("SUPABASE_KEY")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def get_url():
    url = os.environ.get("SUPABASE_URL")
    if url and url.endswith('/'):
        url = url[:-1]
    return f"{url}/rest/v1/messages" if url else None

def add_message(role, content):
    url = get_url()
    if not url: return
    try:
        requests.post(url, headers=get_headers(), json={"role": role, "content": content})
    except Exception as e:
        print(f"Error saving to Supabase: {e}")

def get_all_messages():
    url = get_url()
    if not url: return []
    try:
        res = requests.get(f"{url}?select=role,content&order=created_at.asc", headers=get_headers())
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
    return []
