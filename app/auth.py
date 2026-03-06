from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenData
import os
from dotenv import load_dotenv

load_dotenv()

# Secret key used to sign our JWT tokens — lives in .env, never in code
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-preventing-crash") # this key is not used inproduction
ALGORITHM = "HS256" #signing algo for JWT tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # token expires after 30 minutes

# Using bcrypt to hash the passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Tells FastAPI where to look for the token in incoming requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    #bcrypt has a 72 byte limit on passwords, so we're limiting to 72 char to prevent errors
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Checks if a plain text password matches the stored hash w/o decoding the hash!!
    # Truncate to match how we hashed it
    return pwd_context.verify(plain_password[:72], hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # So we don't modify the original
    to_encode = data.copy()

    # Expiry time defaults to 30 minutes if not specified
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    # Encoding everything into a signed JWT token string
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Checks the token is valid
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decoding the token and getting the username
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Looking up the user in the database based on the username in the token
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user