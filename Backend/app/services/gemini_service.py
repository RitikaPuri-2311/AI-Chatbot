import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite")

# In-memory conversation store
# Key: session_id, Value: list of messages
conversation_store: dict = {}

def get_ai_response(session_id: str, user_message: str) -> str:
    # Get or create history for this session
    if session_id not in conversation_store:
        conversation_store[session_id] = []
    
    history = conversation_store[session_id]
    
    # Start chat with existing history
    chat = model.start_chat(history=history)
    
    # Send message and get response
    response = chat.send_message(user_message)
    ai_reply = response.text
    
    # Save both messages to history
    # Gemini uses "user" and "model" (not "assistant")
    conversation_store[session_id].append({
        "role": "user",
        "parts": [user_message]
    })
    conversation_store[session_id].append({
        "role": "model",
        "parts": [ai_reply]
    })
    
    # Keep only last 20 messages to avoid token limit
    if len(conversation_store[session_id]) > 20:
        conversation_store[session_id] = \
            conversation_store[session_id][-20:]
    
    return ai_reply

def get_session_history(session_id: str) -> list:
    history = conversation_store.get(session_id, [])
    # Convert Gemini format to frontend format
    messages = []
    for i, msg in enumerate(history):
        messages.append({
            "id": str(i),
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["parts"][0],
            "createdAt": ""
        })
    return messages