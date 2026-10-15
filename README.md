# University Schedule Telegram Bot

## Requirements

Python 3.11 or newer and a Telegram bot token. The schedule source must be a public XLSX/CSV export URL (or a local development file path).

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `TELEGRAM_BOT_TOKEN` and `SCHEDULE_SOURCE_URL` in `.env`. `SCHEDULE_SOURCE_URL` is the configurable Google Sheets export URL; it is never hardcoded. `TIMEZONE` defaults to `Europe/Chisinau` and `SCHEDULE_REFRESH_HOURS` defaults to `72`.

## Run

```powershell
python main.py
```

The bot discovers groups from the valid schedule, stores each user's selected group in SQLite, and keeps the last valid schedule in `schedule_cache.json`. Failed downloads or invalid schedules do not replace that cache.

## Tests

```powershell
pytest -q
```
