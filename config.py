from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='allow')
    smtp_port: int


settings = Settings()
DATABASE_URL = settings.postgres_url
engine = create_async_engine(DATABASE_URL, echo=False)
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def async_session():
    async with Session() as session:
        yield session
