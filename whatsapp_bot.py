"""
whatsapp_bot.py
----------------
Listens for WhatsApp messages (via Twilio) and replies with farm
spray/irrigation decisions based on real-time weather data.

Commands you can send from WhatsApp:
  setlocation <lat> <lon>   -> save your farm's coordinates
                                e.g. "setlocation 5.4141 100.3288"
  spray                     -> get spray decision for your saved location
  irrigate                  -> get irrigation decision for your saved location
  forecast                  -> get both decisions at once
  help                      -> show available commands

Run this with:
    py whatsapp_bot.py

Then point Twilio's WhatsApp Sandbox "WHEN A MESSAGE COMES IN" webhook
to your ngrok URL + "/whatsapp" (e.g. https://xxxx.ngrok-free.dev/whatsapp)
"""

import json
import os

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from weather import get_forecast
from decision_engine import should_spray, should_irrigate

app = Flask(__name__)

# Simple local storage: maps WhatsApp phone number -> (lat, lon)
# Saved to a JSON file so it persists even if you restart the script.
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
    """Generate the spray + irrigation report as a WhatsApp-friendly string."""
    forecast = get_forecast(lat, lon, hours=24)

    spray_result = should_spray(
        rain_chance_pct=forecast["rain_chance_pct"],
        rain_mm=forecast["rain_mm"],
        wind_speed_kmh=forecast["wind_speed_kmh"],
        hours_to_check=6,
    )

    irrigation_result = should_irrigate(
        rain_mm_past=[0],  # placeholder, same as main.py for now
        rain_chance_pct_future=forecast["rain_chance_pct"],
        rain_mm_future=forecast["rain_mm"],
        hours_ahead=24,
    )

    lines = []
    lines.append(f"🌾 *Farm Report* ({lat}, {lon})")
    lines.append("")
    lines.append("💧 *Spray:* " + ("✅ Safe to spray" if spray_result["decision"] else "⛔ Do not spray"))
    lines.append(spray_result["reason"])
    lines.append("")
    lines.append("🚿 *Irrigation:* " + ("✅ Irrigate today" if irrigation_result["decision"] else "⛔ Skip irrigation"))
    lines.append(irrigation_result["reason"])

    return "\n".join(lines)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")  # e.g. "whatsapp:+60123456789"

    locations = load_locations()
    resp = MessagingResponse()
    reply_text = ""

    parts = incoming_msg.split()
    command = parts[0].lower() if parts else ""

    if command == "setlocation" and len(parts) == 3:
        try:
            lat = float(parts[1])
            lon = float(parts[2])
            locations[sender] = {"lat": lat, "lon": lon}
            save_locations(locations)
            reply_text = f"✅ Location saved: {lat}, {lon}\nNow try sending: forecast"
        except ValueError:
            reply_text = "⚠️ Invalid coordinates. Example: setlocation 5.4141 100.3288"

    elif command in ("spray", "irrigate", "forecast"):
        if sender not in locations:
            reply_text = (
                "⚠️ No location saved yet.\n"
                "Send: setlocation <lat> <lon>\n"
                "Example: setlocation 5.4141 100.3288"
            )
        else:
            lat = locations[sender]["lat"]
            lon = locations[sender]["lon"]
            try:
                reply_text = build_report(lat, lon)
            except Exception as e:
                reply_text = f"⚠️ Error fetching weather: {e}"

    elif command == "help" or command == "":
        reply_text = (
            "🌾 *Farm Bot Commands*\n\n"
            "setlocation <lat> <lon> - save your farm location\n"
            "forecast - get spray + irrigation decision\n"
            "spray - spray decision only\n"
            "irrigate - irrigation decision only\n"
            "help - show this message"
        )

    else:
        reply_text = "🤔 Unknown command. Send 'help' to see what I can do."

    resp.message(reply_text)
    return str(resp)


if __name__ == "__main__":
    print("Starting WhatsApp farm bot on port 8080...")
    print("Make sure ngrok is running and pointed at port 8080.")
    app.run(port=8080)
