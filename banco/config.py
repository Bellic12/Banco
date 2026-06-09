from pydantic_settings import BaseSettings
from uuid import UUID


class Settings(BaseSettings):
    database_url: str
    airline_account_id: UUID
    insurer_account_id: UUID
    airline_callback_url: str

    model_config = {"env_file": ".env"}


settings = Settings()
