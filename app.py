import os
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram_i18n import I18nMiddleware
from dotenv import find_dotenv, load_dotenv
from aiogram.fsm.strategy import FSMStrategy
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores.gnu_text_core import GNUTextCore
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

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
BOT_TOKEN = os.getenv("TOKEN")
TEMP_DIR = os.getenv("TEMP_DIR")
I18N_BASE_DIR = os.path.join(Path.cwd(), "locales")
WEBHOOK_URL = os.getenv("API_URL")
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))


async def on_startup(bot: Bot) -> None:
    if DB_RECREATE_FLAG:
        await drop_db()
    await create_db()
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(bot: Bot) -> None:
    await bot.session.close()


def main() -> None:
    app = web.Application()
    bot = Bot(token=BOT_TOKEN)
    bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_CHAT)
    dp.include_routers(user_handlers_router, admin_handlers_router)
    i18n = I18nMiddleware(core=GNUTextCore(path=I18N_BASE_DIR), manager=i18n_middleware.UserManager(), default_locale="en")
    i18n.setup(dp)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    bot.set_my_commands(commands=INITIAL_MENU_ITEMS, scope=types.BotCommandScopeAllPrivateChats())
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/")
    setup_application(app, dp, bot=bot)
    
    try:
        web.run_app(app, host=HOST, port=PORT)
    except OSError as err:
        raise OSError(err.errno, f'error while attempting to bind on address {HOST}:{PORT}: {err.strerror.lower()}') from None


if __name__ == "__main__":
    logging.basicConfig(
        filename=os.path.join(TEMP_DIR, 'app.log'),  
        filemode='w',        
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  
        level=logging.WARNING  
    )
    
    main()