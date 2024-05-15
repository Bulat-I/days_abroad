from aiogram.types import BotCommand

INITIAL_MENU_ITEMS = [
    BotCommand(command="start", description="Start"),
    BotCommand(command="cancel", description="Cancel"),
]

MENU_ITEMS = [
    BotCommand(command="en", description="Switch to English"),
    BotCommand(command="ru", description="Switch to Russian"),
    BotCommand(command="cancel", description="Cancel"),
]

MENU_ITEMS_ADMIN = [
    BotCommand(command="start", description="Back to user menu"),
    BotCommand(command="cancel", description="Cancel"),
]