"""In-memory agent status tracking for real-time status display."""
from datetime import UTC, datetime

_status: dict[str, dict] = {}


def update_status(nickname: str, status: str) -> None:
    _status[nickname] = {
        "status": status,
        "updated_at": datetime.now(UTC).isoformat(),
    }


def get_status(nickname: str) -> dict:
    return _status.get(nickname, {"status": "idle", "updated_at": None})


def get_all_statuses() -> dict[str, dict]:
    return dict(_status)
