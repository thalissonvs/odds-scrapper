from datetime import datetime
from zoneinfo import ZoneInfo

import ua_generator


def get_random_user_agent() -> str:
    return ua_generator.generate(
        device=['desktop'],
        platform=['windows', 'linux', 'macos'],
        browser=['chrome', 'firefox', 'edge', 'safari'],
    ).text


def convert_to_utc(time_str: str) -> str:
    hour_eastern_time, period = time_str.split(' ')[:2]
    tz_et = ZoneInfo('America/New_York')  # ET = Eastern Time

    date_eastern_time = datetime.strptime(f'{hour_eastern_time} {period}', '%I:%M %p')
    date_eastern_time = date_eastern_time.replace(
        year=datetime.now().year,
        month=datetime.now().month,
        day=datetime.now().day,
        tzinfo=tz_et,
    )
    date_utc = date_eastern_time.astimezone(ZoneInfo('UTC'))
    return date_utc.isoformat().replace('+00:00', '+00:00')


def get_current_date() -> str:
    """Get the current date formatted as MM-DD-YYYY.

    Returns:
        str: Formatted current date
    """
    return datetime.now().strftime('%m-%d-%Y')
