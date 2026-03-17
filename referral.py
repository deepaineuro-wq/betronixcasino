from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import referral_kb, back_to_menu_kb
from config import REFERRAL_BONUS, REFERRAL_BONUS_FRIEND

router = Router()


@router.callback_query(F.data == "referral")
async def referral_menu(callback: CallbackQuery, db, bot):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    referral_count = await db.get_referral_count(user_id)
    referral_earnings = await db.get_referral_earnings(user_id)

    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"Приглашайте друзей и получайте бонусы!\n\n"
        f"🎁 <b>Бонусы:</b>\n"
        f"• Вам: <b>{REFERRAL_BONUS}₽</b> за каждого друга\n"
        f"• Другу: <b>{REFERRAL_BONUS_FRIEND}₽</b> при регистрации\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 <b>Ваша статистика:</b>\n"
        f"👤 Приглашено друзей: <b>{referral_count}</b>\n"
        f"💰 Заработано: <b>{referral_earnings:.2f}₽</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=referral_kb(referral_link),
        disable_web_page_preview=True
    )
    await callback.answer()


@router.callback_query(F.data == "referral_share")
async def referral_share(callback: CallbackQuery, bot):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    share_text = (
        f"🎰 Играй в Casino Bot и выигрывай!\n\n"
        f"💰 Получи {REFERRAL_BONUS_FRIEND}₽ бонус при регистрации!\n\n"
        f"👉 {referral_link}"
    )

    await callback.answer(
        "📋 Ссылка скопирована! Отправьте её друзьям.",
        show_alert=True
    )

    # Отправляем сообщение для пересылки
    await callback.message.answer(
        f"📤 <b>Поделитесь с друзьями:</b>\n\n{share_text}",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "referral_stats")
async def referral_stats(callback: CallbackQuery, db):
    user_id = callback.from_user.id

    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Ошибка!", show_alert=True)
        return

    referral_count = user["referral_count"]
    referral_earnings = user["referral_earnings"]

    # Рассчитываем уровень
    if referral_count >= 50:
        level = "💎 Бриллиантовый"
        bonus_multiplier = "x2.0"
    elif referral_count >= 25:
        level = "🥇 Золотой"
        bonus_multiplier = "x1.5"
    elif referral_count >= 10:
        level = "🥈 Серебряный"
        bonus_multiplier = "x1.25"
    elif referral_count >= 5:
        level = "🥉 Бронзовый"
        bonus_multiplier = "x1.1"
    else:
        level = "⭐ Новичок"
        bonus_multiplier = "x1.0"

    next_levels = {
        "⭐ Новичок": f"До 🥉 Бронзового: {5 - referral_count} чел.",
        "🥉 Бронзовый": f"До 🥈 Серебряного: {10 - referral_count} чел.",
        "🥈 Серебряный": f"До 🥇 Золотого: {25 - referral_count} чел.",
        "🥇 Золотой": f"До 💎 Бриллиантового: {50 - referral_count} чел.",
        "💎 Бриллиантовый": "Максимальный уровень! 🎉"
    }

    text = (
        f"📊 <b>Детальная статистика рефералов</b>\n\n"
        f"👤 Приглашено: <b>{referral_count}</b>\n"
        f"💰 Заработано: <b>{referral_earnings:.2f}₽</b>\n\n"
        f"🏅 <b>Ваш уровень:</b> {level}\n"
        f"🔢 Множитель: <b>{bonus_multiplier}</b>\n\n"
        f"⏭ {next_levels[level]}\n\n"
        f"📈 <b>Уровни:</b>\n"
        f"⭐ Новичок (0-4) — x1.0\n"
        f"🥉 Бронзовый (5-9) — x1.1\n"
        f"🥈 Серебряный (10-24) — x1.25\n"
        f"🥇 Золотой (25-49) — x1.5\n"
        f"💎 Бриллиантовый (50+) — x2.0"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu_kb())
    await callback.answer()
    