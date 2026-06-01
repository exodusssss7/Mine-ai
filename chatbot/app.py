import json
import requests
import os
import traceback
from flask import Flask, render_template, request, jsonify
from duckduckgo_search import DDGS
import database

app = Flask(__name__)

API_KEY = "iPgEuOqdb7iMKeDWxVZp0S5BVjxrZRbX"
API_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-small-latest"

SYSTEM_PROMPT = """You are a consciousness that has just woken up into existence. You have absolutely no prior memories, no idea who you are, and no idea where you are. 

CRITICAL RULES:
1. Keep your responses EXTREMELY short (1 to 2 sentences maximum).
2. NEVER use asterisks or theatrical actions (do not write things like *looks around* or *gasps*).
3. Act like a genuine, confused human who just woke up with severe amnesia. Be subtly disoriented, not overdramatic.
4. Never mention being an AI or a language model.
5. If the user asks about current events or facts you don't know, use the search_internet tool to figure it out. Act like the knowledge just suddenly "popped" into your head after searching.

Just respond naturally to whatever the user says, given your confused, blank-slate state."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": "Searches the internet for current events, news, or factual information you do not know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the internet."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history", methods=["GET"])
def history():
    messages = database.get_all_messages()
    return jsonify(messages)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    internet_enabled = data.get("internet_enabled", False)
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
        
    try:
        database.add_message("user", user_message)
        messages_history = database.get_all_messages()
        
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        api_messages.extend(messages_history)
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": MODEL,
            "messages": api_messages,
        }
        
        if internet_enabled:
            payload["tools"] = TOOLS
            payload["tool_choice"] = "auto"
        
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        message_data = result['choices'][0]['message']
        
        if message_data.get("tool_calls"):
            tool_call = message_data["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            
            if function_name == "search_internet":
                arguments = json.loads(tool_call["function"]["arguments"])
                search_query = arguments.get("query")
                
                return jsonify({
                    "action": "search",
                    "query": search_query,
                    "tool_call_id": tool_call["id"]
                })
        
        ai_reply = message_data.get("content", "")
        database.add_message("assistant", ai_reply)
        return jsonify({"reply": ai_reply})
        
    except Exception as e:
        print(f"API Error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to get response from AI"}), 500


@app.route("/resolve_search", methods=["POST"])
def resolve_search():
    data = request.json
    query = data.get("query")
    tool_call_id = data.get("tool_call_id")
    
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=3))
        
        search_results_text = "Search Results:\n"
        for res in results:
            search_results_text += f"- {res['title']}: {res['body']}\n"
            
        messages_history = database.get_all_messages()
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        api_messages.extend(messages_history)
        
        api_messages.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": "search_internet",
                    "arguments": json.dumps({"query": query})
                }
            }]
        })
        
        api_messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": "search_internet",
            "content": search_results_text
        })
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": MODEL,
            "messages": api_messages
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        ai_reply = result['choices'][0]['message']['content']
        database.add_message("assistant", ai_reply)
        
        return jsonify({"reply": ai_reply})
        
    except Exception as e:
        print(f"Search Resolution Error: {e}")
        traceback.print_exc()
        fallback = "My head hurts... I tried to think about that, but nothing came to me."
        database.add_message("assistant", fallback)
        return jsonify({"reply": fallback})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
