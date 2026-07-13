"""Gemini function declarations for weather tools."""

from google.genai import types

WEATHER_TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_weather",
        description=(
            "Get the current weather for a city including temperature, conditions, "
            "humidity, wind speed, and pressure. Use when the customer asks about "
            "weather, temperature, rain, or forecast for a location."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "city": types.Schema(
                    type=types.Type.STRING,
                    description="City name, e.g. Delhi, Mumbai, Bangalore",
                ),
            },
            required=["city"],
        ),
    ),
]
