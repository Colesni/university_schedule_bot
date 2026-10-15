import logging
import zipfile

from openpyxl.utils.exceptions import InvalidFileException
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.handlers import BotHandlers
from database.repository import UserGroupRepository
from config import load_settings
from schedule.cache import ScheduleCache
from schedule.parser import parse_workbook
from schedule.service import ScheduleService
from schedule.source import PublicExportScheduleSource
from utils.logging_config import configure_logging

logger = logging.getLogger(__name__)


def load_schedule(settings, cache: ScheduleCache) -> list:
    if not settings.schedule_source_url:
        logger.warning("SCHEDULE_SOURCE_URL is not configured; using cache")
        return cache.entries
    try:
        entries = parse_workbook(PublicExportScheduleSource(settings.schedule_source_url).fetch())
        if not entries:
            raise ValueError("schedule parser returned no valid entries")
        cache.replace(entries)
        logger.info("Schedule refreshed: %s valid entries", len(entries))
    except (OSError, ValueError, KeyError, UnicodeDecodeError, InvalidFileException, zipfile.BadZipFile):
        logger.exception("Schedule refresh failed; keeping the last valid cache")
    return cache.entries


def build_application() -> Application:
    settings = load_settings()
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not configured")
    configure_logging()
    cache = ScheduleCache()
    entries = load_schedule(settings, cache)
    service = ScheduleService(entries, settings.timezone)
    repository = UserGroupRepository()
    handlers = BotHandlers(service, repository)
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text))

    async def refresh_job(context) -> None:
        refreshed = load_schedule(settings, cache)
        service.update_entries(refreshed)

    application.job_queue.run_repeating(
        refresh_job,
        interval=settings.schedule_refresh_hours * 60 * 60,
        first=settings.schedule_refresh_hours * 60 * 60,
    )
    return application


if __name__ == "__main__":
    build_application().run_polling()
