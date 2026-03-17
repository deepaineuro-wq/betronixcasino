import random
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import (
    games_menu_kb, coin_choice_kb, roulette_choice_kb,
    bet_amount_kb, back_to_games_kb, play_again_kb, back_to_menu_kb
)
from config import MIN_BET, MAX_BET

router = Router()


# =================== STATES ===================

class BetState(StatesGroup):
    waiting_for_bet = State()
    waiting_for_coin_choice = State()
    waiting_for_roulette_choice = State()
    waiting_for_mines_count = State()
    waiting_for_crash_cashout = State()


# =================== GAMES MENU ===================

@router.callback_query(F.data == "games")
async def games_menu(callback: CallbackQuery):
    text = (
        "🎮 <b>Выберите игру:</b>\n\n"
        "🎲 <b>Кости</b> — угадайте больше/меньше\n"
        "🪙 <b>Монетка</b> — орёл или решка\n"
        "🎰 <b>Слоты</b> — крутите барабаны\n"
        "🎡 <b>Рулетка</b> — красное/чёрное/зелёное\n"
        "🃏 <b>Блэкджек</b> — наберите 21\n"
        "💣 <b>Мины</b> — найдите алмазы\n"
        "📈 <b>Краш</b> — успейте забрать"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=games_menu_kb())
    await callback.answer()


# =================== UNIVERSAL BET INPUT ===================

async def ask_bet(callback: CallbackQuery, state: FSMContext, game_name: str, game_type: str, next_state: State = None):
    """Запрашиваем ставку для игры"""
    db = callback.message.bot.__dict__.get("workflow_data", {}).get("db")
    user_id = callback.from_user.id

    await state.update_data(game_type=game_type)

    balance = 0
    # Получаем db из middleware/workflow
    text = (
        f"🎮 <b>{game_name}</b>\n\n"
        f"💰 Введите сумму ставки или выберите:\n\n"
        f"Минимум: <b>{MIN_BET}₽</b>\n"
        f"Максимум: <b>{MAX_BET}₽</b>"
    )

    if next_state:
        await state.set_state(next_state)
    else:
        await state.set_state(BetState.waiting_for_bet)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=bet_amount_kb(game_type))
    await callback.answer()


# =================== DICE GAME 🎲 ===================

@router.callback_query(F.data == "game_dice")
async def game_dice_start(callback: CallbackQuery, state: FSMContext):
    await ask_bet(
    