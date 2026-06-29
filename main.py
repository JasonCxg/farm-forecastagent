"""
main.py
--------
Connects weather.py + decision_engine.py into one daily farm report.

This is the script you'll eventually run once a day (manually for now,
automatically later) to get your spray/irrigation recommendation.

Run it with:
    python3 main.py
"""

from weather import get_forecast
from decision_engine import should_spray, should_irrigate


def generate_daily_report(latitude: float, longitude: float, farm_name: str = "My Farm") -> str:
    """
    Fetch live weather and generate a plain-language daily report
    for spray and irrigation decisions.
    """
    # Get next 24 hours of forecast data
    forecast = get_forecast(latitude, longitude, hours=24)

    # --- Spray decision (look at next 6 hours) ---
    spray_result = should_spray(
        rain_chance_pct=forecast["rain_chance_pct"],
        rain_mm=forecast["rain_mm"],
        wind_speed_kmh=forecast["wind_speed_kmh"],
        hours_to_check=6,
    )

    # --- Irrigation decision ---
    # NOTE: we don't have "past rain" data wired up yet (that needs a
    # historical API call, which we'll add next). For now we treat past
    # rain as unknown (0) - this is a placeholder until v1.1.
    irrigation_result = should_irrigate(
        rain_mm_past=[0],  # placeholder - to be replaced with real historical data
        rain_chance_pct_future=forecast["rain_chance_pct"],
        rain_mm_future=forecast["rain_mm"],
        hours_ahead=24,
    )

    # --- Build the report ---
    report = []
    report.append(f"🌾 Daily Farm Report — {farm_name}")
    report.append(f"📍 Location: {latitude}, {longitude}")
    report.append("")
    report.append("💧 SPRAY DECISION:")
    report.append(f"   {'✅ SAFE TO SPRAY' if spray_result['decision'] else '⛔ DO NOT SPRAY'}")
    report.append(f"   Reason: {spray_result['reason']}")
    report.append("")
    report.append("🚿 IRRIGATION DECISION:")
    report.append(f"   {'✅ IRRIGATE TODAY' if irrigation_result['decision'] else '⛔ SKIP IRRIGATION'}")
    report.append(f"   Reason: {irrigation_result['reason']}")
    report.append("")
    report.append("⚠️  Note: irrigation logic is using placeholder past-rain data.")
    report.append("    Next step: add historical rainfall lookup for full accuracy.")

    return "\n".join(report)


if __name__ == "__main__":
    # Default: Penang, Malaysia coordinates
    # TODO: replace with your exact farm's GPS coordinates
    FARM_LAT = 5.4141
    FARM_LON = 100.3288
    FARM_NAME = "Jason's Farm (Penang)"

    print(generate_daily_report(FARM_LAT, FARM_LON, FARM_NAME))
