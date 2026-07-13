"""
OpenWeatherMap integration for the LangGraph weather tool.

All HTTP calls and formatting live here — graph nodes only call service functions.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Final, Literal

import requests

from app.config import settings

logger = logging.getLogger(__name__)

OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

WEATHER_TOOL_NAMES: Final[frozenset[str]] = frozenset({"get_weather"})

WeatherIntent = Literal["current", "forecast", "rain_today", "rain_tomorrow"]

_RAIN_WEATHER_MAINS: Final[frozenset[str]] = frozenset(
    {"Rain", "Drizzle", "Thunderstorm"}
)

_WEATHER_KEYWORDS: Final[tuple[str, ...]] = (
    "weather",
    "temperature",
    "forecast",
    "will it rain",
    "going to rain",
    "rain today",
    "rain tomorrow",
    "how hot",
    "how cold",
    "humidity",
    "wind speed",
    "wind in",
    "climate",
    "sunny",
    "later today",
    "what's the weather",
    "whats the weather",
)

_CITY_EXTRACTION_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(
        r"(?:weather|temperature|forecast|climate|humidity|wind speed)\s+(?:in|for|at)\s+"
        r"([A-Za-z][A-Za-z\s\-]{1,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"forecast\s+for\s+([A-Za-z][A-Za-z\s\-]{1,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"how\s+(?:hot|cold)\s+is\s+([A-Za-z][A-Za-z\s\-]{1,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"is\s+it\s+sunny\s+in\s+([A-Za-z][A-Za-z\s\-]{1,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"will\s+it\s+rain\s+(?:today|tomorrow)?\s*(?:in|for|at)?\s*"
        r"([A-Za-z][A-Za-z\s\-]{1,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"will\s+it\s+rain\s+(?:today|tomorrow)\s+in\s+([A-Za-z][A-Za-z\s\-]{1,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-]{1,40})\s*\??\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-]{1,40})(?:\s+today|\s+tomorrow|\s+now)?",
        re.IGNORECASE,
    ),
)

_CITY_FROM_FORMATTED: Final[re.Pattern[str]] = re.compile(
    r"📍\s*Weather for\s+([A-Za-z][A-Za-z\s\-]{1,40})",
    re.IGNORECASE,
)

_STRIP_CITY_SUFFIXES: Final[re.Pattern[str]] = re.compile(
    r"\b(today|tomorrow|now|please|right now|later)\b",
    re.IGNORECASE,
)


def is_weather_request(message: str) -> bool:
    """True when the message is asking about weather rather than support or RAG."""
    text = (message or "").strip().lower()
    if not text:
        return False
    return any(keyword in text for keyword in _WEATHER_KEYWORDS)


def detect_weather_intent(message: str) -> WeatherIntent:
    """Pick current weather vs forecast / rain outlook from the user message."""
    text = (message or "").strip().lower()

    if "rain tomorrow" in text or (
        "tomorrow" in text and ("rain" in text or "forecast" in text)
    ):
        return "rain_tomorrow"

    if any(
        phrase in text
        for phrase in (
            "will it rain",
            "going to rain",
            "rain today",
            "later today",
            "forecast",
        )
    ):
        if "tomorrow" in text:
            return "rain_tomorrow"
        return "rain_today"

    return "current"


def _clean_city_name(raw: str) -> str | None:
    city = (raw or "").strip(" ?.,!")
    city = _STRIP_CITY_SUFFIXES.sub("", city).strip()
    if len(city) < 2:
        return None
    return city.title()


def extract_city_from_message(message: str) -> str | None:
    """Extract a city name from common weather question phrasings."""
    text = (message or "").strip()
    if not text:
        return None

    for pattern in _CITY_EXTRACTION_PATTERNS:
        match = pattern.search(text)
        if match:
            city = _clean_city_name(match.group(1))
            if city:
                return city

    return None


def extract_city_from_history(conversation_history: list[dict] | None) -> str | None:
    """Reuse the most recent city mentioned in prior weather turns."""
    if not conversation_history:
        return None

    for msg in reversed(conversation_history):
        text = ""
        parts = msg.get("parts") or []
        if parts and isinstance(parts[0], str):
            text = parts[0]

        formatted_match = _CITY_FROM_FORMATTED.search(text)
        if formatted_match:
            city = _clean_city_name(formatted_match.group(1))
            if city:
                return city

        if msg.get("role") == "user":
            city = extract_city_from_message(text)
            if city:
                return city

    return None


def resolve_city(
    message: str,
    conversation_history: list[dict] | None = None,
) -> str | None:
    """Resolve city from the current message, then fall back to conversation memory."""
    return extract_city_from_message(message) or extract_city_from_history(
        conversation_history
    )


def condition_to_emoji(condition: str, main: str = "") -> str:
    """Map OpenWeather conditions to display emojis."""
    text = f"{condition} {main}".lower()

    if "thunder" in text:
        return "⛈"
    if "snow" in text:
        return "❄️"
    if "rain" in text or "drizzle" in text:
        return "🌧"
    if "mist" in text or "fog" in text or "haze" in text:
        return "🌫"
    if "few clouds" in text:
        return "🌤"
    if "cloud" in text:
        return "☁️"
    if "clear" in text:
        return "☀️"
    return "🌡"


def _missing_api_key_error() -> dict[str, Any]:
    return {
        "success": False,
        "error": (
            "Weather lookups are not available right now because the weather "
            "service is not configured."
        ),
    }


def _missing_city_error() -> dict[str, Any]:
    return {
        "success": False,
        "error": (
            "I'd be happy to check the weather for you. "
            "Which city would you like me to look up? "
            "For example: \"Weather in Delhi\"."
        ),
    }


def _city_not_found_error(city: str) -> dict[str, Any]:
    return {
        "success": False,
        "error": (
            f'Sorry, I couldn\'t find weather information for "{city}".\n\n'
            "Please check the spelling or try another city."
        ),
    }


def _api_unreachable_error() -> dict[str, Any]:
    return {
        "success": False,
        "error": (
            "I couldn't reach the weather service right now. "
            "Please try again in a moment."
        ),
    }


def _unexpected_api_error() -> dict[str, Any]:
    return {
        "success": False,
        "error": (
            "The weather service returned an unexpected response. "
            "Please try again later."
        ),
    }


def _invalid_api_response_error() -> dict[str, Any]:
    return {
        "success": False,
        "error": "I received an invalid response from the weather service.",
    }


def _call_openweather(url: str, city: str) -> tuple[dict[str, Any] | None, str | None]:
    """
    Call OpenWeatherMap and return (payload, error_message).

  Logs request metadata and response time.
    """
    api_key = settings.OPENWEATHER_API_KEY
    cleaned_city = (city or "").strip()
    endpoint = "forecast" if "forecast" in url else "current"

    if not api_key:
        logger.warning("weather_api_skipped reason=missing_api_key city=%s", cleaned_city)
        return None, _missing_api_key_error()["error"]

    if not cleaned_city:
        return None, _missing_city_error()["error"]

    params = {"q": cleaned_city, "appid": api_key, "units": "metric"}
    started = time.perf_counter()

    logger.info(
        "weather_api_request endpoint=%s city=%s",
        endpoint,
        cleaned_city,
    )

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.Timeout:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.error(
            "weather_api_failure endpoint=%s city=%s reason=timeout elapsed_ms=%.1f",
            endpoint,
            cleaned_city,
            elapsed_ms,
        )
        return None, _api_unreachable_error()["error"]
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.error(
            "weather_api_failure endpoint=%s city=%s reason=%s elapsed_ms=%.1f",
            endpoint,
            cleaned_city,
            exc,
            elapsed_ms,
        )
        return None, _api_unreachable_error()["error"]

    elapsed_ms = (time.perf_counter() - started) * 1000

    if response.status_code == 404:
        logger.warning(
            "weather_api_failure endpoint=%s city=%s status=404 elapsed_ms=%.1f",
            endpoint,
            cleaned_city,
            elapsed_ms,
        )
        return None, _city_not_found_error(cleaned_city)["error"]

    if response.status_code != 200:
        logger.error(
            "weather_api_failure endpoint=%s city=%s status=%s elapsed_ms=%.1f",
            endpoint,
            cleaned_city,
            response.status_code,
            elapsed_ms,
        )
        return None, _unexpected_api_error()["error"]

    try:
        data = response.json()
    except ValueError:
        logger.error(
            "weather_api_failure endpoint=%s city=%s reason=invalid_json elapsed_ms=%.1f",
            endpoint,
            cleaned_city,
            elapsed_ms,
        )
        return None, _invalid_api_response_error()["error"]

    if not data:
        logger.error(
            "weather_api_failure endpoint=%s city=%s reason=empty_payload elapsed_ms=%.1f",
            endpoint,
            cleaned_city,
            elapsed_ms,
        )
        return None, _unexpected_api_error()["error"]

    logger.info(
        "weather_api_success endpoint=%s city=%s elapsed_ms=%.1f",
        endpoint,
        cleaned_city,
        elapsed_ms,
    )
    return data, None


def get_weather(city: str) -> dict[str, Any]:
    """
    Fetch current weather for a city from OpenWeatherMap.

    Returns structured fields or a friendly error — never raises.
    """
    cleaned_city = (city or "").strip()
    if not settings.OPENWEATHER_API_KEY:
        return _missing_api_key_error()
    if not cleaned_city:
        return _missing_city_error()

    data, error = _call_openweather(OPENWEATHER_CURRENT_URL, cleaned_city)
    if error:
        return {"success": False, "error": error}

    main = data.get("main") or {}
    wind = data.get("wind") or {}
    weather_list = data.get("weather") or [{}]
    weather_entry = weather_list[0]
    condition = weather_entry.get("description", "Unknown").title()
    main_group = weather_entry.get("main", "")
    sys_data = data.get("sys") or {}

    return {
        "success": True,
        "endpoint": "current",
        "city": data.get("name", cleaned_city),
        "country": sys_data.get("country", ""),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "weather_condition": condition,
        "weather_main": main_group,
        "humidity": main.get("humidity"),
        "wind_speed": wind.get("speed"),
        "pressure": main.get("pressure"),
    }


def get_forecast(city: str) -> dict[str, Any]:
    """Fetch 5-day / 3-hour forecast for a city."""
    cleaned_city = (city or "").strip()
    if not settings.OPENWEATHER_API_KEY:
        return _missing_api_key_error()
    if not cleaned_city:
        return _missing_city_error()

    data, error = _call_openweather(OPENWEATHER_FORECAST_URL, cleaned_city)
    if error:
        return {"success": False, "error": error}

    city_info = data.get("city") or {}
    entries = data.get("list") or []
    if not entries:
        return {
            "success": False,
            "error": (
                f"Forecast data is unavailable for \"{cleaned_city}\" right now. "
                "Please try again later."
            ),
        }

    return {
        "success": True,
        "endpoint": "forecast",
        "city": city_info.get("name", cleaned_city),
        "country": city_info.get("country", ""),
        "entries": entries,
    }


def _parse_forecast_dt(entry: dict[str, Any]) -> datetime | None:
    dt_txt = entry.get("dt_txt")
    if not dt_txt:
        return None
    try:
        return datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _is_rain_entry(entry: dict[str, Any]) -> bool:
    weather_list = entry.get("weather") or [{}]
    main_group = weather_list[0].get("main", "")
    return main_group in _RAIN_WEATHER_MAINS


def _time_of_day_label(hour: int) -> str:
    if hour < 12:
        return "this morning"
    if hour < 17:
        return "this afternoon"
    return "this evening"


def analyze_rain_forecast(
    forecast: dict[str, Any],
    *,
    target: Literal["today", "tomorrow"],
) -> dict[str, Any]:
    """Determine whether rain is expected on the target day."""
    if not forecast.get("success"):
        return forecast

    entries = forecast.get("entries") or []
    today = date.today()
    target_day = today if target == "today" else today + timedelta(days=1)

    rain_slots: list[datetime] = []
    for entry in entries:
        dt = _parse_forecast_dt(entry)
        if not dt or dt.date() != target_day:
            continue
        if _is_rain_entry(entry):
            rain_slots.append(dt)

    city = forecast.get("city", "Unknown")
    country = forecast.get("country", "")
    location = f"{city}, {country}" if country else city
    day_label = "today" if target == "today" else "tomorrow"

    if not rain_slots:
        message = f"🌧 Rain is not expected {day_label} in {location}."
    else:
        timing = _time_of_day_label(rain_slots[0].hour)
        if target == "tomorrow":
            message = f"🌧 Rain is likely tomorrow in {location}."
        else:
            message = f"🌧 Rain is likely {timing} in {location}."

    return {
        "success": True,
        "endpoint": "forecast",
        "city": city,
        "country": country,
        "rain_expected": bool(rain_slots),
        "weather_condition": "Rain" if rain_slots else "No Rain",
        "message": message,
    }


def format_weather_message(result: dict[str, Any]) -> str:
    """Format current weather, forecast rain outlook, or errors for the agent."""
    if not result.get("success"):
        return result.get("error", "Weather information is unavailable.")

    if result.get("message"):
        return result["message"]

    city = result.get("city", "Unknown")
    country = result.get("country", "")
    location = f"{city}, {country}" if country else city
    condition = result.get("weather_condition", "Unknown")
    main_group = result.get("weather_main", "")
    emoji = condition_to_emoji(condition, main_group)

    temp = result.get("temperature")
    feels = result.get("feels_like")
    humidity = result.get("humidity")
    wind = result.get("wind_speed")
    pressure = result.get("pressure")

    lines = [
        f"📍 Weather for {location}",
        "",
        f"{emoji} Condition: {condition}",
    ]

    if temp is not None:
        lines.append(f"🌡 Temperature: {round(temp)}°C")
    if feels is not None:
        lines.append(f"🤒 Feels Like: {round(feels)}°C")
    if humidity is not None:
        lines.append(f"💧 Humidity: {humidity}%")
    if wind is not None:
        lines.append(f"🌬 Wind: {wind} m/s")
    if pressure is not None:
        lines.append(f"📈 Pressure: {pressure} hPa")

    return "\n".join(lines)


def fetch_weather_for_intent(city: str, intent: WeatherIntent) -> dict[str, Any]:
    """Call the appropriate OpenWeather endpoint for the detected intent."""
    if intent == "current":
        return get_weather(city)

    forecast = get_forecast(city)
    if not forecast.get("success"):
        return forecast

    target = "tomorrow" if intent == "rain_tomorrow" else "today"
    return analyze_rain_forecast(forecast, target=target)


def process_weather_query(
    message: str,
    conversation_history: list[dict] | None = None,
) -> dict[str, Any]:
    """
    End-to-end weather handling for graph nodes.

    Resolves city + intent, calls the correct API, and returns a formatted message.
    """
    intent = detect_weather_intent(message)
    city = resolve_city(message, conversation_history)

    if not city:
        error = _missing_city_error()
        return {
            "success": False,
            "intent": intent,
            "city": None,
            "endpoint": None,
            "formatted": error["error"],
            "error": error["error"],
        }

    result = fetch_weather_for_intent(city, intent)
    formatted = format_weather_message(result)

    return {
        "success": result.get("success", False),
        "intent": intent,
        "city": city,
        "endpoint": result.get("endpoint"),
        "formatted": formatted,
        "error": result.get("error"),
        "raw": result,
    }


def execute_weather_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch get_weather for LangGraph router tool execution."""
    message = args.get("message", "")
    city = args.get("city") or extract_city_from_message(message) or ""
    history = args.get("conversation_history") or []

    if not city:
        city = extract_city_from_history(history) or ""

    if not city:
        return _missing_city_error()

    intent = detect_weather_intent(message) if message else "current"
    result = fetch_weather_for_intent(city, intent)
    payload = dict(result)
    payload["formatted"] = format_weather_message(result)
    return payload
