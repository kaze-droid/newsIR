from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    ALLOWED_HOSTS: list = ['*']
    INDEX_NAME: str = "articles_unprocessed"
    BI_ENCODER: str = "Kaze-droid/SENAN-Raw"
    ELASTIC_PASSWORD: str

settings = Settings()
