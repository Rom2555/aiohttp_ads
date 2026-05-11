import os
from datetime import datetime

from aiohttp import web
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


# Асинхронный движок
engine = create_async_engine(database_url, echo=False)
# Фабрика сессий
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Модель база данных
class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    owner = Column(String(100), nullable=False)


# Схемы Pydantic
class AdSchema(BaseModel):
    """Базовая схема валидации полей объявления."""
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=300)
    owner: str = Field(min_length=1, max_length=100)

    @field_validator('title', 'description', 'owner', mode='before')
    @classmethod
    def strip_ws(cls, v):
        """Обрезает пробелы по краям и запрещает строки, состоящие только из пробелов."""
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('Поле не может быть пустым или состоять из пробелов')
        return v

class AdCreate(AdSchema):
    """Схема для создания объявления"""
    pass

class AdUpdate(AdSchema):
    """Схема для обновления объявления"""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1, max_length=300)
    owner: str | None = Field(None, min_length=1, max_length=100)

class AdResponse(BaseModel):
    """Схема для ответа API"""
    id: int
    title: str
    description: str
    created_at: datetime | None
    owner: str


# Middleware
@web.middleware
async def db_middleware(request: web.Request, handler):
    """
    Middleware для управления сессией БД.
    Открывает сессию, передает её в request, коммит при успешном ответе, откат при ошибке.
    """
    async with async_session() as session:
        request['db'] = session
        try:
            resp = await handler(request)
            # Коммит если статус ответа успешный (2xx)
            if 200 <= resp.status < 300:
                await session.commit()
            return resp
        except web.HTTPException:
            # HTTP ошибки (400, 404)
            raise
        except Exception:
            # Все остальные ошибки - аварийное завершение, откат
            await session.rollback()
            raise

# Инициализация приложения и подключение middleware
app = web.Application()
app.middlewares.append(db_middleware)



# Обработчики роутов
async def health(request: web.Request) -> web.Response:
    """Проверка работоспособности сервера"""
    return web.json_response({"status": "ok"})

async def list_ads(request: web.Request) -> web.Response:
    """Возвращает список всех объявлений."""
    pass

async def create_ad(request: web.Request) -> web.Response:
    """Создает новое объявление."""
    pass

async def get_ad(request: web.Request) -> web.Response:
    """Возвращает данные одного объявления по ID."""
    pass

async def update_ad(request: web.Request) -> web.Response:
    """Обновляет данные существующего объявления."""
    pass

async def delete_ad(request: web.Request) -> web.Response:
    """Удаляет объявление по ID."""
    pass



# Регистрация маршрутов и запуск
app.router.add_get('/health', health)
app.router.add_get('/ads', list_ads)
app.router.add_post('/ads', create_ad)
app.router.add_get('/ads/{ad_id}', get_ad)
app.router.add_patch('/ads/{ad_id}', update_ad)
app.router.add_delete('/ads/{ad_id}', delete_ad)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)