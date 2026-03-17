import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.db import Database
from handlers import games, payment, referral, start

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()


async def main():
    # Инициализация базы данных
    await db.create_tables()

    # Передаём db во все роутеры через workflow_data
    dp.workflow_data["db"] = db
    dp.workflow_data["bot"] = bot

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(games.router)
    dp.include_router(payment.router)
    dp.include_router(referral.router)

    # Удаляем вебхук и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    