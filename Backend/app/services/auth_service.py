from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12
)
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory user store — replace with DB tomorrow
fake_users_db: dict = {}

def hash_password(password: str) -> str:
    # Temporary — replace with bcrypt later
    return f"hashed_{password}"

def verify_password(plain: str, hashed: str) -> bool:
    return hashed == f"hashed_{plain}"
    
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def register_user(email: str, username: str, password: str) -> dict:
    if email in fake_users_db:
        raise ValueError("Email already registered")
    
    user = {
        "id": str(len(fake_users_db) + 1),
        "email": email,
        "username": username,
        "hashed_password": hash_password(password)
    }
    fake_users_db[email] = user
    return user

def login_user(email: str, password: str) -> dict:
    user = fake_users_db.get(email)
    if not user:
        raise ValueError("User not found")
    if not verify_password(password, user["hashed_password"]):
        raise ValueError("Incorrect password")
    return user

def get_user_by_email(email: str) -> dict:
    return fake_users_db.get(email)