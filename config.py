import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    schedule_source_url: str
    timezone: str = "Europe/Chisinau"
    schedule_refresh_hours: int = 72


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        schedule_source_url=os.getenv("SCHEDULE_SOURCE_URL", ""),
        timezone=os.getenv("TIMEZONE", "Europe/Chisinau"),
        schedule_refresh_hours=int(os.getenv("SCHEDULE_REFRESH_HOURS", "72")),
    )
