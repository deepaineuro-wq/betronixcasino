import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject

from database import get_user, create_user, get_top_players
from keyboards import main_menu_kb, back_to_menu_kb

router = Router()

WELCOME_TEXT = """
╔══════════════════════════════╗
   🎰  <b>CRYPTO CASINO</b>  🎰
╚══════════════════════════════╝

🃏 Добро пожаловать, <b>{name}</b>!

🎲 <b>Доступные игры:</b>
├ 🎲 <b>Кубики</b> — угадай число!
└ 🎰 <b>Слоты</b> — крути барабаны!

💎 Пополняй через <b>CryptoBot</b>
💸 Моментальные выплаты
👥 Приглашай друзей — получай <b>10%</b>

▸ Жми кнопку и начинай! ◂
"""

PROFILE_TEXT = """
╔══════════════════════════════╗
     👤  <b>ПРОФИЛЬ ИГРОКА</b>
╚══════════════════════════════╝

🆔 <b>ID:</b> <code>{user_id}</code>
👤 <b>Имя:</b> {name}

💰 <b>Баланс:</b> {balance:.2f} USDT

📊 <b>Статистика:</b>
├ 🎮 Игр сыграно: <b>{games_played}</b>
├ 🏆 Побед: <b>{games_won}</b>
├ 📈 Процент побед: <b>{win_rate:.1f}%</b>
├ 💵 Поставлено: <b>{total_wagered:.2f}$</b>
└ 🤑 Выиграно: <b>{total_won:.2f}$</b>

💳 <b>Финансы:</b>
├ 📥 Депозиты: <b>{total_deposited:.2f}$</b>
├ 📤 Выводы: <b>{total_withdrawn:.2f}$</b>
└ 📊 Профит: <b>{profit:+.2f}$</b>

👥 <b>Рефералы:</b>
├ 👫 Приглашено: <b>{referral_count}</b>
└ 💎 Заработано: <b>{referral_earnings:.2f}$</b>

📅 Дата регистрации: <b>{reg_date}</b>
"""

RULES_TEXT = """
╔══════════════════════════════╗
     📖  <b>ПРАВИЛА КАЗИНО</b>
╚══════════════════════════════╝

🎲 <b>КУБИКИ (DICE)</b>
├ Бросаете кубик (1-6)
├ Выпало <b>1-3</b> → ❌ Проигрыш
├ Выпало <b>4-5</b> → ✅ Выигрыш <b>x1.5</b>
└ Выпало <b>6</b> → 🔥 Выигрыш <b>x2.5</b>

🎰 <b>СЛОТЫ (SLOTS)</b>
├ Крутите барабаны
├ <b>🍋🍋🍋</b> → ❌ Проигрыш
├ <b>2 совп*
