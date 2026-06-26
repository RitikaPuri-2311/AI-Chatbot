from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.config import settings
from app.models.user import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(password: str) -> str:
    password = password.strip()[:72]
    # encode to bytes and check length
    encoded = password.encode('utf-8')[:72]
    return pwd_context.hash(encoded)

def verify_password(plain: str, hashed: str) -> bool:
    plain = plain.strip()
    encoded = plain.encode('utf-8')[:72]
    return pwd_context.verify(encoded, hashed)

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

async def register_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str
) -> User:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=email,
        username=username,
        hashed_password=hash_password(password),
        # Seed with default permissions
        permissions=["ai:chat", "ai:embed", "ai:search"]
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
    
async def login_user(
    db: AsyncSession,
    email: str,
    password: str
) -> User:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")
    if not verify_password(password, user.hashed_password):
        raise ValueError("Incorrect password")
    return user

async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> User:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()