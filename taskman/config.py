import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".taskman" / "config.json"

DEFAULTS = {
    "calendars": [
        {"id": "7685t2hrfacfa1q5hua5bjs4sta7e3a3@import.calendar.google.com", "color": "#33B679"},
        {"id": "yamacyurtsever123@gmail.com", "color": "#B39DDB"},
        {"id": "2c7b10fca87309698fede1d408db29f4527ef0becbae33f5b18108a16cb46516@group.calendar.google.com", "color": "#E67C73"},
    ],
    "calendarTimezone": "UTC",
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(DEFAULTS, indent=2))
        return dict(DEFAULTS)
    data = json.loads(CONFIG_PATH.read_text())
    return {**DEFAULTS, **data}
