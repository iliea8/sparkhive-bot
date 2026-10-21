import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8654231613:AAHjwE7y8ha2AS2aP79C3kbrNf2S2hkymE4"
ADMIN_ID = 7473332530
BRAND_NAME = "SPARKHIVE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ============ /start ============
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await db.init_db()
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.first_name or ""
        )
    await message.answer(
        f"سلام {message.from_user.first_name} عزیز! 👋\n\n"
        f"به کامیونیتی هنری **{config.BRAND_NAME}** خوش اومدی.\n\n"
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


# ============ /submit ============
@dp.message(Command("submit"))
async def cmd_submit(message: Message):
    await message.answer(
        "🎨 نقاشی‌ت رو برام بفرست.\n"
        "می‌تونی یه توضیح کوتاه هم همراهش بفرستی.\n\n"
        "⚠️ فقط عکس بفرست، نه فایل."
    )


# ============ دریافت عکس ============
@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    await db.save_artwork(user_id, file_id, caption)
    await db.add_credits(user_id, 10)
    
    user = await db.get_user(user_id)
    new_credits = user["credits"] + 10
    
    await message.answer(
        f"✅ نقاشی‌ت با موفقیت ثبت شد!\n\n"
        f"💰 **+۱۰ اعتبار** به حسابت اضافه شد.\n"
        f"💎 اعتبار کل: **{new_credits}**\n\n"
        "نقاشی‌ت برای بررسی ارسال شد. اگه تأیید بشه، توی کانال منتشر میشه و **+۵۰ اعتبار** دیگه می‌گیری! 🎉",
        parse_mode="Markdown",
        reply_markup=back_button()
    )
    
    try:
        await bot.send_photo(
            config.ADMIN_ID,
            file_id,
            caption=f"🎨 نقاشی جدید از {message.from_user.full_name}\n"
                    f"🆔 @{message.from_user.username or 'ندارد'}\n"
                    f"📝 توضیح: {caption or 'ندارد'}\n\n"
                    f"برای بررسی: /admin"
        )
    except Exception as e:
        logging.error(f"خطا در ارسال به ادمین: {e}")


# ============ /profile ============
@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("اول /start رو بزن.")
        return
    
    avatar_emoji = {"base": "⚪", "silver": "🥈", "gold": "🥇"}.get(user["avatar_level"], "⚪")
    vip_badge = "💎 VIP" if user["is_vip"] else ""
    verified = "✅" if user["is_verified"] else ""
    
    await message.answer(
        f"{avatar_emoji} **پروفایل هنری {user['first_name']}** {vip_badge} {verified}\n\n"
        f"🆔 آیدی: `{user['user_id']}`\n"
        f"💰 اعتبار: **{user['credits']}**\n"
        f"✨ سطح آواتار: **{user['avatar_level']}**\n"
        f"🔥 زنجیره: **{user['streak']} روز**\n"
        f"📅 عضویت: {user['joined_at']}\n\n"
        f"لینک اختصاصی گالری:\n"
        f"`https://t.me/{config.BRAND_NAME}_Bot?start=gallery_{user['user_id']}`",
        parse_mode="Markdown",
        reply_markup=back_button()
    )


# ============ /credits ============
@dp.message(Command("credits"))
async def cmd_credits(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("اول /start رو بزن.")
        return
    
    await message.answer(
        f"💰 **اعتبار تو: {user['credits']}**\n\n"
        "📈 **راه‌های کسب اعتبار:**\n"
        "🎨 ارسال نقاشی: **+۱۰**\n"
        "✅ انتشار توی کانال: **+۵۰**\n"
        "🔥 زنجیره۷ روزه: **+۱۰۰**\n\n"
        "🎁 **قابلیت‌های قابل باز کردن:**\n"
        "🥈 آواتار نقره‌ای: **۲۰۰**\n"
        "🥇 آواتار طلایی: **۵۰۰**\n"
        "📌 پین نقاشی: **۵۰۰**\n"
        "🖼️ گالری نامحدود: **۱۰۰۰**\n"
        "✅ نشان تأیید: **۲۰۰۰**",
        parse_mode="Markdown",
        reply_markup=back_button()
    )


# ============ /avatar ============
@dp.message(Command("avatar"))
async def cmd_avatar(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("اول /start رو بزن.")
        return
    
    await message.answer(
        f"✨ **آواتار فعلی تو: {user['avatar_level']}**\n\n"
        "آواتارها رو با اعتبار باز کن:",
        parse_mode="Markdown",
        reply_markup=avatar_menu(user["avatar_level"])
    )


# ============ /gallery ============
@dp.message(Command("gallery"))
async def cmd_gallery(message: Message):
    user_id = message.from_user.id
    artworks = await db.get_user_artworks(user_id)
    if not artworks:
        await message.answer(
            "🖼️ گالری تو خالیه.\n\n"
            "با /submit اولین نقاشی‌ت رو بفرست!",
            reply_markup=back_button()
        )
        return
    
    await message.answer(f"🖼️ **گالری تو: {len(artworks)} اثر**", parse_mode="Markdown")
    for art in artworks[:5]:
        status_emoji = "✅" if art["status"] == "published" else "⏳"
        await bot.send_photo(
            user_id,
            art["file_id"],
            caption=f"{status_emoji} وضعیت: {art['status']}\n"
                    f"📝 {art['caption'] or 'بدون توضیح'}\n"
                    f"📅 {art['created_at']}"
        )


# ============ /vip ============
@dp.message(Command("vip"))
async def cmd_vip(message: Message):
    await message.answer(
        f"💎 **اشتراک ویژه {config.BRAND_NAME}**\n\n"
        "با خرید اشتراک، اینا رو داری:\n"
        "✅ آواتار طلایی همیشگی\n"
        "✅ گالری نامحدود\n"
        "✅ نشان VIP کنار اسمت\n"
        "✅ دسترسی زودتر به رویدادها\n"
        "✅ نشان حامی\n\n"
        "💰 قیمت: به زودی اعلام میشه\n\n"
        "فعلاً می‌تونی از بات حمایت کنی:",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❤️ حمایت با Telegram Stars", callback_data="support_stars")]
        ])
    )


# ============ /admin ============
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ تو ادمین نیستی.")
        return
    
    pending = await db.get_pending_artworks()
    if not pending:
        await message.answer("🎉 هیچ نقاشی در انتظار تأیید نیست.")
        return
    
    await message.answer(f"📋 **{len(pending)} نقاشی در انتظار تأیید:**", parse_mode="Markdown")
    for art in pending[:10]:
        user = await db.get_user(art["user_id"])
        await bot.send_photo(
            config.ADMIN_ID,
            art["file_id"],
            caption=f"🆔 اثر #{art['id']}\n"
                    f"👤 {user['first_name'] if user else 'ناشناس'}\n"
                    f"📝 {art['caption'] or 'بدون توضیح'}",
            reply_markup=admin_review(art["id"])
        )


# ============ /help ============
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 **راهنمای ربات SPARKHIVE**\n\n"
        "🎨 **ارسال نقاشی:**\n"
        "با /submit یا دکمه‌ی «ارسال نقاشی» عکست رو بفرست.\n"
        "هر نقاشی **+۱۰ اعتبار** برات داره.\n\n"
        "💰 **اعتبار چیه؟**\n"
        "با فعالیت توی بات اعتبار می‌گیری و باهاش قابلیت‌های ویژه باز می‌کنی.\n\n"
        "🎁 **قابلیت‌های ویژه:**\n"
        "🥈 آواتار نقره‌ای (۲۰۰)\n"
        "🥇 آواتار طلایی (۵۰۰)\n"
        "📌 پین نقاشی (۵۰۰)\n"
        "🖼️ گالری نامحدود (۱۰۰۰)\n"
        "✅ نشان تأیید (۲۰۰۰)\n\n"
        "📋 **دستورات:**\n"
        "/start - منوی اصلی\n"
        "/submit - ارسال نقاشی\n"
        "/profile - پروفایل من\n"
        "/credits - اعتبار من\n"
        "/avatar - آواتار من\n"
        "/gallery - گالری من\n"
        "/vip - اشتراک ویژه\n""/help - همین راهنما\n\n"
        "❓ سوالی داشتی، توی کانال بپرس.",
        parse_mode="Markdown",
        reply_markup=back_button()
    )


# ============ دکمه‌های شیشه‌ای ============
@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    await callback.message.delete()
    await bot.send_message(
        callback.from_user.id,
        "🏠 منوی اصلی:",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "menu_submit")
async def cb_menu_submit(callback: CallbackQuery):
    await callback.message.delete()
    await bot.send_message(
        callback.from_user.id,
        "🎨 نقاشی‌ت رو برام بفرست.\n⚠️ فقط عکس بفرست."
    )


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
    await bot.send_message(
        callback.from_user.id,
        "❤️ **حمایت از SPARKHIVE**\n\n"
        "با حمایت مالی، به رشد کامیونیتی هنری کمک می‌کنی.\n"
        "به زودی امکان پرداخت با Telegram Stars فعال میشه.",
        parse_mode="Markdown",
        reply_markup=back_button()
    )


# ============ ارتقای آواتار ============
@dp.callback_query(F.data == "avatar_silver")
async def cb_avatar_silver(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if user["credits"] < 200:
        await callback.answer("❌ اعتبار کافی نداری! (نیاز: ۲۰۰)", show_alert=True)
        return
    await db.remove_credits(callback.from_user.id, 200)
    await db.update_avatar(callback.from_user.id, "silver")
    await callback.message.edit_text("✅ آواتار نقره‌ای فعال شد! 🥈")


@dp.callback_query(F.data == "avatar_gold")
async def cb_avatar_gold(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if user["credits"] < 500:
        await callback.answer("❌ اعتبار کافی نداری! (نیاز: ۵۰۰)", show_alert=True)
        return
    await db.remove_credits(callback.from_user.id, 500)
    await db.update_avatar(callback.from_user.id, "gold")
    await callback.message.edit_text("✅ آواتار طلایی فعال شد! 🥇")


# ============ تأیید ادمین ============
@dp.callback_query(F.data.startswith("approve_"))
async def cb_approve(callback: CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔", show_alert=True)
        return
    artwork_id = int(callback.data.split("_")[1])
    await db.publish_artwork(artwork_id)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ **منتشر شد!**",
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("reject_"))
async def cb_reject(callback: CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔", show_alert=True)
        return
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ **رد شد.**",
        parse_mode="Markdown"
    )


# ============ اجرا ============
async def main():
    await init_db()
    print(f"🚀 ربات {BRAND_NAME} روشن شد...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())