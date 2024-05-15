from aiogram_i18n.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_inline_callback_keyboard(*, buttons: dict[str, str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for button_text, data in buttons.items():
        keyboard.row(InlineKeyboardButton(text=button_text, callback_data=data))

    return keyboard.as_markup()


def build_dynamic_inline_keyboard(trip_buttons: dict, current_page: int, items_per_page: int) -> InlineKeyboardMarkup:
    start_index = (current_page - 1) * items_per_page
    end_index = min(start_index + items_per_page, len(trip_buttons))

    keyboard = InlineKeyboardBuilder()
    sliced_trip_buttons = dict(list(trip_buttons.items())[start_index:end_index])
    for button_text, callback_data in sliced_trip_buttons.items():
        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        keyboard.row(button)

    if len(trip_buttons) > end_index:
        next_button = InlineKeyboardButton(text="Next ➡️", callback_data="next_page")
        keyboard.row(next_button)
    if current_page > 1:
        prev_button = InlineKeyboardButton(text="⬅️ Prev", callback_data="prev_page")
        keyboard.row(prev_button)

    return keyboard.as_markup()
