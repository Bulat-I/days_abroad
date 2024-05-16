from aiogram.types import BotCommand

INITIAL_MENU_ITEMS = [
    BotCommand(command="start", description="Start/Старт"),
    BotCommand(command="cancel", description="Cancel/Отмена"),
]

MENU_ITEMS = [
    BotCommand(command="en", description="Switch to English"),
    BotCommand(command="ru", description="Переключить на русский"),
    BotCommand(command="cancel", description="Cancel/Отмена"),
]

MENU_ITEMS_ADMIN = [
    BotCommand(command="start", description="Back to user menu"),
    BotCommand(command="cancel", description="Cancel/Отмена"),
]