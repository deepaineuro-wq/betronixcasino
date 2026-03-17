from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎲 Кубики", callback_data="game_dice"),
        InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        InlineKeyboardButton(text="💰 Кошелёк", callback_data="wallet")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Рефералы", callback_data="referral"),
        InlineKeyboardButton(text="🏆 Топ игроков", callback_data="top_players")
    )
    builder.row(
        InlineKeyboardButton(text="📖 Правила", callback_data="rules")
    )
    return builder.as_markup()


def wallet_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Пополнить", callback_data="deposit"),
        InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def deposit_amounts_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    amounts = [1, 5, 10, 25, 50, 100]
    for i in range(0, len(amounts), 3):
        row_buttons = []
        for amt in amounts[i:i + 3]:
            row_buttons.append(
                InlineKeyboardButton(text=f"💵 {amt} USDT", callback_data=f"dep_{amt}")
            )
        builder.row(*row_buttons)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="wallet"))
    return builder.as_markup()


def bet_amounts_kb(game: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    bets = [0.5, 1, 2, 5, 10, 25]
    for i in range(0, len(bets), 3):
        row_buttons = []
        for bet in bets[i:i + 3]:
            label = f"{int(bet)}$" if bet == int(bet) else f"{bet}$"
            row_buttons.append(
                InlineKeyboardButton(text=f"🎯 {label}", callback_data=f"bet_{game}_{bet}")
            )
        builder.row(*row_buttons)
    builder.row(InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu"))
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def play_again_kb(game: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Играть снова", callback_data=f"game_{game}"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    return builder.as_markup()


def check_payment_kb(invoice_id: str, pay_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Оплатить", url=pay_url)
    )
    builder.row(
        InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_pay_{invoice_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="wallet")
    )
    return builder.as_markup()


def confirm_withdraw_kb(amount: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_wd_{amount}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="wallet")
    )
    return builder.as_markup()
    