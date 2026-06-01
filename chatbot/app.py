import json
import requests
import os
from flask import Flask, render_template, request, jsonify
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

Just respond naturally to whatever the user says, given your confused, blank-slate state."""

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
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
        
    database.add_message("user", user_message)
    messages_history = database.get_all_messages()
    
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages.extend(messages_history)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": api_messages
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        ai_reply = result['choices'][0]['message']['content']
        database.add_message("assistant", ai_reply)
        return jsonify({"reply": ai_reply})
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": "Failed to get response from AI"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
