import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, Update
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, CallbackQueryHandler
from uuid import uuid4
from flask import Flask
import threading

# .env ফাইল লোড করা হচ্ছে
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_CHANNEL_ID = os.getenv("DEFAULT_CHANNEL_ID")

# Flask অ্যাপ তৈরি করা হচ্ছে
app = Flask(__name__)

# Telegram bot application তৈরি করা হচ্ছে
telegram_app = Application.builder().token(BOT_TOKEN).build()

# 🎥 সিনেমার তথ্য সংগ্রহের জন্য ফাংশন 🎥
async def fetch_movie_info(movie_name):
    # উদাহরণ হিসেবে সিনেমার তথ্য প্রদান
    return [
        {
            "title": f"{movie_name} 2024",
            "poster_url": "https://example.com/kalki_2024.jpg",
            "description": f"{movie_name} 2024 একটি জনপ্রিয় সিনেমা।",
            "rating": "⭐ 8.3",
            "genre": ["Action", "Adventure"],
            "tags": ["#Action", "#Drama", "#Epic", "#Adventure"],
            "release_year": 2024,
            "trending": True,
            "trailer_link": f"https://www.youtube.com/results?search_query={movie_name}+2024+trailer"
        },
        {
            "title": f"{movie_name} 2019",
            "poster_url": "https://example.com/kalki_2019.jpg",
            "description": f"{movie_name} 2019 একটি জনপ্রিয় সিনেমা।",
            "rating": "⭐ 7.8",
            "genre": ["Drama"],
            "tags": ["#Drama", "#Classic", "#Historical"],
            "release_year": 2019,
            "trending": False,
            "trailer_link": f"https://www.youtube.com/results?search_query={movie_name}+2019+trailer"
        }
    ]

# 🎬 ইনলাইন মোড হ্যান্ডলার 🎬
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    # 🎬 সিনেমার তালিকা সংগ্রহ করা 🎬
    movies = await fetch_movie_info(query)
    results = []
    for movie in movies:
        title_with_year = f"{movie['title']}"
        trending_tag = "🔥 Trending" if movie.get("trending") else "✨ Popular"

        # ইনলাইন রেসাল্ট বানানো
        results.append(
            InlineQueryResultPhoto(
                id=str(uuid4()),
                title=f"{title_with_year} {trending_tag}",
                photo_url=movie["poster_url"],
                thumb_url=movie["poster_url"],
                caption=(
                    f"🎬 *{title_with_year}*\n"
                    f"{trending_tag}\n"
                    f"⭐ *Rating:* {movie['rating']}\n"
                    f"🎭 *Genre:* {', '.join(movie['genre'])}\n"
                    f"🏷 *Tags:* {', '.join(movie['tags'])}\n"
                    f"📖 *Description:* {movie['description']}\n"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📣 Share to Channel", callback_data=f"post|{movie['title']}")],
                    [InlineKeyboardButton("▶️ Watch Trailer", url=movie["trailer_link"])]
                ])
            )
        )
    await update.inline_query.answer(results)

# 📢 চ্যানেলে পোস্ট করার কলব্যাক ফাংশন 📢
async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    movie_title = query.data.split('|')[1]

    # 🎥 নির্দিষ্ট সিনেমার তথ্য বের করা 🎥
    movie_info = next((m for m in await fetch_movie_info(movie_title) if m["title"] == movie_title), None)
    if not movie_info:
        await query.answer("⚠️ Movie information not found.")
        return

    # ✨ মুভির তথ্য পাঠানোর জন্য বার্তা গঠন করা ✨
    tags = ", ".join(movie_info["tags"])
    message = f"""
🎬 *Title:* {movie_info['title']}
⭐ *Rating:* {movie_info['rating']}
🎭 *Genre:* {', '.join(movie_info['genre'])}
🏷 *Tags:* {tags}
📖 *Description:* {movie_info['description']}
    """

    keyboard = [
        [InlineKeyboardButton("▶️ Watch Trailer", url=movie_info["trailer_link"])],
        [InlineKeyboardButton("🎥 Movie Channel", url="https://t.me/moviechannel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # চ্যানেলে পোস্ট করা হচ্ছে
    await context.bot.send_photo(chat_id=DEFAULT_CHANNEL_ID, photo=movie_info["poster_url"], caption=message, reply_markup=reply_markup, parse_mode="Markdown")
    await query.answer("✅ Successfully posted to channel!")

# 📄 সাহায্য কমান্ড 📄
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *কমান্ড সমূহ* 🎬\n"
        "/help - সাহায্য দেখুন\n"
        "🎬 ইনলাইন মোডে সিনেমার তথ্য খুঁজুন (টেক্সট টাইপ করুন)\n\n"
        "⚠️ উদাহরণ: সিনেমার নাম টাইপ করুন যেমন - Kalki"
    )

# 📲 বট হ্যান্ডলার যোগ করা 📲
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(InlineQueryHandler(inline_query))
telegram_app.add_handler(CallbackQueryHandler(post_to_channel, pattern=r'^post\|'))

# 🚀 Flask রুট 🚀
@app.route('/')
def index():
    return "🤖 Bot is running..."

@app.route('/health')
def health():
    return "✅ Bot health check successful!"

@app.route('/status')
def status():
    return {
        "status": "running",
        "features": ["Genre-based search", "Trending movies", "Tags display", "Release year filter"]
    }

# Flask এবং Telegram bot একসাথে চালানো হচ্ছে
def run_flask():
    app.run(port=5000)

def run_bot():
    telegram_app.run_polling()

if __name__ == "__main__":
    print("🤖 Bot is running with Flask server...")
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_bot).start()
