import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, Update, ParseMode
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, CallbackQueryHandler
from uuid import uuid4
from flask import Flask, jsonify
import threading
import random

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_CHANNEL_ID = os.getenv("DEFAULT_CHANNEL_ID")

# Initialize Flask app
app = Flask(__name__)

# Telegram bot application
telegram_app = Application.builder().token(BOT_TOKEN).build()

# 🎬 Sample movie database with varied genres and attributes
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
        "top_rated": True,
        "comedy": False,
        "year_best": 2024,
        "trailer_link": "https://www.youtube.com/results?search_query=Kalki+2024+trailer"
    },
    # Add more movies here...
]

# Function to search for movies based on various filters
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

# Inline query handler for searching movies
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    if not query:
        return

    # Filter movies based on query
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

    # Create inline results
    results = []
    for movie in movies:
        trending_tag = "🔥 #Trending" if movie.get("trending") else "✨ #Popular"
        source_tag = f"📺 Source: {movie['source']}"

        results.append(
            InlineQueryResultPhoto(
                id=str(uuid4()),
                title=f"{movie['title']} {trending_tag}",
                photo_url=movie["poster_url"],
                thumb_url=movie["poster_url"],
                caption=(
                    f"🎬 *{movie['title']}*\n"
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

# Callback function to post movie details to the channel
async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    movie_title = query.data.split('|')[1]

    movie_info = next((m for m in MOVIE_DATABASE if m["title"] == movie_title), None)
    if not movie_info:
        await query.answer("⚠️ Movie information not found.")
        return

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

    await context.bot.send_photo(chat_id=DEFAULT_CHANNEL_ID, photo=movie_info["poster_url"], caption=message, reply_markup=reply_markup, parse_mode="Markdown")
    await query.answer("✅ Successfully posted to channel!")

# Enhanced start command with detailed usage instructions
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Welcome to the Movie Bot!* 🎬\n"
        "This bot helps you find movies, view trailers, explore by genres, and much more.\n\n"
        "*Available Commands:*\n"
        "/start - View start instructions\n"
        "/help - Display a list of available commands\n"
        "/favorites - View or manage your favorite movies\n"
        "/watchlist - View or manage your watchlist\n"
        "/trending - See trending movies\n"
        "/new - Discover new releases\n\n"
        "*Inline Commands:* (type these in chat)\n"
        "- Search by typing a movie name\n"
        "- Type 'new' for latest releases\n"
        "- Type 'trending' for popular movies\n"
        "- Search by genre, e.g., 'genre:Action'\n"
        "- Use 'best of [year]' to find top movies of the year\n\n"
        "Explore movies and enjoy a personalized experience! 🎬✨"
    )

# Help command with usage tips
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Movie Bot Commands* 🎬\n\n"
        "/start - Start and get usage instructions\n"
        "/help - Show this help message\n"
        "/favorites - Manage your favorite movies\n"
        "/watchlist - Access your watchlist\n"
        "/trending - Get trending movie list\n"
        "/new - Get list of new movie releases\n\n"
        "*Inline Search Examples:*\n"
        "- 'genre:Action' for movies by genre\n"
        "- 'best of 2023' for top movies by year"
    )

# Add command handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(InlineQueryHandler(inline_query))
telegram_app.add_handler(CallbackQueryHandler(post_to_channel, pattern=r'^post\|'))

# Flask routes
@app.route('/')
def index():
    return "🤖 Bot is running..."

@app.route('/health')
def health():
    return jsonify(status="running", health_check="success")

# Run Flask and Telegram bot
def run_flask():
    app.run(host="0.0.0.0", port=8000)

def run_bot():
    telegram_app.run_polling()

if __name__ == "__main__":
    print("🤖 Bot is running with Flask server...")
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_bot).start()
