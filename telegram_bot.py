"""
telegram_bot.py
----------------
Telegram version of the farm spray/irrigation advisor bot.
No message limits, completely free, no Twilio needed.

Commands you can send in Telegram:
  /setlocation <lat> <lon>   -> save your farm's coordinates
                                 e.g. /setlocation 5.4141 100.3288
  /spray                     -> get spray decision for your saved location
  /irrigate                  -> get irrigation decision for your saved location
  /forecast                  -> get both decisions at once
  /help                      -> show available commands

Run this with:
    python telegram_bot.py

Needs an environment variable TELEGRAM_BOT_TOKEN set to your bot's token
(get this from @BotFather on Telegram).
"""

import json
import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from weather import get_forecast
from decision_engine import should_spray, should_irrigate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS_FILE = "user_locations.json"


def load_locations() -> dict:
    if os.path.exists(LOCATIONS_FILE):
        with open(LOCATIONS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_locations(locations: dict) -> None:
    with open(LOCATIONS_FILE, "w") as f:
        json.dump(locations, f)


def build_report(lat: float, lon: float) -> str:
    """Generate the spray + irrigation report as a Telegram-friendly string."""
    forecast = get_forecast(lat, lon, hours=24)

    spray_result = should_spray(
        rain_chance_pct=forecast["rain_chance_pct"],
        rain_mm=forecast["rain_mm"],
        wind_speed_kmh=forecast["wind_speed_kmh"],
        hours_to_check=6,
    )

    irrigation_result = should_irrigate(
        rain_mm_past=[0],  # placeholder, same limitation as before
        rain_chance_pct_future=forecast["rain_chance_pct"],
        rain_mm_future=forecast["rain_mm"],
        hours_ahead=24,
    )

    lines = []
    lines.append(f"🌾 Farm Report ({lat}, {lon})")
    lines.append("")
    lines.append("💧 Spray: " + ("✅ Safe to spray" if spray_result["decision"] else "⛔ Do not spray"))
    lines.append(spray_result["reason"])
    lines.append("")
    lines.append("🚿 Irrigation: " + ("✅ Irrigate today" if irrigation_result["decision"] else "⛔ Skip irrigation"))
    lines.append(irrigation_result["reason"])

    return "\n".join(lines)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🌾 Farm Bot Commands\n\n"
        "/setlocation <lat> <lon> - save your farm location\n"
        "/forecast - get spray + irrigation decision\n"
        "/spray - spray decision only\n"
        "/irrigate - irrigation decision only\n"
        "/help - show this message"
    )
    await update.message.reply_text(text)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await help_command(update, context)


async def setlocation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    args = context.args  # text after the command, already split by spaces

    if len(args) != 2:
        await update.message.reply_text(
            "⚠️ Usage: /setlocation <lat> <lon>\nExample: /setlocation 5.4141 100.3288"
        )
        return

    try:
        lat = float(args[0])
        lon = float(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid coordinates. Example: /setlocation 5.4141 100.3288")
        return

    locations = load_locations()
    locations[chat_id] = {"lat": lat, "lon": lon}
    save_locations(locations)

    await update.message.reply_text(f"✅ Location saved: {lat}, {lon}\nNow try /forecast")


async def _send_report_or_prompt(update: Update) -> None:
    chat_id = str(update.effective_chat.id)
    locations = load_locations()

    if chat_id not in locations:
        await update.message.reply_text(
            "⚠️ No location saved yet.\n"
            "Send: /setlocation <lat> <lon>\n"
            "Example: /setlocation 5.4141 100.3288"
        )
        return

    lat = locations[chat_id]["lat"]
    lon = locations[chat_id]["lon"]

    try:
        report = build_report(lat, lon)
        await update.message.reply_text(report)
    except Exception as e:
        logger.exception("Error building report")
        await update.message.reply_text(f"⚠️ Error fetching weather: {e}")


async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_report_or_prompt(update)


async def spray_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # For simplicity v1 reuses the same combined report.
    # (We can split spray-only / irrigate-only logic out later if you want.)
    await _send_report_or_prompt(update)


async def irrigate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_report_or_prompt(update)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is not set. "
            "Get a token from @BotFather on Telegram and set it before running."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setlocation", setlocation_command))
    application.add_handler(CommandHandler("forecast", forecast_command))
    application.add_handler(CommandHandler("spray", spray_command))
    application.add_handler(CommandHandler("irrigate", irrigate_command))

    print("Telegram farm bot starting (polling mode)...")
    application.run_polling()


if __name__ == "__main__":
    main()
