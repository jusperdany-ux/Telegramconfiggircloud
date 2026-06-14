import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp

# ========= TOKEN از Environment =========
BOT_TOKEN = os.getenv("8807849202:AAFks5IhzGUj_0Ee_jgQIvx_nWPVW4U_hWE")

BASE_URL = "https://api.cloudflare.com/client/v4"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_state = {}
user_api = {}

# ========= Cloudflare =========
async def get_zones(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/zones", headers=headers) as r:
            return await r.json()

async def create_dns(api_key, zone_id, name, ip):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "A",
        "name": name,
        "content": ip,
        "ttl": 120,
        "proxied": False
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/zones/{zone_id}/dns_records",
            headers=headers,
            json=data
        ) as r:
            return await r.json()

# ========= Telegram Bot =========

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 API Key کلادفلر رو بفرست:")
    user_state[message.from_user.id] = "api"

@dp.message(Command("domains"))
async def domains(message: types.Message):
    api = user_api.get(message.from_user.id)

    if not api:
        await message.answer("❌ اول API Key بده")
        return

    data = await get_zones(api)

    if not data.get("success"):
        await message.answer("❌ API Key اشتباهه")
        return

    msg = "🌐 دامنه‌ها:\n\n"
    for z in data["result"]:
        msg += f"{z['name']}\nID: {z['id']}\n\n"

    await message.answer(msg)

@dp.message()
async def all_messages(message: types.Message):
    uid = message.from_user.id
    text = message.text

    if user_state.get(uid) == "api":
        user_api[uid] = text
        user_state[uid] = None
        await message.answer("✅ ذخیره شد\n/domains بزن")
        return

    if text.startswith("/send"):
        try:
            _, zone_id, sub, ip = text.split()
            api = user_api.get(uid)

            if not api:
                await message.answer("❌ API Key ندارید")
                return

            res = await create_dns(api, zone_id, sub, ip)

            if res.get("success"):
                await message.answer("✅ DNS ساخته شد")
            else:
                await message.answer("❌ خطا در Cloudflare")
        except:
            await message.answer("❌ فرمت:\n/send zone_id sub ip")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())