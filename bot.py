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

# Initialize Telegram bot application
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

# Data structures for user data
user_profiles = {}
user_favorites = {}
user_watchlists = {}
user_ratings = {}

# Helper function to fetch movies
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

# Command to set up user profile
async def setup_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    genre = " ".join(context.args).title()
    
    if genre not in [g for m in MOVIE_DATABASE for g in m["genre"]]:
        await update.message.reply_text("Invalid genre. Try: Action, Adventure, Comedy, etc.")
        return
    
    user_profiles[user_id] = genre
    await update.message.reply_text(f"Profile set! Your preferred genre is {genre}. You’ll receive recommendations accordingly.")

# Command to get personalized recommendations
async def recommend_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    preferred_genre = user_profiles.get(user_id)
    
    if not preferred_genre:
        await update.message.reply_text("You don't have a profile yet. Use /setup_profile <genre> to set it up.")
        return
    
    recommendations = await fetch_movie_info(genre=preferred_genre)
    
    if not recommendations:
        await update.message.reply_text("No recommendations available at the moment.")
    else:
        movie = random.choice(recommendations)
        await update.message.reply_text(f"🎬 *{movie['title']}*\n📖 {movie['description']}\n⭐ {movie['rating']}\n📅 {movie['release_year']}\n")

# Command to add movie to favorites
async def add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    movie_name = " ".join(context.args)
    
    if movie_name not in [m["title"] for m in MOVIE_DATABASE]:
        await update.message.reply_text("Movie not found.")
        return
    
    user_favorites.setdefault(user_id, []).append(movie_name)
    await update.message.reply_text(f"{movie_name} added to favorites!")

# Command to rate a movie
async def rate_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        movie_name, rating = " ".join(context.args[:-1]), int(context.args[-1])
        if rating < 1 or rating > 10:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /rate_movie <movie name> <rating (1-10)>")
        return
    
    user_ratings.setdefault(user_id, {})[movie_name] = rating
    await update.message.reply_text(f"Thank you! You rated {movie_name} as {rating}/10.")

# Start command with extended instructions
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Welcome to the Enhanced Movie Bot!* 🎬\n"
        "Here’s everything you can do:\n\n"
        "📝 *Commands:*\n"
        "/start - Display this message\n"
        "/setup_profile <genre> - Set up your preferred genre\n"
        "/recommend_movie - Get a movie recommendation based on your profile\n"
        "/add_favorite <movie name> - Add a movie to your favorites\n"
        "/view_favorites - View your list of favorite movies\n"
        "/rate_movie <movie name> <rating (1-10)> - Rate a movie\n"
        "/get_feedback - Provide feedback about the bot\n\n"
        "🌟 *Inline Commands:*\n"
        "- Type 'trending' to see trending movies\n"
        "- Type 'new' to view new releases\n"
        "- Search by typing a movie name\n"
        "- Use 'genre:<genre>' to filter by genre (e.g., 'genre:Comedy')\n"
        "- Find top movies of a specific year by typing 'best of <year>'\n\n"
        "Enjoy exploring! 🎬🍿"
    )

# Inline query handler
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # (Same as previous code, handles various inline queries)
    pass

# Flask and Telegram app initialization
@app.route('/')
def index():
    return "🤖 Enhanced Bot is running!"

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
