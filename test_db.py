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

os.environ["SUPABASE_URL"] = "https://jvvvzgejdojnnwmyuuau.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp2dnZ6Z2VqZG9qbm53bXl1dWF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAyMzA4MjYsImV4cCI6MjA5NTgwNjgyNn0.zbROytbmR00yPgl90St-uu7tVZ4bmC1ZopfXAF4jexI"

print(requests.get(get_url() + "?select=role,content&order=created_at.asc", headers=get_headers()).json())
