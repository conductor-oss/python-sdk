"""Deep agent — plan, delegate to a sub-agent, pause for approval, write a report.

A travel assistant that plans with write_todos, hands weather lookups to a
weather-analyst sub-agent, asks for approval before writing a file, and writes
its recommendation to report.md in the run's workspace.

Demonstrates:
    - deep_agent(): one call gives an Agent with planning, file tools and sub-agents
    - The plan lives in _agent_state, outside the conversation
    - A sub-agent with its own context, sharing the run's workspace
    - Human approval before write_file

Requirements:
    - Conductor server with LLM support
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api as environment variable
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini as environment variable
    - Network access to open-meteo.com for the weather tool
"""

import json
import urllib.parse
import urllib.request

from conductor.ai.agents import Agent, AgentRuntime, EventType, tool
from conductor.ai.agents.deep import deep_agent, workspace_dir
from settings import settings

_WMO = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    80: "light showers",
    81: "showers",
    82: "violent showers",
    95: "thunderstorm",
}


def _get_json(url: str, params: dict) -> dict:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=15) as resp:
        return json.load(resp)


@tool
def get_weather(city: str) -> str:
    """Get the current weather and a 7-day daily forecast for a city.

    Args:
        city: City name in any language, for example "Beijing" or "上海".
    """
    geo = _get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en"},
    )
    if not geo.get("results"):
        return f"City not found: {city}"
    place = geo["results"][0]
    fc = _get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 7,
        },
    )
    cur, daily = fc["current"], fc["daily"]
    lines = [
        f"{place['name']} ({place.get('admin1', '')}, {place.get('country', '')})",
        f"Now ({cur['time']}): {_WMO.get(cur['weather_code'], cur['weather_code'])}, "
        f"{cur['temperature_2m']}°C, wind {cur['wind_speed_10m']} km/h",
        "Next 7 days:",
    ]
    for i, day in enumerate(daily["time"]):
        lines.append(
            f"  {day}: {_WMO.get(daily['weather_code'][i], daily['weather_code'][i])}, "
            f"{daily['temperature_2m_min'][i]}~{daily['temperature_2m_max'][i]}°C, "
            f"precipitation {daily['precipitation_probability_max'][i]}%"
        )
    return "\n".join(lines)


# The sub-agent has its own context. It gets the file tools from deep_agent so
# it can write its full comparison to the shared workspace.
weather_analyst = Agent(
    name="weather_analyst",
    model=settings.llm_model,
    instructions=(
        "You are a weather analyst. Call get_weather for each city you are given. "
        "Write the full forecast for each city to weather-<city>.md in the workspace "
        "with write_file, then reply with a two-sentence summary and the file paths."
    ),
    tools=[get_weather],
    metadata={
        "description": "Looks up and compares the weather in several cities. Give it the full list of cities."
    },
)

agent = deep_agent(
    name="travel_planner",
    model=settings.llm_model,
    instructions=(
        "You are a travel assistant. Delegate all weather lookups to weather_analyst "
        "in one call with every city. Then write your recommendation to report.md "
        "and tell the user what you chose and why."
    ),
    subagents=[weather_analyst],
    workspace="./workspace",
    approval=["write_file"],
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        handle = runtime.start(
            agent,
            "I want to visit Beijing or Shanghai this weekend. Compare the weather and recommend one.",
        )
        print(f"Started: {handle.execution_id}\n")

        for event in handle.stream():
            if event.type == EventType.TOOL_CALL:
                print(f"  [tool_call] {event.tool_name}({str(event.args)[:120]})")
            elif event.type == EventType.TOOL_RESULT:
                print(f"  [tool_result] {event.tool_name} -> {str(event.result)[:120]}")
            elif event.type == EventType.WAITING:
                print("  [waiting] approving write_file")
                handle.approve()
            elif event.type == EventType.DONE:
                print(f"\nDone: {event.output}")

        ws = workspace_dir(handle.execution_id, "./workspace")
        report = ws / "report.md"
        print(f"\nWorkspace: {ws}")
        if report.exists():
            print("--- report.md ---")
            print(report.read_text())
