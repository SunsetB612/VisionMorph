"""
用户认证相关的Pydantic模型
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr

class UserCreate(UserBase):
    """用户注册模型"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名长度至少3位')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    avatar_path: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: Optional[int] = None

class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = None
    avatar_path: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('用户名长度至少3位')
            if not v.isalnum():
                raise ValueError('用户名只能包含字母和数字')
        return v
