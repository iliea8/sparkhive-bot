import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# تنظیمات
# ==========================================
BOT_TOKEN = "8654231613:AAHjwE7y8ha2AS2aP79C3kbrNf2S2hkymE4"
ADMIN_ID = 7473332530
BRAND_NAME = "SPARKHIVE"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# بخش دیتابیس
# ==========================================
import aiosqlite
DB_NAME = "sparkhive.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                credits INTEGER DEFAULT 0,
                avatar_level TEXT DEFAULT 'base',
                is_vip INTEGER DEFAULT 0,
                is_verified INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_submit TEXT,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS artworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_id TEXT,
                caption TEXT,
                status TEXT DEFAULT 'pending',
                published_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_user(user_id, username, first_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

async def add_credits(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def remove_credits(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET credits = credits - ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def update_avatar(user_id, level):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET avatar_level = ? WHERE user_id = ?", (level, user_id))
        await db.commit()

async def save_artwork(user_id, file_id, caption):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO artworks (user_id, file_id, caption) VALUES (?, ?, ?)",
            (user_id, file_id, caption)
        )
        await db.commit()

async def get_user_artworks(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM artworks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def get_pending_artworks():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM artworks WHERE status = 'pending' ORDER BY created_at ASC") as cursor:
            return await cursor.fetchall()

async def publish_artwork(artwork_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE artworks SET status = 'published', published_at = CURRENT_TIMESTAMP WHERE id = ?",
            (artwork_id,)
        )
        await db.commit()

# ==========================================
# بخش کیبوردها
# ==========================================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 ارسال نقاشی", callback_data="menu_submit")],
        [InlineKeyboardButton(text="👤 پروفایل", callback_data="menu_profile"),
         InlineKeyboardButton(text="💰 اعتبار", callback_data="menu_credits")],
        [InlineKeyboardButton(text="🖼️ گالری", callback_data="menu_gallery"),
         InlineKeyboardButton(text="✨ آواتار", callback_data="menu_avatar")],
        [InlineKeyboardButton(text="💎 اشتراک ویژه", callback_data="menu_vip")],
        [InlineKeyboardButton(text="❤️ حمایت مالی", callback_data="menu_support")]
    ])

def avatar_menu(current_level):
    buttons = []
    if current_level == "base":
        buttons.append([InlineKeyboardButton(text="🥈 آواتار نقره‌ای (۲۰۰ اعتبار)", callback_data="avatar_silver")])
        buttons.append([InlineKeyboardButton(text="🥇 آواتار طلایی (۵۰۰ اعتبار)", callback_data="avatar_gold")])
    elif current_level == "silver":
        buttons.append([InlineKeyboardButton(text="🥇 آواتار طلایی (۵۰۰ اعتبار)", callback_data="avatar_gold")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_review(artwork_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ انتشار", callback_data=f"approve_{artwork_id}")],
        [InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{artwork_id}")]
    ])

def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_main")]
    ])

# ==========================================
# دستورات
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await init_db()
    user = await get_user(message.from_user.id)
    if not user:
        await create_user(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.first_name or ""
        )
    await message.answer(
        f"سلام {message.from_user.first_name} عزیز! 👋\n\n"
        f"به کامیونیتی هنری **{BRAND_NAME}** خوش اومدی.\n\n"
        "اینجا می‌تونی:\n"
        "🎨 نقاشی‌هات رو بفرستی\n"
        "💰 با هر نقاشی اعتبار بگیری\n"
        "✨ آواتارت رو ارتقا بدی\n"
        "🖼️ گالری شخصی خودت رو بسازی\n"
        "🏆 و توی کانال دیده بشی\n\n"
        "از منوی زیر شروع کن:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message(Command("submit"))
async def cmd_submit(message: Message):
    await message.answer("🎨 نقاشی‌ت رو برام بفرست.\nمی‌تونی یه توضیح کوتاه هم همراهش بفرستی.\n\n⚠️ فقط عکس بفرست، نه فایل.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    caption = message.caption or ""
    await save_artwork(user_id, file_id, caption)
    await add_credits(user_id, 10)
    user = await get_user(user_id)
    new_credits = user["credits"] + 10
    await message.answer(
        f"✅ نقاشی‌ت با موفقیت ثبت شد!\n\n💰 **+۱۰ اعتبار** به حسابت اضافه شد.\n💎 اعتبار کل: **{new_credits}**\n\nنقاشی‌ت برای بررسی ارسال شد.",
        parse_mode="Markdown", reply_markup=back_button()
    )
    try:
        await bot.send_photo(ADMIN_ID, file_id, caption=f"🎨 نقاشی جدید از {message.from_user.full_name}\n🆔 @{message.from_user.username or 'ندارد'}\n📝 توضیح: {caption or 'ندارد'}\n\nبرای بررسی: /admin")
    except:
        pass

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user: return await message.answer("اول /start رو بزن.")
    avatar_emoji = {"base": "⚪", "silver": "🥈", "gold": "🥇"}.get(user["avatar_level"], "⚪")
    await message.answer(
        f"{avatar_emoji} **پروفایل هنری {user['first_name']}**\n\n🆔 آیدی: `{user['user_id']}`\n💰 اعتبار: **{user['credits']}**\n✨ سطح آواتار:**{user['avatar_level']}**",
        parse_mode="Markdown", reply_markup=back_button()
    )

@dp.message(Command("credits"))
async def cmd_credits(message: Message):
    user = await get_user(message.from_user.id)
    if not user: return await message.answer("اول /start رو بزن.")
    await message.answer(f"💰 **اعتبار تو: {user['credits']}**\n\nراه‌های کسب: +۱۰ ارسال، +۵۰ انتشار", parse_mode="Markdown", reply_markup=back_button())

@dp.message(Command("avatar"))
async def cmd_avatar(message: Message):
    user = await get_user(message.from_user.id)
    if not user: return await message.answer("اول /start رو بزن.")
    await message.answer(f"✨ **آواتار فعلی تو: {user['avatar_level']}**\n\nآواتارها رو با اعتبار باز کن:", parse_mode="Markdown", reply_markup=avatar_menu(user["avatar_level"]))

@dp.message(Command("gallery"))
async def cmd_gallery(message: Message):
    artworks = await get_user_artworks(message.from_user.id)
    if not artworks: return await message.answer("🖼️ گالری تو خالیه.\n\nبا /submit اولین نقاشی‌ت رو بفرست!", reply_markup=back_button())
    await message.answer(f"🖼️ **گالری تو: {len(artworks)} اثر**", parse_mode="Markdown")
    for art in artworks[:5]:
        await bot.send_photo(message.from_user.id, art["file_id"], caption=f"وضعیت: {art['status']}")

@dp.message(Command("vip"))
async def cmd_vip(message: Message):
    await message.answer(f"💎 **اشتراک ویژه {BRAND_NAME}**\n\n✅ آواتار طلایی\n✅ گالری نامحدود\n💰 قیمت: به زودی", parse_mode="Markdown", reply_markup=back_button())

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID: return await message.answer("⛔ تو ادمین نیستی.")
    pending = await get_pending_artworks()
    if not pending: return await message.answer("🎉 هیچ نقاشی در انتظار نیست.")
    for art in pending[:10]:
        user = await get_user(art["user_id"])
        await bot.send_photo(ADMIN_ID, art["file_id"], caption=f"🆔 #{art['id']}\n👤 {user['first_name'] if user else 'ناشناس'}", reply_markup=admin_review(art["id"]))

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("📖 راهنما:\n/start\n/submit\n/profile\n/credits\n/avatar\n/gallery\n/vip\n/help", reply_markup=back_button())

# ==========================================
# کالبک‌ها
# ==========================================
@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "🏠 منوی اصلی:", reply_markup=main_menu())

@dp.callback_query(F.data == "menu_submit")
async def cb_menu_submit(callback: CallbackQuery):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "🎨 نقاشی‌ت رو برام بفرست.")

@dp.callback_query(F.data == "menu_profile")
async def cb_menu_profile(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_profile(callback.message)

@dp.callback_query(F.data == "menu_credits")
async def cb_menu_credits(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_credits(callback.message)

@dp.callback_query(F.data == "menu_gallery")
async def cb_menu_gallery(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_gallery(callback.message)

@dp.callback_query(F.data == "menu_avatar")
async def cb_menu_avatar(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_avatar(callback.message)

@dp.callback_query(F.data == "menu_vip")
async def cb_menu_vip(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_vip(callback.message)

@dp.callback_query(F.data == "menu_support")
async def cb_menu_support(callback: CallbackQuery):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "❤️ حمایت: به زودی", reply_markup=back_button())

@dp.callback_query(F.data == "avatar_silver")
async def cb_avatar_silver(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if user["credits"] < 200: return await callback.answer("❌ اعتبار کم!", show_alert=True)
    await remove_credits(callback.from_user.id, 200)
    await update_avatar(callback.from_user.id, "silver")
    await callback.message.edit_text("✅ آواتار نقره‌ای فعال شد! 🥈")

@dp.callback_query(F.data == "avatar_gold")
async def cb_avatar_gold(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if user["credits"] < 500: return await callback.answer("❌ اعتبار کم!", show_alert=True)
    await remove_credits(callback.from_user.id, 500)
    await update_avatar(callback.from_user.id, "gold")
    await callback.message.edit_text("✅ آواتار طلایی فعال شد! 🥇")

@dp.callback_query(F.data.startswith("approve_"))
async def cb_approve(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await publish_artwork(int(callback.data.split("_")[1]))
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ منتشر شد!")

@dp.callback_query(F.data.startswith("reject_"))
async def cb_reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")

# ==========================================
# اجرا
# ==========================================
async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await init_db()
    print(f"🚀 ربات {BRAND_NAME} روشن شد...")
    await asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
