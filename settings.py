from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import Field,SecretStr
class Settings(BaseSettings):
    MODEL_NAME:str
    API_KEY:SecretStr
    model_config=SettingsConfigDict(env_file=r'D:\WORKSPACE\agents\.env',env_file_encoding='utf-8')
settings=Settings()