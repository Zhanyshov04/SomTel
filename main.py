import asyncio
import aiohttp
import time
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# --- TOKEN ---
TOKEN_API = "7583391474:AAF2dsZQCkizbVDuZzRMVEXzkIkExTeWY9w"

bot = Bot(token=TOKEN_API)
dp = Dispatcher()

# --- CACHE için ---
latest_rate = {"value": None, "last_update": 0}

# --- DİL VERİLERİ ---
LANGS = {
    "kg": {
        "welcome": "Салам! 💰 Мен SOMTEL. Бул бот аркылуу акча жөнөтүү, комиссия жана курс тууралуу маалымат ала аласыз.",
        "menu": "🏠 Башкы меню\nЭмне кылгыңыз келет:",
        "options": [
            "1️⃣ SOMTEL жөнүндө маалымат",
            "2️⃣ Комиссия эсептөө",
            "3️⃣ Валюта курсу",
            "4️⃣ Байланыш / Жардам"
        ],
        "back": "🔙 Артка кайтуу",
        "select_country": "🌍 Акчаны жөнөтүүчү өлкөнү тандаңыз:",
        "send_country": "🇹🇷 Түркия",
        "recv_country": "🇰🇬 Кыргызстан",
        "amount_info": "💡 Комиссия төмөнкүдөй эсептелет:\n\n🇹🇷 **Түркиядан жиберүү (TL)**:\n1-19999 = 2%\n20000-34999 = 1.7%\n35000+ = 1.5%\n\n🇰🇬 **Кыргызстандан жиберүү (SOM)**:\n1-49999 = 2.2%\n50000-99999 = 1.8%\n100000+ = 1.5%\n\n💰 **Жөнөтүү суммасын киргизиңиз:**",
        "enter_amount": "💰 Сумманы киргизиңиз:",
        "result": "Комиссия: {fee:.2f} {currency}",
        "rate_error": "❌ Валюта курсу алынган жок. Кийинчерээк аракет кылыңыз.",
        "contact": "📞 Байланыш маалыматтары:\n🇹🇷 WhatsApp: +905059389919\n📧 Email: janyshov04@gmail.com\n🇰🇬 Телефон: +996700200406"
    },
    "tr": {
        "welcome": "Hoş geldiniz! 💰 Ben SOMTEL. Bu bot ile para transferi hakkında bilgi alabilir, komisyon ücretlerini öğrenebilir ve döviz kurlarını görebilirsiniz.",
        "menu": "🏠 Ana Menü\nLütfen yapmak istediğiniz işlemi seçiniz:",
        "options": [
            "1️⃣ SOMTEL hakkında bilgi",
            "2️⃣ Ücret hesapla",
            "3️⃣ Döviz kurları",
            "4️⃣ Yardım / İletişim"
        ],
        "back": "🔙 Geri dön",
        "select_country": "🌍 Gönderen ülkeyi seçiniz:",
        "send_country": "🇹🇷 Türkiye",
        "recv_country": "🇰🇬 Kırgızistan",
        "amount_info": "💡 Komisyon oranları aşağıdaki gibidir:\n\n🇹🇷 **Türkiye'den gönderim (TL)**:\n1-19999 = 2%\n20000-34999 = 1.7%\n35000+ = 1.5%\n\n🇰🇬 **Kırgızistan'dan gönderim (SOM)**:\n1-49999 = 2.2%\n50000-99999 = 1.8%\n100000+ = 1.5%\n\n💰 **Lütfen göndermek istediğiniz miktarı yazınız:**",
        "enter_amount": "💰 Lütfen miktarı giriniz:",
        "result": "Komisyon: {fee:.2f} {currency}",
        "rate_error": "❌ Döviz kurları alınamadı. Lütfen tekrar deneyin.",
        "contact": "📞 İletişim Bilgileri:\n🇹🇷 WhatsApp: +905059389919\n📧 Email: janyshov04@gmail.com\n🇰🇬 Telefon: +996700200406"
    },
    "en": {
        "welcome": "Welcome! 💰 I am SOMTEL. With this bot, you can learn about money transfers, commission fees, and currency exchange rates.",
        "menu": "🏠 Main Menu\nPlease select what you want to do:",
        "options": [
            "1️⃣ About SOMTEL",
            "2️⃣ Calculate Fee",
            "3️⃣ Exchange Rates",
            "4️⃣ Help / Contact"
        ],
        "back": "🔙 Back",
        "select_country": "🌍 Select sending country:",
        "send_country": "🇹🇷 Turkey",
        "recv_country": "🇰🇬 Kyrgyzstan",
        "amount_info": "💡 Commission rates:\n\n🇹🇷 **From Turkey (TRY)**:\n1-19999 = 2%\n20000-34999 = 1.7%\n35000+ = 1.5%\n\n🇰🇬 **From Kyrgyzstan (SOM)**:\n1-49999 = 2.2%\n50000-99999 = 1.8%\n100000+ = 1.5%\n\n💰 **Enter amount to send:**",
        "enter_amount": "💰 Enter the amount:",
        "result": "Fee: {fee:.2f} {currency}",
        "rate_error": "❌ Could not retrieve exchange rates. Try again later.",
        "contact": "📞 Contact Info:\n🇹🇷 WhatsApp: +905059389919\n📧 Email: janyshov04@gmail.com\n🇰🇬 Phone: +996700200406"
    }
}

user_language = {}
user_transfer = {}

# --- KURLAR (her dakika güncellenir) ---
async def get_exchange_rate():
    """TRY -> KGS döviz kurunu alır (her dakika bir kez güncellenir)."""
    now = time.time()
    # 60 saniyeden eskiyse güncelle
    if now - latest_rate["last_update"] > 60 or latest_rate["value"] is None:
        url = "https://open.er-api.com/v6/latest/TRY"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    rate = data.get("rates", {}).get("KGS")
                    if rate:
                        latest_rate["value"] = rate
                        latest_rate["last_update"] = now
        except Exception as e:
            print("Kur çekme hatası:", e)

    return latest_rate["value"]

# --- /start ---
@dp.message(CommandStart())
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang_kg")],
        [InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="lang_tr")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ])
    await message.answer("🌍 Dil seçiniz / Choose your language / Тилди тандаңыз:", reply_markup=keyboard)

# --- Dil seçimi ---
@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback_query: CallbackQuery):
    lang = callback_query.data.split("_")[1]
    user_language[callback_query.from_user.id] = lang
    text = LANGS[lang]["welcome"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt, callback_data=f"menu_{i+1}")] for i, opt in enumerate(LANGS[lang]["options"])
    ])
    await callback_query.message.edit_text(text + "\n\n" + LANGS[lang]["menu"], reply_markup=keyboard)

# --- Menü işlemleri ---
@dp.callback_query(lambda c: c.data.startswith("menu_"))
async def handle_menu(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    lang = user_language.get(user_id, "tr")
    data = callback_query.data

    if data == "menu_1":  # SOMTEL hakkında bilgi
        info = {
            "tr": "📘 SOMTEL, Türkiye ve Kırgızistan arasında hızlı, güvenli ve düşük ücretli para transfer hizmeti sunar.",
            "kg": "📘 SOMTEL - Түркия менен Кыргызстандын ортосундагы тез жана коопсуз акча жөнөтүү кызматын сунуштайт.",
            "en": "📘 SOMTEL offers fast, secure, and low-cost money transfers between Turkey and Kyrgyzstan."
        }
        text = info[lang]
    elif data == "menu_2":  # Ücret hesapla
        text = LANGS[lang]["select_country"]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=LANGS[lang]["send_country"], callback_data="send_TR")],
            [InlineKeyboardButton(text=LANGS[lang]["recv_country"], callback_data="send_KG")]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        return
    elif data == "menu_3":  # Döviz kurları
        rate = await get_exchange_rate()
        if rate:
            text = f"💱 1 TRY = {round(rate, 2)} KGS 🇰🇬\n🕒 Son güncelleme: {time.strftime('%H:%M:%S')}"
        else:
            text = LANGS[lang]["rate_error"]
    elif data == "menu_4":  # İletişim
        text = LANGS[lang]["contact"]
    else:
        text = "❌ Geçersiz seçim."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANGS[lang]["back"], callback_data="main_menu")]])
    await callback_query.message.edit_text(text, reply_markup=keyboard)

# --- Ana Menüye dön ---
@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu(callback_query: CallbackQuery):
    lang = user_language.get(callback_query.from_user.id, "tr")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt, callback_data=f"menu_{i+1}")] for i, opt in enumerate(LANGS[lang]["options"])
    ])
    await callback_query.message.edit_text(LANGS[lang]["menu"], reply_markup=keyboard)

# --- Ücret Hesaplama ---
@dp.callback_query(lambda c: c.data.startswith("send_"))
async def select_country(callback_query: CallbackQuery):
    lang = user_language.get(callback_query.from_user.id, "tr")
    sender_country = callback_query.data.split("_")[1]
    user_transfer[callback_query.from_user.id] = {"sender": sender_country}
    await callback_query.message.edit_text(LANGS[lang]["amount_info"])

@dp.message()
async def calculate_fee(message: Message):
    user_id = message.from_user.id
    if user_id not in user_transfer:
        return

    lang = user_language.get(user_id, "tr")
    sender = user_transfer[user_id]["sender"]

    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Geçersiz miktar. Lütfen sayısal bir değer girin.")
        return

    if sender == "TR":
        if amount <= 19999:
            rate = 0.02
        elif amount <= 34999:
            rate = 0.017
        else:
            rate = 0.015
        currency = "TL"
    else:
        if amount <= 49999:
            rate = 0.022
        elif amount <= 99999:
            rate = 0.018
        else:
            rate = 0.015
        currency = "SOM"

    fee = amount * rate
    await message.answer(LANGS[lang]["result"].format(fee=fee, currency=currency))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Tekrar Hesapla", callback_data="menu_2")],
        [InlineKeyboardButton(text=LANGS[lang]["back"], callback_data="main_menu")]
    ])
    await message.answer("Ne yapmak istersiniz?", reply_markup=keyboard)

# --- Başlat ---
async def main():
    print("🚀 SOMTEL Bot başlatıldı.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
