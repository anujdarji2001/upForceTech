from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PostBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    is_public: bool = True

class PostCreate(PostBase):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)

class PostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None

class PostResponse(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

class LikeBase(BaseModel):
    post_id: int

class LikeResponse(LikeBase):
    id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

class PostWithLikes(PostResponse):
    likes: List[LikeResponse] = [] 