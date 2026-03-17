import aiosqlite
import time
from typing import Optional

DB_PATH = "casino.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                balance REAL DEFAULT 0.0,
                total_deposited REAL DEFAULT 0.0,
                total_withdrawn REAL DEFAULT 0.0,
                total_wagered REAL DEFAULT 0.0,
                total_won REAL DEFAULT 0.0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                referrer_id INTEGER DEFAULT 0,
                referral_earnings REAL DEFAULT 0.0,
                referral_count INTEGER DEFAULT 0,
                registered_at INTEGER DEFAULT 0,
                last_active INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                currency TEXT DEFAULT 'USDT',
                status TEXT DEFAULT 'pending',
                invoice_id TEXT DEFAULT '',
                created_at INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_type TEXT,
                bet_amount REAL,
                result TEXT,
                win_amount REAL,
                created_at INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_user(user_id: int, username: str, first_name: str, referrer_id: int = 0):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users 
            (user_id, username, first_name, referrer_id, registered_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, referrer_id, now, now))

        if referrer_id > 0:
            await db.execute(
                "UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?",
                (referrer_id,)
            )
        await db.commit()


async def update_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ?, last_active = ? WHERE user_id = ?",
            (amount, int(time.time()), user_id)
        )
        await db.commit()


async def update_deposit_stats(user_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_deposited = total_deposited + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


async def update_withdraw_stats(user_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_withdrawn = total_withdrawn + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


async def update_game_stats(user_id: int, bet: float, win: float, won: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        games_won_inc = 1 if won else 0
        await db.execute("""
            UPDATE users SET 
                total_wagered = total_wagered + ?,
                total_won = total_won + ?,
                games_played = games_played + 1,
                games_won = games_won + ?,
                last_active = ?
            WHERE user_id = ?
        """, (bet, win, games_won_inc, int(time.time()), user_id))
        await db.commit()


async def add_referral_earnings(user_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET referral_earnings = referral_earnings + ?, balance = balance + ? WHERE user_id = ?",
            (amount, amount, user_id)
        )
        await db.commit()


async def add_transaction(user_id: int, tx_type: str, amount: float, currency: str = "USDT",
                          invoice_id: str = ""):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO transactions (user_id, type, amount, currency, status, invoice_id, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """, (user_id, tx_type, amount, currency, invoice_id, now))
        await db.commit()


async def update_transaction_status(invoice_id: str, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE transactions SET status = ? WHERE invoice_id = ?",
            (status, invoice_id)
        )
        await db.commit()


async def add_game_history(user_id: int, game_type: str, bet: float, result: str, win: float):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO game_history (user_id, game_type, bet_amount, result, win_amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, game_type, bet, result, win, now))
        await db.commit()


async def get_top_players(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY total_won DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(total_deposited),0) FROM users") as c:
            total_deposits = (await c.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(games_played),0) FROM users") as c:
            total_games = (await c.fetchone())[0]
        return {
            "total_users": total_users,
            "total_deposits": total_deposits,
            "total_games": total_games
        }
        