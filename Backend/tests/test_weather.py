"""Tests for the OpenWeatherMap weather service and LangGraph weather routing."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes import classify_route_node, weather_node
from app.graph.routing import _classify_query_mode_fallback
from app.services.weather_service import (
    analyze_rain_forecast,
    condition_to_emoji,
    detect_weather_intent,
    extract_city_from_history,
    extract_city_from_message,
    fetch_weather_for_intent,
    format_weather_message,
    get_forecast,
    get_weather,
    is_weather_request,
    process_weather_query,
    resolve_city,
)


MOCK_WEATHER_RESPONSE = {
    "name": "Delhi",
    "sys": {"country": "IN"},
    "main": {
        "temp": 32.5,
        "feels_like": 35.0,
        "humidity": 55,
        "pressure": 1012,
    },
    "wind": {"speed": 3.2},
    "weather": [{"description": "clear sky", "main": "Clear"}],
}


def _forecast_entry(day: date, hour: int, main: str = "Clouds") -> dict:
    return {
        "dt_txt": f"{day.isoformat()} {hour:02d}:00:00",
        "weather": [{"main": main, "description": main.lower()}],
    }


MOCK_FORECAST_RESPONSE = {
    "city": {"name": "Indore", "country": "IN"},
    "list": [
        _forecast_entry(date.today(), 15, "Clouds"),
        _forecast_entry(date.today(), 18, "Rain"),
        _forecast_entry(date.today() + timedelta(days=1), 12, "Clouds"),
    ],
}


# --- Intent detection ---


def test_is_weather_request_detects_weather_prompts():
    assert is_weather_request("What's the weather in Delhi?")
    assert is_weather_request("Temperature in Bangalore")
    assert is_weather_request("Will it rain today?")
    assert is_weather_request("How hot is Bangalore?")
    assert is_weather_request("Is it sunny in Pune?")
    assert is_weather_request("Humidity in Jaipur")
    assert is_weather_request("Wind speed in Kolkata")
    assert not is_weather_request("What is your return policy?")


def test_detect_weather_intent():
    assert detect_weather_intent("Weather in Delhi") == "current"
    assert detect_weather_intent("Will it rain today?") == "rain_today"
    assert detect_weather_intent("Will it rain tomorrow in Chennai?") == "rain_tomorrow"
    assert detect_weather_intent("Forecast for Indore") == "rain_today"
    assert detect_weather_intent("Weather later today in Mumbai") == "rain_today"


def test_extract_city_from_message():
    assert extract_city_from_message("Weather in Mumbai") == "Mumbai"
    assert extract_city_from_message("What is the temperature in Bangalore?") == "Bangalore"
    assert extract_city_from_message("Forecast for Indore") == "Indore"
    assert extract_city_from_message("How hot is Bangalore?") == "Bangalore"
    assert extract_city_from_message("Is it sunny in Pune?") == "Pune"
    assert extract_city_from_message("Humidity in Jaipur") == "Jaipur"
    assert extract_city_from_message("Wind speed in Kolkata") == "Kolkata"
    assert extract_city_from_message("Will it rain tomorrow in Chennai?") == "Chennai"
    assert extract_city_from_message("Will it rain today?") is None


def test_resolve_city_from_conversation_history():
    history = [
        {"role": "user", "parts": ["Weather in Indore"]},
        {
            "role": "assistant",
            "parts": ["📍 Weather for Indore\n\n☁️ Condition: Clouds"],
        },
    ]
    assert resolve_city("Will it rain today?", history) == "Indore"


def test_extract_city_from_history_formatted_response():
    history = [
        {
            "role": "assistant",
            "parts": ["📍 Weather for Mumbai\n\n🌧 Condition: Rain"],
        },
    ]
    assert extract_city_from_history(history) == "Mumbai"


# --- Current weather API ---


@patch("app.services.weather_service.settings.OPENWEATHER_API_KEY", "test-key")
@patch("app.services.weather_service.requests.get")
def test_get_weather_valid_city(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_WEATHER_RESPONSE
    mock_get.return_value = mock_response

    result = get_weather("Delhi")

    assert result["success"] is True
    assert result["endpoint"] == "current"
    assert result["city"] == "Delhi"
    assert result["country"] == "IN"
    assert result["temperature"] == 32.5
    assert result["weather_condition"] == "Clear Sky"
    mock_get.assert_called_once()
    assert "forecast" not in mock_get.call_args[0][0]


@patch("app.services.weather_service.settings.OPENWEATHER_API_KEY", "test-key")
@patch("app.services.weather_service.requests.get")
def test_get_weather_invalid_city(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_weather("Chennnai")

    assert result["success"] is False
    assert "Chennnai" in result["error"]
    assert "spelling" in result["error"].lower()


@patch("app.services.weather_service.settings.OPENWEATHER_API_KEY", "")
def test_get_weather_missing_api_key():
    result = get_weather("Delhi")

    assert result["success"] is False
    assert "not configured" in result["error"].lower()


@patch("app.services.weather_service.settings.OPENWEATHER_API_KEY", "test-key")
@patch("app.services.weather_service.requests.get")
def test_get_weather_api_failure(mock_get):
    import requests

    mock_get.side_effect = requests.RequestException("network down")

    result = get_weather("Delhi")

    assert result["success"] is False
    assert "couldn't reach" in result["error"].lower()


# --- Forecast API ---


@patch("app.services.weather_service.settings.OPENWEATHER_API_KEY", "test-key")
@patch("app.services.weather_service.requests.get")
def test_get_forecast_valid_city(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_FORECAST_RESPONSE
    mock_get.return_value = mock_response

    result = get_forecast("Indore")

    assert result["success"] is True
    assert result["endpoint"] == "forecast"
    assert result["city"] == "Indore"
    assert len(result["entries"]) == 3
    assert "forecast" in mock_get.call_args[0][0]


def test_analyze_rain_forecast_rain_expected_today():
    forecast = {
        "success": True,
        "city": "Indore",
        "country": "IN",
        "entries": MOCK_FORECAST_RESPONSE["list"],
    }
    result = analyze_rain_forecast(forecast, target="today")

    assert result["success"] is True
    assert result["rain_expected"] is True
    assert "likely" in result["message"].lower()


def test_analyze_rain_forecast_no_rain_today():
    forecast = {
        "success": True,
        "city": "Indore",
        "country": "IN",
        "entries": [_forecast_entry(date.today(), 12, "Clear")],
    }
    result = analyze_rain_forecast(forecast, target="today")

    assert result["success"] is True
    assert result["rain_expected"] is False
    assert "not expected" in result["message"].lower()


@patch("app.services.weather_service.get_forecast")
def test_fetch_weather_for_intent_uses_forecast_for_rain(mock_forecast):
    mock_forecast.return_value = {
        "success": True,
        "city": "Delhi",
        "country": "IN",
        "entries": [_forecast_entry(date.today(), 12, "Clear")],
    }

    result = fetch_weather_for_intent("Delhi", "rain_today")

    mock_forecast.assert_called_once_with("Delhi")
    assert result["success"] is True
    assert "not expected" in result["message"].lower()


# --- Formatting ---


def test_condition_to_emoji_mapping():
    assert condition_to_emoji("clear sky", "Clear") == "☀️"
    assert condition_to_emoji("broken clouds", "Clouds") == "☁️"
    assert condition_to_emoji("few clouds", "Clouds") == "🌤"
    assert condition_to_emoji("light rain", "Rain") == "🌧"
    assert condition_to_emoji("thunderstorm", "Thunderstorm") == "⛈"
    assert condition_to_emoji("snow", "Snow") == "❄️"
    assert condition_to_emoji("mist", "Mist") == "🌫"


def test_format_weather_message_current():
    message = format_weather_message(
        {
            "success": True,
            "city": "Indore",
            "country": "IN",
            "temperature": 32,
            "feels_like": 34,
            "weather_condition": "Broken Clouds",
            "weather_main": "Clouds",
            "humidity": 44,
            "wind_speed": 8.3,
            "pressure": 1003,
        }
    )
    assert "📍 Weather for Indore" in message
    assert "☁️ Condition: Broken Clouds" in message
    assert "🌡 Temperature: 32°C" in message
    assert "🤒 Feels Like: 34°C" in message
    assert "💧 Humidity: 44%" in message
    assert "🌬 Wind: 8.3 m/s" in message
    assert "📈 Pressure: 1003 hPa" in message


def test_format_weather_message_rain_outlook():
    message = format_weather_message(
        {
            "success": True,
            "message": "🌧 Rain is not expected today in Indore, IN.",
        }
    )
    assert "Rain is not expected" in message


def test_process_weather_query_missing_city():
    result = process_weather_query("Will it rain today?", [])

    assert result["success"] is False
    assert result["city"] is None
    assert "which city" in result["formatted"].lower()


@patch("app.services.weather_service.fetch_weather_for_intent")
def test_process_weather_query_with_history(mock_fetch):
    mock_fetch.return_value = {
        "success": True,
        "endpoint": "forecast",
        "message": "🌧 Rain is likely this evening in Indore, IN.",
    }
    history = [{"role": "user", "parts": ["Weather in Indore"]}]

    result = process_weather_query("Will it rain today?", history)

    assert result["success"] is True
    assert result["city"] == "Indore"
    mock_fetch.assert_called_once_with("Indore", "rain_today")


# --- LangGraph routing / node ---


def test_weather_routing_fallback():
    state = {"user_message": "What's the weather in Delhi?"}
    result = _classify_query_mode_fallback(state, active_doc=None, compare_ids=[])
    assert result["query_mode"] == "weather"


@pytest.mark.asyncio
@patch("app.graph.nodes.classify_query_mode_llm", new_callable=AsyncMock)
async def test_classify_route_detects_weather(mock_classify):
    mock_classify.return_value = {
        "query_mode": "multi_document",
        "compare_document_ids": [],
        "metadata_action": None,
    }

    result = await classify_route_node(
        {
            "user_message": "Weather in Mumbai",
            "user_id": "user-1",
            "conversation_history": [],
        }
    )

    assert result["query_mode"] == "weather"
    assert result["route"] == "weather"


@pytest.mark.asyncio
@patch("app.graph.nodes.classify_query_mode_llm", new_callable=AsyncMock)
async def test_classify_route_forced_weather_mode(mock_classify):
    mock_classify.return_value = {
        "query_mode": "normal_chat",
        "compare_document_ids": [],
        "metadata_action": None,
    }

    result = await classify_route_node(
        {
            "user_message": "Hello",
            "user_id": "user-1",
            "conversation_history": [],
            "force_query_mode": "weather",
        }
    )

    assert result["query_mode"] == "weather"


@pytest.mark.asyncio
@patch("app.graph.nodes.process_weather_query")
async def test_weather_node_execution(mock_process):
    mock_process.return_value = {
        "success": True,
        "city": "Delhi",
        "endpoint": "current",
        "formatted": "📍 Weather for Delhi, IN\n\n☀️ Condition: Clear",
    }

    result = await weather_node(
        {
            "user_message": "What is the weather in Delhi?",
            "contents": [],
            "tool_calls_made": [],
            "conversation_history": [],
        }
    )

    assert result["query_mode"] == "weather"
    assert result["route"] == "router"
    assert len(result["tool_calls_made"]) == 1
    mock_process.assert_called_once()
    assert any("Weather for Delhi" in c.get("parts", [""])[0] for c in result["contents"])


@pytest.mark.asyncio
@patch("app.graph.nodes.process_weather_query")
async def test_weather_node_missing_city(mock_process):
    mock_process.return_value = {
        "success": False,
        "city": None,
        "endpoint": None,
        "formatted": "Which city would you like me to look up?",
    }

    result = await weather_node(
        {
            "user_message": "Will it rain today?",
            "contents": [],
            "tool_calls_made": [],
            "conversation_history": [],
        }
    )

    assert result["query_mode"] == "weather"
    assert result["route"] == "router"
    assert result["tool_calls_made"] == []
    assert any("Which city" in c.get("parts", [""])[0] for c in result["contents"])
