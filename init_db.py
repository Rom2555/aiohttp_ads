import asyncio
from app import Base, engine

async def init():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Таблицы успешно созданы или уже существуют")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")

if __name__ == '__main__':
    asyncio.run(init())