"""Constants for the Untappd integration."""

from datetime import timedelta

DOMAIN = "untappd"

CONF_USERNAME = "username"
CONF_SCAN_INTERVAL = "scan_interval"

BASE_URL = "https://untappd.com"
USER_AGENT = "Mozilla/5.0 (compatible; HomeAssistant-Untappd/0.1; personal use)"

# Untappd closed its public API, so this reads the public profile page.
# Keep the interval gentle.
DEFAULT_SCAN_INTERVAL = 30  # minutes
MIN_SCAN_INTERVAL = 15  # minutes
UPDATE_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL)

EVENT_NEW_CHECKIN = "new_checkin"

CONF_COOKIE = "cookie"
CONF_USER_AGENT = "user_agent"

# Only used with a session cookie (logged-in beer history).
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)
FULL_SYNC_INTERVAL = timedelta(hours=24)
PAGE_DELAY = 1.5  # seconds between beer-history pages
MAX_PAGES = 200

# Poll faster in the evening, when check-ins usually happen.
CONF_HAPPY_INTERVAL = "happy_hour_interval"
CONF_HAPPY_START = "happy_hour_start"
CONF_HAPPY_END = "happy_hour_end"
DEFAULT_HAPPY_INTERVAL = 15  # minutes
DEFAULT_HAPPY_START = "17:00:00"
DEFAULT_HAPPY_END = "01:00:00"
