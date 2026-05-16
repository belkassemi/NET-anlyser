from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./netanalyzer.db"
    # Example for MySQL: "mysql+pymysql://user:password@localhost:3306/netanalyzer"
    # DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/netanalyzer"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production-secret-key-32chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    INTERNAL_API_KEY: str = "internal-capture-service-key"
    FIRST_ADMIN_EMAIL: str = "admin@netanalyzer.local"
    FIRST_ADMIN_PASSWORD: str = "Admin@123"

    class Config:
        env_file = ".env"


settings = Settings()
