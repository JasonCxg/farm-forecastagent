"""
decision_engine.py
-------------------
The "brain" of the farm AI agent (v1 - rule based, no AI yet).

Takes a weather forecast (from weather.py) and decides:
  1. Should the farmer spray today? (pesticide/fertilizer)
  2. Should the farmer irrigate today?

These are simple, transparent rules based on agronomy best practice.
Once this works and you trust it, we'll layer an LLM on top to turn
these into natural, explained advice (that's v2).
"""

from typing import List


def should_spray(
    rain_chance_pct: List[float],
    rain_mm: List[float],
    wind_speed_kmh: List[float],
    hours_to_check: int = 6,
) -> dict:
    """
    Decide whether it's safe to spray (pesticide/fertilizer) right now.

    Rules:
      - Don't spray if rain is likely (>50% chance) in the next `hours_to_check` hours
        -> rain washes off the spray before it works
      - Don't spray if wind speed is too high (>20 km/h)
        -> risk of spray drifting onto neighboring crops or being wasted
      - Otherwise, it's a safe window to spray

    Args:
        rain_chance_pct: hourly rain probability list (from forecast)
        rain_mm: hourly rain amount list (from forecast)
        wind_speed_kmh: hourly wind speed list (from forecast)
        hours_to_check: how many hours ahead to look (default 6)

    Returns:
        dict with 'decision' (True/False), 'reason' (str), and 'risk_factors' (list)
    """
    window_rain_chance = rain_chance_pct[:hours_to_check]
    window_rain_mm = rain_mm[:hours_to_check]
    window_wind = wind_speed_kmh[:hours_to_check]

    risk_factors = []

    max_rain_chance = max(window_rain_chance) if window_rain_chance else 0
    max_wind = max(window_wind) if window_wind else 0
    total_rain_mm = sum(window_rain_mm) if window_rain_mm else 0

    RAIN_CHANCE_THRESHOLD = 50  # percent
    WIND_THRESHOLD = 20  # km/h

    if max_rain_chance > RAIN_CHANCE_THRESHOLD:
        risk_factors.append(
            f"High rain chance ({max_rain_chance}%) within next {hours_to_check}h - spray may wash off"
        )

    if max_wind > WIND_THRESHOLD:
        risk_factors.append(
            f"High wind speed ({max_wind} km/h) within next {hours_to_check}h - drift risk"
        )

    decision = len(risk_factors) == 0

    if decision:
        reason = f"Conditions look safe for the next {hours_to_check}h (low rain risk, low wind)."
    else:
        reason = "Spraying not recommended: " + "; ".join(risk_factors)

    return {
        "decision": decision,
        "reason": reason,
        "risk_factors": risk_factors,
        "max_rain_chance_pct": max_rain_chance,
        "max_wind_kmh": max_wind,
    }


def should_irrigate(
    rain_mm_past: List[float],
    rain_chance_pct_future: List[float],
    rain_mm_future: List[float],
    hours_ahead: int = 24,
    dry_threshold_mm: float = 5.0,
) -> dict:
    """
    Decide whether the farmer should irrigate today.

    Rules:
      - If there's been little/no rain recently AND none expected soon -> irrigate
      - If rain is coming soon (>50% chance) -> hold off, let nature do the watering
      - If it's already rained enough recently -> no need to irrigate

    Args:
        rain_mm_past: rainfall in mm over the recent past (e.g. last 24-48h)
        rain_chance_pct_future: hourly rain probability looking forward
        rain_mm_future: hourly rain amount looking forward
        hours_ahead: how many hours ahead to check for incoming rain
        dry_threshold_mm: how much rain (mm) counts as "enough" to skip irrigation

    Returns:
        dict with 'decision' (True/False) and 'reason' (str)
    """
    window_chance = rain_chance_pct_future[:hours_ahead]
    window_future_mm = rain_mm_future[:hours_ahead]

    total_past_rain = sum(rain_mm_past) if rain_mm_past else 0
    max_future_chance = max(window_chance) if window_chance else 0
    total_future_rain = sum(window_future_mm) if window_future_mm else 0

    RAIN_COMING_THRESHOLD = 50  # percent

    if total_past_rain >= dry_threshold_mm:
        decision = False
        reason = f"Recent rainfall ({total_past_rain:.1f}mm) already meets soil needs - skip irrigation."
    elif max_future_chance > RAIN_COMING_THRESHOLD and total_future_rain >= dry_threshold_mm:
        decision = False
        reason = (
            f"Rain likely soon ({max_future_chance}% chance, ~{total_future_rain:.1f}mm expected) "
            f"- hold off and let rain do the watering."
        )
    else:
        decision = True
        reason = (
            f"Low recent rain ({total_past_rain:.1f}mm) and no significant rain expected "
            f"- irrigation recommended."
        )

    return {
        "decision": decision,
        "reason": reason,
        "total_past_rain_mm": total_past_rain,
        "max_future_rain_chance_pct": max_future_chance,
        "total_future_rain_mm": total_future_rain,
    }


if __name__ == "__main__":
    # Quick manual test with realistic-looking sample data
    print("=== TEST 1: Safe spray conditions ===")
    result = should_spray(
        rain_chance_pct=[10, 15, 20, 25, 10, 5],
        rain_mm=[0, 0, 0, 0, 0, 0],
        wind_speed_kmh=[8, 9, 10, 7, 6, 5],
    )
    print(result["reason"])
    print(f"Decision: {'SPRAY' if result['decision'] else 'DO NOT SPRAY'}\n")

    print("=== TEST 2: Rain coming soon, should NOT spray ===")
    result = should_spray(
        rain_chance_pct=[20, 30, 70, 80, 60, 40],
        rain_mm=[0, 0, 2.5, 5.0, 1.0, 0],
        wind_speed_kmh=[8, 9, 10, 7, 6, 5],
    )
    print(result["reason"])
    print(f"Decision: {'SPRAY' if result['decision'] else 'DO NOT SPRAY'}\n")

    print("=== TEST 3: Irrigation needed (dry conditions) ===")
    result = should_irrigate(
        rain_mm_past=[0, 0, 0],
        rain_chance_pct_future=[10, 15, 20],
        rain_mm_future=[0, 0, 0],
    )
    print(result["reason"])
    print(f"Decision: {'IRRIGATE' if result['decision'] else 'DO NOT IRRIGATE'}\n")

    print("=== TEST 4: Irrigation NOT needed (rain coming) ===")
    result = should_irrigate(
        rain_mm_past=[0, 0, 0],
        rain_chance_pct_future=[60, 70, 80],
        rain_mm_future=[5, 8, 10],
    )
    print(result["reason"])
    print(f"Decision: {'IRRIGATE' if result['decision'] else 'DO NOT IRRIGATE'}\n")
