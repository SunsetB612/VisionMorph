"""
用户认证业务逻辑
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.models import User
from .schemas import UserCreate, UserLogin, UserResponse, UserUpdate

def create_user(db: Session, user: UserCreate) -> UserResponse:
    """创建新用户"""
    # 检查邮箱是否已存在
    existing_user = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": user.email}
    ).fetchone()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    existing_username = db.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user.username}
    ).fetchone()
    
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被使用"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    
    result = db.execute(
        text("""
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (:username, :email, :password_hash, :created_at)
        """),
        {
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow()
        }
    )
    
    db.commit()
    
    # 获取新创建的用户
    new_user = db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": result.lastrowid}
    ).fetchone()
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        avatar_path=new_user.avatar_path,
        created_at=new_user.created_at
    )

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """验证用户登录"""
    user = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        avatar_path=user.avatar_path,
        created_at=user.created_at
    )

def login_user(db: Session, user_login: UserLogin) -> dict:
    """用户登录"""
    user = authenticate_user(db, user_login.email, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar_path=user.avatar_path,
            created_at=user.created_at
        )
    }

def get_user_by_id(db: Session, user_id: int) -> Optional[UserResponse]:
    """根据ID获取用户信息"""
    user = db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
    
    if not user:
        return None
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar_path=user.avatar_path,
        created_at=user.created_at
    )

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> UserResponse:
    """更新用户信息"""
    # 检查用户是否存在
    existing_user = db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
    
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 如果更新用户名，检查是否重复
    if user_update.username and user_update.username != existing_user.username:
        duplicate_username = db.execute(
            text("SELECT id FROM users WHERE username = :username AND id != :user_id"),
            {"username": user_update.username, "user_id": user_id}
        ).fetchone()
        
        if duplicate_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户名已被使用"
            )
    
    # 构建更新SQL
    update_fields = []
    update_values = {"user_id": user_id}
    
    if user_update.username is not None:
        update_fields.append("username = :username")
        update_values["username"] = user_update.username
    
    if user_update.avatar_path is not None:
        update_fields.append("avatar_path = :avatar_path")
        update_values["avatar_path"] = user_update.avatar_path
    
    if not update_fields:
        # 没有需要更新的字段
        return get_user_by_id(db, user_id)
    
    # 执行更新
    update_sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :user_id"
    db.execute(text(update_sql), update_values)
    db.commit()
    
    # 返回更新后的用户信息
    return get_user_by_id(db, user_id)

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    result = db.execute(
        text("DELETE FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    db.commit()
    return True
