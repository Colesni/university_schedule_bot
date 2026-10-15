import logging
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class ScheduleSource:
    def fetch(self) -> bytes:
        raise NotImplementedError


class PublicExportScheduleSource(ScheduleSource):
    def __init__(self, url: str, timeout: int = 30):
        if not url:
            raise ValueError("Schedule source URL is required")
        self.url = url
        self.timeout = timeout

    def fetch(self) -> bytes:
        parsed = urlparse(self.url)
        if parsed.scheme in ("http", "https"):
            request = Request(self.url, headers={"User-Agent": "university-schedule-bot/1.0"})
            with urlopen(request, timeout=self.timeout) as response:
                data = response.read()
        elif parsed.scheme == "file":
            data = Path(parsed.path).read_bytes()
        else:
            data = Path(self.url).read_bytes()
        if not data:
            raise ValueError("Schedule source returned an empty file")
        return data
