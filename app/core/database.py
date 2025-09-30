"""
数据库连接和初始化模块
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# 数据库文件路径
DB_PATH = "visionmorph.db"

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
    return conn

@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """初始化数据库，创建所有表"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                avatar_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. 创建图片表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                width INTEGER,
                height INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 3. 创建生成效果图表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_image_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_image_id) REFERENCES images(id) ON DELETE CASCADE
            )
        """)
        
        # 4. 创建图片评价表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generated_image_id INTEGER UNIQUE NOT NULL,
                overall_score INTEGER CHECK (overall_score >= 1 AND overall_score <= 100),
                highlights TEXT,
                ai_comment TEXT,
                shooting_guidance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generated_image_id) REFERENCES generated_images(id) ON DELETE CASCADE
            )
        """)
        
        # 创建索引
        create_indexes(cursor)
        
        conn.commit()
        print("✅ 数据库初始化完成！")

def create_indexes(cursor):
    """创建数据库索引"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_images_user_id ON images(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_generated_images_original_id ON generated_images(original_image_id)",
        "CREATE INDEX IF NOT EXISTS idx_generated_images_created_at ON generated_images(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_image_evaluations_generated_id ON image_evaluations(generated_image_id)",
        "CREATE INDEX IF NOT EXISTS idx_image_evaluations_score ON image_evaluations(overall_score)",
        "CREATE INDEX IF NOT EXISTS idx_image_evaluations_created_at ON image_evaluations(created_at)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)

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
