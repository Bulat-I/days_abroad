import asyncio
import os
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram_i18n import I18nMiddleware
from dotenv import find_dotenv, load_dotenv
from aiogram.fsm.strategy import FSMStrategy
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores.gnu_text_core import GNUTextCore

from common.bot_commands import INITIAL_MENU_ITEMS

from handlers.user_handlers import user_handlers_router
from handlers.admin_handlers import admin_handlers_router
from middlewares.database import DataBaseSession
from middlewares import i18n_middleware

load_dotenv(find_dotenv())
from database.engine import create_db, drop_db
from database.engine import session_maker

ALLOWED_UPDATES = ["message, inline_query"]
DB_RECREATE_FLAG = False

I18N_BASE_DIR = os.path.join(Path.cwd(), "locales")

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_CHAT)
dp.include_routers(user_handlers_router, admin_handlers_router)

i18n = I18nMiddleware(
        core=GNUTextCore(
            path=I18N_BASE_DIR,
        ),
        manager=i18n_middleware.UserManager(),
        default_locale="en"
    )

i18n.setup(dp)


async def on_startup(bot):
    if DB_RECREATE_FLAG:
        await drop_db()
    
    await create_db()


async def on_shutdown(bot):
    ...


async def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=INITIAL_MENU_ITEMS, scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


if __name__ == "__main__":
    asyncio.run(main())