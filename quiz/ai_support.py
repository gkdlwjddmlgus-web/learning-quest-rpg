from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Any, Callable, TypeVar

from quiz.repository import get_connection, initialize_database

T = TypeVar("T")

CACHE_VERSION = "v1"
QUOTA_COOLDOWN_MINUTES = 5


class AIServiceError(RuntimeError):
    """사용자에게 그대로 보여줘도 되는 AI 서비스 오류."""


class AIQuotaError(AIServiceError):
    """Gemini 429 / quota 초과 오류."""


def initialize_ai_support() -> None:
    initialize_database()
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_cache (
                cache_key TEXT PRIMARY KEY,
                cache_kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                hit_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_runtime_state (
                state_key TEXT PRIMARY KEY,
                state_value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def make_cache_key(cache_kind: str, payload: Any) -> str:
    raw = f"{CACHE_VERSION}|{cache_kind}|{_canonical(payload)}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{cache_kind}:{digest}"


def get_cached_json(cache_kind: str, key_payload: Any) -> dict[str, Any] | list[Any] | None:
    initialize_ai_support()
    cache_key = make_cache_key(cache_kind, key_payload)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT payload FROM ai_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            """
            UPDATE ai_cache
            SET hit_count = hit_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE cache_key = ?
            """,
            (cache_key,),
        )
        connection.commit()
    try:
        return json.loads(row["payload"])
    except (TypeError, json.JSONDecodeError):
        return None


def set_cached_json(cache_kind: str, key_payload: Any, payload: Any) -> None:
    initialize_ai_support()
    cache_key = make_cache_key(cache_kind, key_payload)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_cache (cache_key, cache_kind, payload, hit_count)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (cache_key, cache_kind, json.dumps(payload, ensure_ascii=False)),
        )
        connection.commit()


def _set_state(key: str, value: str) -> None:
    initialize_ai_support()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_runtime_state (state_key, state_value)
            VALUES (?, ?)
            ON CONFLICT(state_key) DO UPDATE SET
                state_value = excluded.state_value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        connection.commit()


def _get_state(key: str) -> str | None:
    initialize_ai_support()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT state_value FROM ai_runtime_state WHERE state_key = ?",
            (key,),
        ).fetchone()
    return None if row is None else str(row["state_value"])


def _quota_blocked_until() -> datetime | None:
    value = _get_state("gemini_quota_blocked_until")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _set_quota_cooldown(minutes: int = QUOTA_COOLDOWN_MINUTES) -> None:
    blocked_until = datetime.now() + timedelta(minutes=minutes)
    _set_state("gemini_quota_blocked_until", blocked_until.isoformat(timespec="seconds"))


def clear_quota_cooldown() -> None:
    _set_state("gemini_quota_blocked_until", "")


def is_quota_error(error: Exception) -> bool:
    text = str(error).lower()
    markers = (
        "429",
        "resource_exhausted",
        "quota exceeded",
        "free_tier_requests",
        "generaterequestsperday",
    )
    return any(marker in text for marker in markers)


def _extract_retry_seconds(error: Exception) -> int | None:
    text = str(error)
    patterns = [
        r"retry(?:delay| in)?['\"\s:]*([0-9]+(?:\.[0-9]+)?)s",
        r"retryDelay['\"\s:]*['\"]?([0-9]+(?:\.[0-9]+)?)s",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return max(1, int(float(match.group(1))))
            except ValueError:
                pass
    return None


def friendly_ai_error(error: Exception) -> str:
    if isinstance(error, AIServiceError):
        return str(error)

    if is_quota_error(error):
        retry = _extract_retry_seconds(error)
        if "perday" in str(error).lower() or "free_tier_requests" in str(error).lower():
            return (
                "오늘 사용할 수 있는 Gemini 무료 API 요청 한도에 도달했습니다. "
                "이미 생성된 월드와 저장된 문제는 계속 사용할 수 있습니다. "
                "무료 한도가 갱신된 뒤 다시 생성해 주세요."
            )
        if retry:
            return f"Gemini 요청 한도에 잠시 도달했습니다. 약 {retry}초 뒤 다시 시도해 주세요."
        return "Gemini 요청 한도에 잠시 도달했습니다. 잠시 뒤 다시 시도해 주세요."

    text = str(error).strip()
    if not text:
        return "AI 요청 중 알 수 없는 오류가 발생했습니다."
    return f"AI 요청 중 오류가 발생했습니다: {text}"


def call_gemini(call: Callable[[], T]) -> T:
    blocked_until = _quota_blocked_until()
    now = datetime.now()
    if blocked_until and now < blocked_until:
        remaining = max(1, int((blocked_until - now).total_seconds() // 60) + 1)
        raise AIQuotaError(
            f"Gemini 요청 한도를 보호하기 위해 약 {remaining}분 동안 추가 API 호출을 잠시 막았습니다. "
            "저장된 월드와 문제은행은 계속 이용할 수 있습니다."
        )

    try:
        result = call()
        clear_quota_cooldown()
        return result
    except Exception as exc:
        if is_quota_error(exc):
            _set_quota_cooldown()
            raise AIQuotaError(friendly_ai_error(exc)) from exc
        raise AIServiceError(friendly_ai_error(exc)) from exc
