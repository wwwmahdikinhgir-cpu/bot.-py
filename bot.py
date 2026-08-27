import telebot
from telebot import types
from datetime import datetime
import sqlite3
import os

# ============================================
# ⚙️ تنظیمات - این قسمت را تغییر دهید
# ============================================

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '123456789'))
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', 'your_channel')
CHANNEL_URL = os.environ.get('CHANNEL_URL', 'https://t.me/your_channel')
CARD_NUMBER = os.environ.get('CARD_NUMBER', '6037-XXXX-XXXX-XXXX')
CARD_HOLDER = os.environ.get('CARD_HOLDER', 'Name')

PLANS = {
    "1month": {"name": "یک ماهه", "price": 150000, "volume": "30GB", "duration": "30 روز"},
    "3month": {"name": "سه ماهه", "price": 400000, "volume": "100GB", "duration": "90 روز"},
    "6month": {"name": "شش ماهه", "price": 700000, "volume": "200GB", "duration": "180 روز"},
}

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('nextnet.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    joined_date TEXT,
    balance INTEGER DEFAULT 0
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plan_id TEXT,
    price INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TEXT,
    vpn_config TEXT
)''')

conn.commit()

def check_membership(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def main_menu(is_admin=False):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🛒 خرید VPN", callback_data="buy_vpn"),
        types.InlineKeyboardButton("👤 حساب کاربری", callback_data="account")
    )
    keyboard.add(
        types.InlineKeyboardButton("💬 پشتیبانی", callback_data="support"),
        types.InlineKeyboardButton("📋 راهنما", callback_data="guide")
    )
    keyboard.add(
        types.InlineKeyboardButton("🎁 کد تخفیف", callback_data="discount"),
        types.InlineKeyboardButton("📊 وضعیت سرویس", callback_data="status")
    )
    if is_admin:
        keyboard.add(types.InlineKeyboardButton("⚙️ پنل مدیریت", callback_data="admin_panel"))
    return keyboard

def plans_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for plan_id, plan in PLANS.items():
        keyboard.add(
            types.InlineKeyboardButton(
                f"💎 {plan['name']} - {plan['price']:,} تومان\n📊 {plan['volume']} | ⏱ {plan['duration']}",
                callback_data=f"plan_{plan_id}"
            )
        )
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    return keyboard

def admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
    )
    keyboard.add(
        types.InlineKeyboardButton("🎁 کد تخفیف", callback_data="admin_discount"),
        types.InlineKeyboardButton("📦 سفارشات", callback_data="admin_orders")
    )
    keyboard.add(
        types.InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)',
                   (user.id, user.username, user.first_name, datetime.now().isoformat()))
    conn.commit()
    
    welcome = f"""
🌟 به ربات Next Net خوش آمدید {user.first_name}!

🔐 سرویس VPN پرسرعت و امن

━━━━━━━━━━━━━━━━━━━

✨ امکانات:
• سرعت بالا و پینگ پایین
• اتصال همزمان چند دستگاه
• پشتیبانی 24/7
• سرورهای اختصاصی

💳 پرداخت: کارت به کارت
🎁 کد تخفیف: دارد

━━━━━━━━━━━━━━━━━━━

برای شروع یکی از گزینه‌ها را انتخاب کنید:
    """
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(user.id == ADMIN_ID))

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "⚙️ پنل مدیریت:", reply_markup=admin_keyboard())
    else:
        bot.reply_to(message, "⛔️ شما دسترسی ندارید!")

@bot.callback_query_handler(func=lambda call: call.data == "buy_vpn")
def buy_vpn(call):
    if not check_membership(call.from_user.id):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_URL))
        keyboard.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_member"))
        bot.edit_message_text(
            f"⚠️ برای استفاده از ربات ابتدا در کانال ما عضو شوید:\n\n📢 @{CHANNEL_USERNAME}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        return
    bot.edit_message_text(
        "💎 انتخاب پلن VPN\n\nیکی از پلن‌ها را انتخاب کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=plans_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_member")
def check_member(call):
    if check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ عضویت تایید شد!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ حالا می‌توانید خرید کنید!", 
                        reply_markup=main_menu(call.from_user.id == ADMIN_ID))
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def select_plan(call):
    plan_id = call.data.replace("plan_", "")
    plan = PLANS.get(plan_id)
    if not plan:
        bot.answer_callback_query(call.id, "❌ پلن نامعتبر!")
        return
    cursor.execute('INSERT INTO orders (user_id, plan_id, price, created_at) VALUES (?, ?, ?, ?)',
                   (call.from_user.id, plan_id, plan['price'], datetime.now().isoformat()))
    conn.commit()
    order_id = cursor.lastrowid
    
    payment_text = f"""
🧾 پیش‌فاکتور سفارش #{order_id}

━━━━━━━━━━━━━━━━━━━

📦 پلن: {plan['name']}
📊 حجم: {plan['volume']}
⏱ مدت: {plan['duration']}
💰 مبلغ: {plan['price']:,} تومان

━━━━━━━━━━━━━━━━━━━

💳 شماره کارت:
`{CARD_NUMBER}`

👤 به نام: {CARD_HOLDER}

━━━━━━━━━━━━━━━━━━━

پس از پرداخت، روی دکمه زیر بزنید:
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✅ پرداخت کردم", callback_data=f"paid_{order_id}"))
    keyboard.add(types.InlineKeyboardButton("🔙 انصراف", callback_data="back_main"))
    bot.edit_message_text(payment_text, call.message.chat.id, call.message.message_id,
                         reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid(call):
    order_id = call.data.replace("paid_", "")
    admin_keyboard = types.InlineKeyboardMarkup()
    admin_keyboard.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{order_id}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}")
    )
    bot.send_message(
        ADMIN_ID,
        f"🔔 سفارش جدید #{order_id}\n\n👤 کاربر: {call.from_user.first_name} (@{call.from_user.username})\n🆔 آیدی: `{call.from_user.id}`",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )
    bot.edit_message_text(
        "✅ پرداخت شما ثبت شد!\n\nپس از تایید ادمین، کانفیگ ارسال می‌شود.\n⏱ معمولا کمتر از 30 دقیقه.",
        call.message.chat.id,
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_order(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔️ غیرمجاز!")
        return
    order_id = call.data.replace("confirm_", "")
    cursor.execute('UPDATE orders SET status = "completed" WHERE order_id = ?', (order_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "✅ تایید شد!")
    bot.edit_message_text(f"✅ سفارش #{order_id} تایید شد", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔️ غیرمجاز!")
        return
    order_id = call.data.replace("reject_", "")
    cursor.execute('UPDATE orders SET status = "rejected" WHERE order_id = ?', (order_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "❌ رد شد")
    bot.edit_message_text(f"❌ سفارش #{order_id} رد شد", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "account")
def account(call):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (call.from_user.id,))
    user = cursor.fetchone()
    cursor.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY order_id DESC LIMIT 5', (call.from_user.id,))
    orders = cursor.fetchall()
    
    text = f"""
👤 حساب کاربری

━━━━━━━━━━━━━━━━━━━

🆔 آیدی: `{call.from_user.id}`
📅 عضویت: {user[3][:10] if user else 'نامشخص'}
💰 کیف پول: {user[5] if user else 0:,} تومان

📦 سفارشات اخیر:
    """
    if orders:
        for order in orders:
            status = "✅" if order[4] == "completed" else "⏳"
            plan = PLANS.get(order[2], {})
            text += f"\n{status} #{order[0]} - {plan.get('name', 'نامشخص')}"
    else:
        text += "\nهنوز سفارشی ندارید"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    text = """
💬 پشتیبانی Next Net

━━━━━━━━━━━━━━━━━━━

برای ارتباط با پشتیبانی پیام دهید

🕐 ساعات پاسخگویی: 9 صبح تا 11 شب
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "guide")
def guide(call):
    text = """
📋 راهنمای استفاده

━━━━━━━━━━━━━━━━━━━

1️⃣ خرید VPN:
• "خرید VPN" را بزنید
• پلن انتخاب کنید
• پرداخت کنید
• "پرداخت کردم" را بزنید

2️⃣ دریافت کانفیگ:
• پس از تایید ادمین ارسال می‌شود

3️⃣ اتصال:
• اپ VPN نصب کنید
• کانفیگ را ایمپورت کنید
• متصل شوید 🚀

━━━━━━━━━━━━━━━━━━━

⚠️ هر اکانت فقط یک دستگاه
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "discount")
def discount(call):
    text = """
🎁 کد تخفیف

━━━━━━━━━━━━━━━━━━━

برای دریافت کد تخفیف:
• کانال ما را دنبال کنید
• در قرعه‌کشی‌ها شرکت کنید
• از پشتیبانی بپرسید

━━━━━━━━━━━━━━━━━━━
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "status")
def status(call):
    text = """
📊 وضعیت سرویس‌ها

━━━━━━━━━━━━━━━━━━━

✅ سرور آلمان: فعال
✅ سرور هلند: فعال
✅ سرور فرانسه: فعال
⚠️ سرور ترکیه: شلوغ

━━━━━━━━━━━━━━━━━━━
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔️ دسترسی غیرمجاز!")
        return
    bot.edit_message_text(
        "⚙️ پنل مدیریت\n\nیک گزینه را انتخاب کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "completed"')
    total_orders = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(price) FROM orders WHERE status = "completed"')
    total_revenue = cursor.fetchone()[0] or 0
    
    text = f"""
📊 آمار ربات

━━━━━━━━━━━━━━━━━━━

👥 کاربران: {total_users}
📦 سفارشات: {total_orders}
💰 درآمد: {total_revenue:,} تومان
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users(call):
    if call.from_user.id != ADMIN_ID:
        return
    cursor.execute('SELECT * FROM users ORDER BY joined_date DESC LIMIT 10')
    users = cursor.fetchall()
    
    text = "👥 آخرین کاربران:\n\n"
    for user in users:
        text += f"• {user[2]} (@{user[1]}) - {user[3][:10]}\n"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "admin_orders")
def admin_orders(call):
    if call.from_user.id != ADMIN_ID:
        return
    cursor.execute('SELECT * FROM orders ORDER BY order_id DESC LIMIT 10')
    orders = cursor.fetchall()
    
    text = "📦 آخرین سفارشات:\n\n"
    for order in orders:
        status = "✅" if order[4] == "completed" else "⏳"
        plan = PLANS.get(order[2], {})
        text += f"{status} #{order[0]} - {plan.get('name', 'نامشخص')} - {order[3]:,} تومان\n"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    bot.edit_message_text(
        "🌟 منوی اصلی\n\nیک گزینه را انتخاب کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu(call.from_user.id == ADMIN_ID)
    )

print("🤖 Next Net Bot is running...")
bot.infinity_polling()