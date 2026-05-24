"""应用配置"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./qms.db",
    )

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")
    )

    # 应用
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "52428800"))  # 50MB

    # 分页
    PAGE_SIZE: int = 20


settings = Settings()
