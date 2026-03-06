from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr # Pydantic's built-in email validation
    password: str 


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True # Tells Pydantic to read data from SQLAlchemy models


class UserLogin(BaseModel):
    username: str
    password: str

# What's sent back after a successful login
class Token(BaseModel):
    access_token: str
    token_type: str

# JWT token: endoded data that includes the username and an expiration time
class TokenData(BaseModel):
    username: Optional[str] = None