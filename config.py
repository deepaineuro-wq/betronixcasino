import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("8533035842:AAHr4My2B2et-Dylna7Rs4GymqwcmtPZp7E")
CRYPTOPAY_TOKEN = os.getenv("551271:AAWPQLmyVY5H6GS3bkks7bH3xjMTQzeyMWt")
ADMIN_ID = int(os.getenv("7987189183", 0))
BOT_USERNAME = os.getenv("BetronixCasinoBot", "")

# CryptoBot API (mainnet)
CRYPTOPAY_API_URL = "https://pay.crypt.bot/api"
# Для тестов: "https://testnet-pay.crypt.bot/api"

# Настройки казино
MIN_BET = 0.5          # Минимальная ставка в USD
MAX_BET = 100.0        # Максимальная ставка
MIN_DEPOSIT = 1.0      # Минимальный депозит
MIN_WITHDRAW = 5.0     # Минимальный вывод
HOUSE_EDGE = 0.05      # Преимущество казино 5%
REFERRAL_BONUS = 0.10  # 10% реферальный бонус от депозита
