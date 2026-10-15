from telegram import ReplyKeyboardMarkup

MENU_BUTTONS = ["🕐 Acum", "📅 Program azi", "⚙️ Schimbă grupa"]


def group_keyboard(groups: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[group] for group in groups], resize_keyboard=True, one_time_keyboard=True)


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([MENU_BUTTONS], resize_keyboard=True)
