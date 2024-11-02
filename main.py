import os
import random
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, Update
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
from uuid import uuid4
from flask import Flask, jsonify
import threading

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_CHANNEL_ID = os.getenv("DEFAULT_CHANNEL_ID")

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot application
telegram_app = Application.builder().token(BOT_TOKEN).build()

# 🎬 Extended Movie Database with multiple tags and attributes
MOVIE_DATABASE = [
    {
        "title": "Kalki 2024",
        "poster_url": "https://example.com/kalki_2024.jpg",
        "description": "An action-packed journey of a mythical hero.",
        "rating": "⭐ 8.3",
        "genre": ["Action", "Adventure"],
        "tags": ["#Action", "#Adventure", "#Blockbuster", "#Mythical"],
        "release_year": 2024,
        "source": "Netflix",
        "trending": True,
        "new_release": True,
        "top_rated": True,
        "comedy": False,
        "year_best": 2024,
        "trailer_link": "https://www.youtube.com/results?search_query=Kalki+2024+trailer"
    },
    # Add additional movies with different tags, genres, and sources...
]

# User data dictionaries
user_preferences = {}
user_feedback = {}
user_watch_history = {}
user_favorites = {}

# 🎬 Function to fetch movie information with filters
async def fetch_movies(name=None, genre=None, trending=False, new_release=False, top_rated=False, year=None, rating=None, source=None, tags=None):
    results = []
    for movie in MOVIE_DATABASE:
        if (
            (name and name.lower() in movie["title"].lower()) or
            (genre and genre in movie["genre"]) or
            (trending and movie["trending"]) or
            (new_release and movie["new_release"]) or
            (top_rated and movie.get("top_rated")) or
            (year and movie["release_year"] == year) or
            (rating and float(movie["rating"].split(" ")[1]) >= rating) or
            (source and movie["source"].lower() == source.lower()) or
            (tags and any(tag in movie["tags"] for tag in tags))
        ):
            results.append(movie)
    return results

# 🎬 Log user's watch history
async def log_watch_history(user_id, movie_title):
    if user_id not in user_watch_history:
        user_watch_history[user_id] = []
    user_watch_history[user_id].append(movie_title)

# 🎬 Command to start with enhanced message and instructions
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Welcome to MovieBot!* 🎬\n\n"
        "Here are some commands you can use:\n"
        "/start - Show this message\n"
        "/set_preferences <genres/tags> - Set preferences (e.g., Action, #Mythical)\n"
        "/recommend_random - Get a random movie\n"
        "/top_movies_of_year <year> - Show top movies of a year\n"
        "/watch_history - See your watch history\n"
        "/feedback <text> - Provide feedback\n"
        "/favorites - View your favorite movies\n\n"
        "*Inline Commands:*\n"
        "- Type 'trending' for trending movies\n"
        "- Use 'genre:<genre>' for specific genres\n"
        "- Use 'tag:<tag>' for specific tags\n"
    )

# 🎬 Inline Query Handler with added tag support
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    if not query:
        return

    # Process different query types
    if query == "new":
        movies = await fetch_movies(new_release=True)
    elif query == "trending":
        movies = await fetch_movies(trending=True)
    elif query.startswith("genre:"):
        genre = query.split(":", 1)[1].strip()
        movies = await fetch_movies(genre=genre)
    elif query.startswith("source:"):
        source = query.split(":", 1)[1].strip()
        movies = await fetch_movies(source=source)
    elif query.startswith("tag:"):
        tag = query.split(":", 1)[1].strip()
        movies = await fetch_movies(tags=[f"#{tag}"])
    else:
        movies = await fetch_movies(name=query)

    results = [
        InlineQueryResultPhoto(
            id=str(uuid4()),
            title=movie['title'],
            photo_url=movie['poster_url'],
            thumb_url=movie['poster_url'],
            caption=(
                f"🎬 *{movie['title']}*\n"
                f"⭐ *Rating:* {movie['rating']}\n"
                f"🎭 *Genre:* {', '.join(movie['genre'])}\n"
                f"📅 *Release Year:* {movie['release_year']}\n"
                f"🏷 *Tags:* {', '.join(movie['tags'])}\n"
                f"{movie['description']}\n"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Watch Trailer", url=movie["trailer_link"])],
                [InlineKeyboardButton("❤️ Add to Favorites", callback_data=f"fav|{movie['title']}")]
            ])
        ) for movie in movies
    ]
    await update.inline_query.answer(results, cache_time=10)

# 🎬 Command to set user preferences
async def set_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    preferences = " ".join(context.args).title()
    user_preferences[user_id] = preferences
    await update.message.reply_text(f"Preferences saved! Your preferences are: {preferences}.")

# 🎬 Command to view favorites
async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    favorites = user_favorites.get(user_id, [])
    if favorites:
        await update.message.reply_text("Your favorite movies:\n" + "\n".join(favorites))
    else:
        await update.message.reply_text("No favorites yet.")

# 🎬 Command for watch history
async def watch_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = user_watch_history.get(user_id, [])
    if history:
        await update.message.reply_text("Your watch history:\n" + "\n".join(history))
    else:
        await update.message.reply_text("You have no watch history.")

# 🎬 Command for feedback
async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    feedback_text = " ".join(context.args)
    if feedback_text:
        user_feedback[user_id] = feedback_text
        await update.message.reply_text("Thanks for your feedback!")
    else:
        await update.message.reply_text("Please add feedback text after the command.")

# Flask and Telegram bot initialization
@app.route('/')
def index():
    return "🤖 MovieBot is running!"

@app.route('/health')
def health():
    return jsonify(status="running", health_check="success")

def run_flask():
    app.run(host="0.0.0.0", port=8000)

def run_bot():
    telegram_app.run_polling()

if __name__ == "__main__":
    print("🤖 Bot is running with Flask server...")
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_bot).start()
