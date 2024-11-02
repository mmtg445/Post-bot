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

# 🎬 মুভি ডাটাবেস 🎬
MOVIE_DATABASE = [
    # এখানে আপনার মুভির ডেটা এড করুন
]

# 🎬 স্টার্ট কমান্ড 🎬
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Trending Movies", callback_data="trending")],
        [InlineKeyboardButton("🌟 Top Rated Movies", callback_data="top_rated")],
        [InlineKeyboardButton("🆕 New Releases", callback_data="new")],
        [InlineKeyboardButton("🎭 Browse by Genre", callback_data="browse_genre")],
        [InlineKeyboardButton("🔍 Search Movie", switch_inline_query_current_chat="")],
        [InlineKeyboardButton("📢 Visit Movie Channel", url="https://t.me/moviechannel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎬 Welcome to Movie Bot!\n\n"
        "You can search movies, get trending, top-rated, new releases, and browse by genre.\n"
        "Choose an option below or type a movie name to search inline.",
        reply_markup=reply_markup
    )

# 🎬 সিনেমা অনুসন্ধান 🎬
async def fetch_movie_info(movie_name=None, genre=None, trending=False, new_release=False, top_rated=False, year_best=None, comedy=False):
    results = []
    for movie in MOVIE_DATABASE:
        if (
            (movie_name and movie_name.lower() in movie["title"].lower()) or
            (genre and genre in movie["genre"]) or
            (trending and movie["trending"]) or
            (new_release and movie["new_release"]) or
            (top_rated and movie.get("top_rated")) or
            (year_best and movie.get("year_best") == year_best) or
            (comedy and movie.get("comedy"))
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
    elif query == "top rated":
        movies = await fetch_movie_info(top_rated=True)
    elif query == "comedy":
        movies = await fetch_movie_info(comedy=True)
    elif query.startswith("best of"):
        year = int(query.split(" ")[-1])
        movies = await fetch_movie_info(year_best=year)
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

# 📲 বট হ্যান্ডলার যোগ করা 📲
telegram_app.add_handler(CommandHandler("start", start_command))
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
    app.run(host="0.0.0.0", port=8000)

def run_bot():
    telegram_app.run_polling()

if __name__ == "__main__":
    print("🤖 Bot is running with Flask server...")
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_bot).start()
