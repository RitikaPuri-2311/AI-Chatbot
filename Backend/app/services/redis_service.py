import redis
import json
from app.config import settings

# Connect to Redis
try:
    r = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        protocol=2  # ← add this — disables HELLO command
    )
    r.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis connected")
except Exception as e:
    REDIS_AVAILABLE = False
    print(f"⚠️ Redis unavailable: {e} — falling back to DB")

SLIDING_WINDOW = 20

def is_available() -> bool:
    try:
        r.ping()
        return True
    except:
        return False

def _key(session_id: str) -> str:
    """Redis key format: chat:session_id"""
    return f"chat:{session_id}"

def get_history(session_id: str) -> list:
    """
    Get conversation history from Redis.
    Returns list of {role, parts} dicts in Gemini format.
    Returns empty list if Redis unavailable or key not found.
    """
    if not is_available():
        return []
    try:
        data = r.get(_key(session_id))
        if data:
            return json.loads(data)
        return []
    except Exception as e:
        print(f"Redis get error: {e}")
        return []

def set_history(session_id: str, history: list) -> bool:
    """
    Save conversation history to Redis.
    Applies sliding window of 20 messages.
    Sets TTL so history auto-expires after 24 hours.
    Returns True if saved, False if Redis unavailable.
    """
    if not is_available():
        return False
    try:
        # Apply sliding window
        if len(history) > SLIDING_WINDOW:
            history = history[-SLIDING_WINDOW:]

        r.setex(
            _key(session_id),
            settings.REDIS_TTL,
            json.dumps(history)
        )
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False

def append_messages(
    session_id: str,
    user_message: str,
    ai_reply: str
) -> bool:
    """
    Append a user + AI message pair to Redis history.
    More efficient than get + set for single appends.
    """
    history = get_history(session_id)

    history.append({
        "role": "user",
        "parts": [user_message]
    })
    history.append({
        "role": "model",
        "parts": [ai_reply]
    })

    return set_history(session_id, history)

def delete_session(session_id: str) -> bool:
    """Delete session history from Redis when session deleted"""
    if not is_available():
        return False
    try:
        r.delete(_key(session_id))
        return True
    except Exception as e:
        print(f"Redis delete error: {e}")
        return False

def get_all_sessions(user_id: str) -> list:
    """
    Get all session keys for a user.
    Useful for debugging — not used in main flow.
    """
    if not is_available():
        return []
    try:
        pattern = f"chat:{user_id}_*"
        keys = r.keys(pattern)
        return [k.replace("chat:", "") for k in keys]
    except Exception as e:
        print(f"Redis keys error: {e}")
        return []