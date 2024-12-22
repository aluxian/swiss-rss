from typing import Optional
from datetime import datetime, timezone
from loguru import logger


def parse_date(date_string: Optional[str]) -> Optional[datetime]:
    if not date_string:
        return None

    date_formats = [
        "%a, %d %b %Y %H:%M:%S %Z",  # RFC 822 format with timezone name
        "%a, %d %b %Y %H:%M:%S %z",  # RFC 822 format with numeric timezone
        "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 format
        "%Y-%m-%d %H:%M:%S%z",  # Alternative ISO-like format
    ]

    for date_format in date_formats:
        try:
            # Parse the date, assuming UTC if no timezone is specified
            dt = datetime.strptime(date_string, date_format)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except ValueError:
            continue

    # If all parsing attempts fail, try a more lenient approach for RFC 822
    try:
        return datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        logger.debug(f"Failed to parse date string: {date_string}")
        return None
