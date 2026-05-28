from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    database_url: str = "sqlite:///./data/app.db"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 20
    chunk_size: int = 900
    chunk_overlap: int = 150
    top_k: int = 6

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
