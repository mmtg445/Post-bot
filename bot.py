import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, Update
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, CallbackQueryHandler
from uuid import uuid4
from flask import Flask, jsonify
import threading

# .env ফাইল থেকে তথ্য লোড করা হচ্ছে
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_CHANNEL_ID = os.getenv("DEFAULT_CHANNEL_ID")

# Flask অ্যাপ তৈরি করা হচ্ছে
app = Flask(__name__)

# Telegram bot application তৈরি করা হচ্ছে
telegram_app = Application.builder().token(BOT_TOKEN).build()

# 🎬 মুভি ডাটাবেস (ডেমো হিসেবে) 🎬
MOVIE_DATABASE = [
    {
        "title": "Kalki 2024",
        "poster_url": "https://example.com/kalki_2024.jpg",
        "description": "Kalki 2024 একটি অ্যাকশনধর্মী সিনেমা।",
        "rating": "⭐ 8.3",
        "genre": ["Action", "Adventure"],
        "tags": ["#Action", "#Adventure", "#Blockbuster"],
        "release_year": 2024,
        "source": "Netflix",
        "trending": True,
        "new_release": True,
        "trailer_link": "https://www.youtube.com/results?search_query=Kalki+2024+trailer"
    },
    {
        "title": "Inception",
        "poster_url": "https://example.com/inception.jpg",
        "description": "Inception একটি সাই-ফাই অ্যাকশনধর্মী সিনেমা।",
        "rating": "⭐ 8.8",
        "genre": ["Sci-Fi", "Thriller"],
        "tags": ["#SciFi", "#MindBending", "#Thriller"],
        "release_year": 2010,
        "source": "Amazon Prime",
        "trending": False,
        "new_release": False,
        "trailer_link": "https://www.youtube.com/results?search_query=Inception+trailer"
    },
    {
        "title": "Avatar 2022",
        "poster_url": "https://example.com/avatar_2022.jpg",
        "description": "Avatar 2022 একটি বিখ্যাত ফ্যান্টাসি সিনেমা।",
        "rating": "⭐ 7.5",
        "genre": ["Fantasy", "Adventure"],
        "tags": ["#Fantasy", "#Adventure", "#Epic"],
        "release_year": 2022,
        "source": "Disney+",
        "trending": True,
        "new_release": True,
        "trailer_link": "https://www.youtube.com/results?search_query=Avatar+2022+trailer"
    }
    # আরও মুভি যোগ করা যেতে পারে...
]

# 🎬 সিনেমার তথ্য সংগ্রহের জন্য ফাংশন 🎬
async def fetch_movie_info(movie_name=None, genre=None, trending=False, new_release=False):
    results = []
    for movie in MOVIE_DATABASE:
        if (
            (movie_name and movie_name.lower() in movie["title"].lower()) or
            (genre and genre in movie["genre"]) or
            (trending and movie["trending"]) or
            (new_release and movie["new_release"])
        ):
            results.append(movie)
    return results

# 🎬 ইনলাইন মোড হ্যান্ডলার 🎬
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    if not query:
        return

    # 🎬 কিওয়ার্ড অনুযায়ী সিনেমা খোঁজা 🎬
    if query == "new":
        movies = await fetch_movie_info(new_release=True)
    elif query == "trending":
        movies = await fetch_movie_info(trending=True)
    elif query.startswith("genre:"):
        genre = query.split(":", 1)[1].strip()
        movies = await fetch_movie_info(genre=genre)
    else:
        movies = await fetch_movie_info(movie_name=query)

    results = []
    for movie in movies:
        title_with_year = f"{movie['title']}"
        trending_tag = "🔥 #Trending" if movie.get("trending") else "✨ #Popular"
        source_tag = f"📺 Source: {movie['source']}"

        # ইনলাইন রেসাল্ট তৈরি
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
                    f"📅 *Release Year:* {movie['release_year']}\n"
                    f"{source_tag}\n"
                    f"📖 *Description:* {movie['description']}\n"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📣 Share to Channel", callback_data=f"post|{movie['title']}")],
                    [InlineKeyboardButton("▶️ Watch Trailer", url=movie["trailer_link"])]
                ])
            )
        )
    await update.inline_query.answer(results, cache_time=10)

# 📢 চ্যানেলে পোস্ট করার কলব্যাক ফাংশন 📢
async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    movie_title = query.data.split('|')[1]

    # 🎥 নির্দিষ্ট সিনেমার তথ্য বের করা 🎥
    movie_info = next((m for m in MOVIE_DATABASE if m["title"] == movie_title), None)
    if not movie_info:
        await query.answer("⚠️ Movie information not found.")
        return

    # মুভির তথ্য বার্তা তৈরি
    tags = ", ".join(movie_info["tags"])
    message = f"""
🎬 *Title:* {movie_info['title']}
⭐ *Rating:* {movie_info['rating']}
🎭 *Genre:* {', '.join(movie_info['genre'])}
🏷 *Tags:* {tags}
📅 *Release Year:* {movie_info['release_year']}
📺 *Source:* {movie_info['source']}
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
        "🎬 ইনলাইন মোডে সিনেমার তথ্য খুঁজুন:\n\n"
        "কিওয়ার্ডের উদাহরণ:\n"
        "👉 সাধারণ খোঁজ: মুভির নাম টাইপ করুন\n"
        "👉 নতুন মুভি: 'new' টাইপ করুন\n"
        "👉 ট্রেন্ডিং মুভি: 'trending' টাইপ করুন\n"
        "👉 জনর অনুসারে খোঁজ: 'genre:genre_name' টাইপ করুন (যেমন - genre:Action)"
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
    return jsonify(status="running", health_check="success")

# Flask এবং Telegram bot একসাথে চালানো হচ্ছে
def run_flask():
    app.run(host="0.0.0.0", port=8000)  # TCP Health check জন্য host 0.0.0.0 ব্যবহার করা হচ্ছে

def run_bot():
    telegram_app.run_polling()

if __name__ == "__main__":
    print("🤖 Bot is running with Flask server...")
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_bot).start()
