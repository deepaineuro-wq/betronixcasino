import aiohttp
from config import CRYPTOPAY_TOKEN, CRYPTOPAY_API_URL


class CryptoPay:
    def __init__(self):
        self.token = CRYPTOPAY_TOKEN
        self.base_url = CRYPTOPAY_API_URL
        self.headers = {"Crypto-Pay-API-Token": self.token}

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, **kwargs) as resp:
                data = await resp.json()
                return data

    async def create_invoice(self, amount: float, currency: str = "USDT",
                             description: str = "", payload: str = "") -> dict:
        """Создать счёт на оплату"""
        params = {
            "currency_type": "crypto",
            "asset": currency,
            "amount": str(amount),
            "description": description,
            "payload": payload,
            "expires_in": 3600
        }
        result = await self._request("POST", "createInvoice", json=params)
        return result.get("result", {})

    async def get_invoices(self, invoice_ids: str = "", status: str = "") -> list:
        """Получить список счетов"""
        params = {}
        if invoice_ids:
            params["invoice_ids"] = invoice_ids
        if status:
            params["status"] = status
        result = await self._request("GET", "getInvoices", params=params)
        return result.get("result", {}).get("items", [])

    async def create_check(self, amount: float, asset: str = "USDT") -> dict:
        """Создать чек для вывода"""
        params = {
            "asset": asset,
            "amount": str(amount)
        }
        result = await self._request("POST", "createCheck", json=params)
        return result.get("result", {})

    async def transfer(self, user_id: int, amount: float, asset: str = "USDT") -> dict:
        """Перевод пользователю"""
        params = {
            "user_id": user_id,
            "asset": asset,
            "amount": str(amount),
            "spend_id": f"withdraw_{user_id}_{amount}"
        }
        result = await self._request("POST", "transfer", json=params)
        return result

    async def get_balance(self) -> list:
        """Баланс бота в CryptoBot"""
        result = await self._request("GET", "getBalance")
        return result.get("result", [])


crypto_pay = CryptoPay()
