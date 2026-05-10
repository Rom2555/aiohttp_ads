import os

from sqlalchemy import Column, Integer, String, Text, DateTime, func, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel, Field, field_validator, ValidationError

# Настройка подключения к PostgreSQL
database_url = os.environ.get("DATABASE_URL")
if database_url:
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "ads_db")
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

engine = create_async_engine(database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    owner = Column(String(100), nullable=False)


# --- Схемы Pydantic ---
class AdSchema(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=300)
    owner: str = Field(min_length=1, max_length=100)

    @field_validator('title', 'description', 'owner', mode='before')
    @classmethod
    def strip_ws(cls, v):
        if isinstance(v, str): v = v.strip()
        if not v: raise ValueError('Поле не может быть пустым или состоять из пробелов')
        return v