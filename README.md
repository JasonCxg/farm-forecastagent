# Farm AI Agent — v1 (Rule-Based Spray & Irrigation Advisor)

This is the first working version of your farm decision-support tool.
It tells you, based on free real-time weather data:
1. Whether it's safe to spray today
2. Whether you should irrigate today

No sensors. No paid APIs. No subscriptions.

## Files

- `weather.py` — fetches free hourly forecast data from Open-Meteo
- `decision_engine.py` — the rule-based "brain" that makes spray/irrigation decisions
- `main.py` — connects the two and prints your daily report

## How to run this on YOUR computer

**Step 1: Install Python** (if you don't have it)
Download from https://www.python.org/downloads/ — get version 3.10 or newer.

**Step 2: Install the one library this needs**
Open a terminal/command prompt and run:
```
pip install requests
```

**Step 3: Save these 3 files in the same folder**
Put `weather.py`, `decision_engine.py`, and `main.py` all in one folder, e.g. `farm-agent/`

**Step 4: Update your farm's coordinates**
Open `main.py` and find these lines near the bottom:
```python
FARM_LAT = 5.4141
FARM_LON = 100.3288
```
Replace with your farm's actual GPS coordinates. You can get these from Google Maps —
right-click your farm location, and it'll show you the lat/long numbers.

**Step 5: Run it**
```
python3 main.py
```

You should see a report like:
```
🌾 Daily Farm Report — Jason's Farm (Penang)
📍 Location: 5.4141, 100.3288

💧 SPRAY DECISION:
   ✅ SAFE TO SPRAY
   Reason: Conditions look safe for the next 6h (low rain risk, low wind).

🚿 IRRIGATION DECISION:
   ✅ IRRIGATE TODAY
   Reason: Low recent rain (0.0mm) and no significant rain expected - irrigation recommended.
```

## Important note about this sandbox vs. your computer

I built and tested this code's LOGIC thoroughly using mock data (fake weather numbers)
because this sandbox environment can't reach the Open-Meteo website directly (network
restriction on my end, not a flaw in the code). On your own computer, there's no such
restriction — `main.py` will pull real, live weather data immediately.

## What's NOT done yet (next steps)

1. **Historical rainfall**: irrigation logic currently assumes 0mm rain in the recent
   past (a placeholder). Next step is adding a call to Open-Meteo's historical weather
   endpoint so the irrigation decision is based on real past rainfall, not a placeholder.
2. **WhatsApp delivery**: right now this just prints to your terminal. Next step is
   wiring this into a WhatsApp bot (via Twilio) so you get this as a daily message.
3. **AI layer**: right now the "reason" text is a fixed template. Next step is sending
   the forecast + rule outputs to Claude's API so it writes a natural, conversational
   explanation instead of a fixed sentence — that's what makes it a true "AI agent"
   rather than a calculator.
4. **Scheduling**: this currently needs to be run manually. Next step is automatic daily
   runs (e.g. via a free cron job on Railway or Render).

## Customizing the rules

Open `decision_engine.py` — near the top of `should_spray()` you'll see:
```python
RAIN_CHANCE_THRESHOLD = 50  # percent
WIND_THRESHOLD = 20  # km/h
```
These are starting points based on general agronomy practice. As you test this against
your own farm's real conditions and crops, adjust these numbers to match what actually
works for your situation.
