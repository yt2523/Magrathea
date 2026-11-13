import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

class DailyLimitExceeded(Exception):
    pass

class BudgetStateError(Exception):
    pass

DEFAULT_LEDGER_PATH = "D:/Codex/usage/deepseek-daily.json"
LINUX_MAPPED_PATH = "/mnt/d/Codex/usage/deepseek-daily.json"
SCHEMA_VERSION = 1
DAILY_LIMIT = 100
TIMEZONE_NAME = "Europe/London"
LOCK_TIMEOUT = 2.0

def _get_default_ledger_path():
    if os.name == 'nt':
        return DEFAULT_LEDGER_PATH
    else:
        return LINUX_MAPPED_PATH

def _load_timezone():
    try:
        return ZoneInfo(TIMEZONE_NAME)
    except ZoneInfoNotFoundError:
        tzif_path = Path(__file__).parent / 'data' / 'Europe_London.tzif'
        try:
            with open(tzif_path, 'rb') as f:
                return ZoneInfo.from_file(f, key=TIMEZONE_NAME)
        except (OSError, ValueError) as e:
            raise BudgetStateError(f"Failed to load timezone data: {e}") from e

def _validate_ledger(data):
    if not isinstance(data, dict):
        raise BudgetStateError("Ledger root must be object")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise BudgetStateError("Invalid schema_version")
    if data.get("timezone") != TIMEZONE_NAME:
        raise BudgetStateError("Invalid timezone")
    if data.get("daily_limit") != DAILY_LIMIT:
        raise BudgetStateError("Invalid daily_limit")
    days = data.get("days")
    if not isinstance(days, dict):
        raise BudgetStateError("days must be object")
    for date, entry in days.items():
        if not isinstance(date, str) or len(date) != 10:
            raise BudgetStateError("Invalid date key")
        if not isinstance(entry, dict):
            raise BudgetStateError("Day entry must be object")
        used = entry.get("used")
        if not isinstance(used, int) or isinstance(used, bool) or used < 0:
            raise BudgetStateError("Invalid used value")
    events = data.get("events")
    if not isinstance(events, list):
        raise BudgetStateError("events must be list")
    return True

def _acquire_lock(lock_dir):
    deadline = time.monotonic() + LOCK_TIMEOUT
    while True:
        try:
            Path(lock_dir).mkdir(exist_ok=False)
            return
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise BudgetStateError("Lock acquisition timed out")
            time.sleep(0.01)
        except OSError as e:
            raise BudgetStateError(f"Failed to acquire lock: {e}")


def _release_lock(lock_dir: Path):
    try:
        lock_dir.rmdir()
    except FileNotFoundError:
        pass

def reserve_call(ledger_path=None, now_utc=None):
    if ledger_path is None:
        ledger_path = _get_default_ledger_path()
    ledger_path = Path(ledger_path)
    lock_dir = Path(str(ledger_path) + ".lock")
    _acquire_lock(lock_dir)
    try:
        if not ledger_path.exists():
            raise BudgetStateError("Ledger file missing")
        try:
            with open(ledger_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            raise BudgetStateError("Ledger corrupt or unreadable")
        _validate_ledger(data)
        tz = _load_timezone()
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        if now_utc.tzinfo is None or now_utc.utcoffset() is None:
            raise BudgetStateError("now_utc must be timezone-aware")
        local_now = now_utc.astimezone(tz)
        date_str = local_now.strftime("%Y-%m-%d")
        days = data["days"]
        if date_str not in days:
            days[date_str] = {"used": 0}
        used = days[date_str]["used"]
        if used >= DAILY_LIMIT:
            raise DailyLimitExceeded(f"Daily limit reached for {date_str}")
        days[date_str]["used"] = used + 1
        event = {
            "utc_time": now_utc.isoformat(),
            "pid": os.getpid(),
            "day": date_str
        }
        data["events"].append(event)
        tmp_path = ledger_path.parent / f".{ledger_path.name}.{uuid.uuid4().hex}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, ledger_path)
        return {
            "date": date_str,
            "used": days[date_str]["used"],
            "limit": DAILY_LIMIT,
            "remaining": DAILY_LIMIT - days[date_str]["used"]
        }
    finally:
        _release_lock(lock_dir)
