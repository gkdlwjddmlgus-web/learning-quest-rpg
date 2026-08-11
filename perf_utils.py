from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Iterator

import streamlit as st


def _context() -> str:
    try:
        user = str(st.session_state.get("auth_username", "-"))
        user_id = str(st.session_state.get("auth_user_id", "-"))
        view = str(st.session_state.get("game_view", "-"))
        return f"user={user} user_id={user_id} view={view}"
    except Exception:
        return "user=- user_id=- view=-"


def _emit(label: str, elapsed: float, status: str = "ok") -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    print(
        f"[PERF] {stamp} | {label:<36} | {elapsed:8.3f}s | "
        f"{status} | {_context()}",
        flush=True,
    )


def perf_log(label: str) -> Callable:
    """함수 전체 실행시간을 Streamlit Cloud 로그에 남긴다."""
    def decorator(func: Callable) -> Callable:
        if getattr(func, "_perf_wrapped", False):
            return func

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            started = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception:
                _emit(label, time.perf_counter() - started, "ERROR")
                raise

            _emit(label, time.perf_counter() - started, "ok")
            return result

        wrapper._perf_wrapped = True
        return wrapper

    return decorator


@contextmanager
def perf_block(label: str) -> Iterator[None]:
    """특정 코드 블록의 실행시간을 측정한다."""
    started = time.perf_counter()
    try:
        yield
    except Exception:
        _emit(label, time.perf_counter() - started, "ERROR")
        raise
    else:
        _emit(label, time.perf_counter() - started, "ok")
