import asyncio
import logging
import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import CRYPTO_BOT_TOKEN
from keyboards.inline import back_to_menu_kb, deposit_amounts_kb, withdraw_kb

try:
    from aiocryptopay import AioCryptoPay, Networks
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)

router = Router()

# Инициализация CryptoBot API
crypto = None
if CRYPTO_AVAILABLE and CRYPTO_BOT_TOKEN and CRYPTO_BOT_TOKEN != "YOUR_CRYPTOBOT_TOKEN_HERE":
    crypto = AioCryptoPay(
        token=CRYPTO_BOT_TOKEN,
        network=Networks.MAIN_NET  # Для тестов: Networks.TEST_NET
    )


class DepositState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment = State()


class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_address = State()
    waiting_for_confirm = State()


# =================== КОШЕЛЁК ===================

@router.callback_query(F.data == "wallet")
async def wallet_menu(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    balance = await db.get_balance(user_id)

    text = (
        f"💳 <b>Кошелёк</b>\n\n"
        f"💰 Баланс: <b>{balance:.2f}₽</b>\n\n"
        f"Выберите действие:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Пополнить", callback_data="deposit"),
            InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw")
        ],
        [InlineKeyboardButton(text="📜 История транзакций", callback_data="tx_history")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


# =================== ПОПОЛНЕНИЕ ===================

@router.callback_query(F.data == "deposit")
async def deposit_start(callback: CallbackQuery, state: FSMContext):
    if not CRYPTO_AVAILABLE or not crypto:
        await callback.answer(
            "❌ Платёжная система временно недоступна!",
            show_alert=True
        )
        return

    text = (
        "📥 <b>Пополнение баланса (USDT)</b>\n\n"
        "💵 Курс: <b>1 USDT = 100₽</b>\n\n"
        "Выберите сумму пополнения или введите свою (в рублях):\n\n"
        "⚡ Минимум: <b>100₽</b> (1 USDT)\n"
        "⚡ Максимум: <b>1 000 000₽</b> (10 000 USDT)"
    )

    await state.set_state(DepositState.waiting_for_amount)
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=deposit_amounts_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dep_"), DepositState.waiting_for_amount)
async def deposit_preset_amount(callback: CallbackQuery, state: FSMContext, db, bot):
    amount_str = callback.data.split("_")[1]
    amount_rub = float(amount_str)
    await process_deposit(callback, state, db, bot, amount_rub)


@router.message(DepositState.waiting_for_amount)
async def deposit_custom_amount(message: Message, state: FSMContext, db, bot):
    try:
        amount_rub = float(message.text.replace(",", ".").strip())
    except ValueError:
        await message.answer(
            "❌ Введите корректную сумму числом!",
            reply_markup=back_to_menu_kb()
        )
        return

    if amount_rub < 100:
        await message.answer("❌ Минимальная сумма: <b>100₽</b>", parse_mode="HTML")
        return
    if amount_rub > 1000000:
        await message.answer("❌ Максимальная сумма: <b>1 000 000₽</b>", parse_mode="HTML")
        return

    # Создаём "фейковый" callback для унификации
    await process_deposit_msg(message, state, db, bot, amount_rub)


async def process_deposit(callback: CallbackQuery, state: FSMContext, db, bot, amount_rub: float):
    """Создаём инвойс CryptoBot для пополнения"""
    user_id = callback.from_user.id
    amount_usdt = round(amount_rub / 100, 2)  # Курс 1 USDT = 100₽

    try:
        # Создаём инвойс в CryptoBot
        invoice = await crypto.create_invoice(
            asset="USDT",
            amount=amount_usdt,
            description=f"Пополнение Casino Bot — {amount_rub}₽",
            hidden_message="✅ Оплата получена! Баланс пополнен.",
            paid_btn_name="callback",
            paid_btn_url=f"https://t.me/{(await bot.get_me()).username}",
            payload=f"{user_id}:{amount_rub}",
            expires_in=3600  # 1 час
        )

        # Сохраняем в БД
        await db.add_payment(user_id, amount_rub, str(invoice.invoice_id))

        await state.update_data(invoice_id=invoice.invoice_id, amount_rub=amount_rub)
        await state.set_state(DepositState.waiting_for_payment)

        pay_url = invoice.pay_url

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить через CryptoBot", url=pay_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{invoice.invoice_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_deposit")]
        ])

        text = (
            f"📥 <b>Счёт на оплату</b>\n\n"
            f"💵 Сумма: <b>{amount_usdt} USDT</b> ({amount_rub:.2f}₽)\n"
            f"🆔 Инвойс: <code>{invoice.invoice_id}</code>\n\n"
            f"⏰ Счёт действителен <b>1 час</b>\n\n"
            f"1️⃣ Нажмите «Оплатить через CryptoBot»\n"
            f"2️⃣ Оплатите в @CryptoBot\n"
            f"3️⃣ Вернитесь и нажмите «Проверить оплату»"
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка создания инвойса: {e}")
        await callback.answer("❌ Ошибка создания платежа. Попробуйте позже.", show_alert=True)
        await state.clear()


async def process_deposit_msg(message: Message, state: FSMContext, db, bot, amount_rub: float):
    """Создаём инвойс CryptoBot для пополнения (из сообщения)"""
    user_id = message.from_user.id
    amount_usdt = round(amount_rub / 100, 2)

    try:
        invoice = await crypto.create_invoice(
            asset="USDT",
            amount=amount_usdt,
            description=f"Пополнение Casino Bot — {amount_rub}₽",
            hidden_message="✅ Оплата получена! Баланс пополнен.",
            paid_btn_name="callback",
            paid_btn_url=f"https://t.me/{(await bot.get_me()).username}",
            payload=f"{user_id}:{amount_rub}",
            expires_in=3600
        )

        await db.add_payment(user_id, amount_rub, str(invoice.invoice_id))

        await state.update_data(invoice_id=invoice.invoice_id, amount_rub=amount_rub)
        await state.set_state(DepositState.waiting_for_payment)

        pay_url = invoice.pay_url

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить через CryptoBot", url=pay_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{invoice.invoice_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_deposit")]
        ])

        text = (
            f"📥 <b>Счёт на оплату</b>\n\n"
            f"💵 Сумма: <b>{amount_usdt} USDT</b> ({amount_rub:.2f}₽)\n"
            f"🆔 Инвойс: <code>{invoice.invoice_id}</code>\n\n"
            f"⏰ Счёт действителен <b>1 час</b>\n\n"
            f"1️⃣ Нажмите «Оплатить через CryptoBot»\n"
            f"2️⃣ Оплатите в @CryptoBot\n"
            f"3️⃣ Вернитесь и нажмите «Проверить оплату»"
        )

        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка создания инвойса: {e}")
        await message.answer("❌ Ошибка создания платежа. Попробуйте позже.")
        await state.clear()


# =================== ПРОВЕРКА ОПЛАТЫ ===================

@router.callback_query(F.data.startswith("check_pay_"))
async def check_payment(callback: CallbackQuery, state: FSMContext, db, bot):
    invoice_id_str = callback.data.replace("check_pay_", "")

    try:
        invoice_id = int(invoice_id_str)
    except ValueError:
        await callback.answer("❌ Ошибка проверки!", show_alert=True)
        return

    try:
        # Проверяем статус инвойса в CryptoBot
        invoices = await crypto.get_invoices(invoice_ids=[invoice_id])

        if not invoices:
            await callback.answer("❌ Инвойс не найден!", show_alert=True)
            return

        invoice = invoices[0]

        if invoice.status == "paid":
            # Подтверждаем оплату в БД
            user_id, amount = await db.confirm_payment(str(invoice_id))

            if user_id:
                await db.add_transaction(
                    user_id, amount, "deposit",
                    f"Пополнение через CryptoBot ({round(amount / 100, 2)} USDT)"
                )

                balance = await db.get_balance(user_id)

                text = (
                    f"✅ <b>Оплата подтверждена!</b>\n\n"
                    f"💵 Зачислено: <b>{amount:.2f}₽</b>\n"
                    f"💰 Текущий баланс: <b>{balance:.2f}₽</b>\n\n"
                    f"🎮 Удачи в играх!"
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎮 Играть", callback_data="games")],
                    [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")]
                ])

                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                await state.clear()
            else:
                await callback.answer("ℹ️ Платёж уже был обработан!", show_alert=True)
                await state.clear()

        elif invoice.status == "expired":
            await callback.answer("⏰ Счёт истёк! Создайте новый.", show_alert=True)
            await state.clear()

        else:
            await callback.answer(
                "⏳ Оплата ещё не поступила.\nОплатите и нажмите «Проверить» снова.",
                show_alert=True
            )

    except Exception as e:
        logger.error(f"Ошибка проверки оплаты: {e}")
        await callback.answer("❌ Ошибка проверки. Попробуйте позже.", show_alert=True)


# =================== ОТМЕНА ПОПОЛНЕНИЯ ===================

@router.callback_query(F.data == "cancel_deposit")
async def cancel_deposit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Пополнение отменено</b>",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb()
    )
    await callback.answer()


# =================== ВЫВОД СРЕДСТВ ===================

@router.callback_query(F.data == "withdraw")
async def withdraw_start(callback: CallbackQuery, state: FSMContext, db):
    user_id = callback.from_user.id
    balance = await db.get_balance(user_id)

    min_withdraw = 500  # Минимальный вывод в рублях

    if balance < min_withdraw:
        await callback.answer(
            f"❌ Минимальная сумма вывода: {min_withdraw}₽\n"
            f"Ваш баланс: {balance:.2f}₽",
            show_alert=True
        )
        return

    text = (
        f"📤 <b>Вывод средств (USDT)</b>\n\n"
        f"💰 Ваш баланс: <b>{balance:.2f}₽</b>\n"
        f"💵 Курс: <b>1 USDT = 100₽</b>\n\n"
        f"⚡ Минимум: <b>{min_withdraw}₽</b> ({min_withdraw / 100} USDT)\n\n"
        f"Введите сумму вывода в рублях:"
    )

    await state.set_state(WithdrawState.waiting_for_amount)
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=withdraw_kb(balance)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wd_"), WithdrawState.waiting_for_amount)
async def withdraw_preset(callback: CallbackQuery, state: FSMContext, db_
