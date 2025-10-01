"""
数据库连接和初始化模块
"""
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # 设置为True可以看到SQL语句
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,   # 连接回收时间
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_connection():
    """获取数据库连接"""
    return engine.connect()

@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def init_database():
    """初始化数据库，创建所有表"""
    try:
        with get_db_connection() as conn:
            # 1. 创建用户表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    avatar_path VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # 2. 创建图片表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size INT NOT NULL,
                    mime_type VARCHAR(100) NOT NULL,
                    width INT,
                    height INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # 3. 创建生成效果图表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS generated_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    original_image_id INT NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_image_id) REFERENCES images(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # 4. 创建图片评价表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS image_evaluations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    generated_image_id INT UNIQUE NOT NULL,
                    overall_score INT CHECK (overall_score >= 1 AND overall_score <= 100),
                    highlights TEXT,
                    ai_comment TEXT,
                    shooting_guidance TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (generated_image_id) REFERENCES generated_images(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # 创建索引
            create_indexes(conn)
            
            print("✅ MySQL数据库初始化完成！")
            
    except SQLAlchemyError as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise

def create_indexes(conn):
    """创建数据库索引"""
    indexes = [
        ("idx_users_email", "users", "email"),
        ("idx_users_username", "users", "username"),
        ("idx_images_user_id", "images", "user_id"),
        ("idx_images_created_at", "images", "created_at"),
        ("idx_generated_images_original_id", "generated_images", "original_image_id"),
        ("idx_generated_images_created_at", "generated_images", "created_at"),
        ("idx_image_evaluations_generated_id", "image_evaluations", "generated_image_id"),
        ("idx_image_evaluations_score", "image_evaluations", "overall_score"),
        ("idx_image_evaluations_created_at", "image_evaluations", "created_at")
    ]
    
    for index_name, table_name, column_name in indexes:
        try:
            # 检查索引是否已存在
            check_sql = f"""
                SELECT COUNT(*) 
                FROM information_schema.statistics 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}' 
                AND index_name = '{index_name}'
            """
            result = conn.execute(text(check_sql)).fetchone()
            
            if result[0] == 0:
                # 索引不存在，创建索引
                create_sql = f"CREATE INDEX {index_name} ON {table_name}({column_name})"
                conn.execute(text(create_sql))
                print(f"✅ 创建索引: {index_name}")
            else:
                print(f"ℹ️ 索引已存在: {index_name}")
                
        except Exception as e:
            print(f"⚠️ 创建索引 {index_name} 时出错: {e}")
            # 继续执行其他索引的创建

def create_storage_directories():
    """创建存储目录"""
    directories = [
        "static/avatars",
        "static/original", 
        "static/results",
        "static/temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 创建目录: {directory}")

def setup_database():
    """完整的数据库设置"""
    print("🚀 开始初始化数据库...")
    
    # 创建存储目录
    create_storage_directories()
    
    # 初始化数据库
    init_database()
    
    print("🎉 数据库设置完成！")

if __name__ == "__main__":
    setup_database()
