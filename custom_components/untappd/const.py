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
