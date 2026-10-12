import os


class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")


settings = Settings()
