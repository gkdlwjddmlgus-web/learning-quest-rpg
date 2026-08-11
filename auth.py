from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime
from typing import Any

import streamlit as st
import quiz.repository as repository


# 기존 단일 사용자 데이터는 이 ID에 저장되어 있다.
LEGACY_USER_ID = "local_player"

# 기존 밸런스 테스트 계정은 데이터 호환을 위해 유지한다.
# 화면에는 노출하지 않으며, 추후 회원가입 시스템 도입 시 제거 가능하다.
TEST_ACCOUNTS = (
    {"username": "high_test", "password": "high1234", "user_id": LEGACY_USER_ID, "tier": "HIGH", "display_name": "고레벨 테스트"},
    {"username": "mid_test", "password": "mid1234", "user_id": "mid_test_user", "tier": "MID", "display_name": "중레벨 테스트"},
    {"username": "low_test", "password": "low1234", "user_id": "low_test_user", "tier": "LOW", "display_name": "저레벨 테스트"},
)


def _connection():
    return repository.get_connection()


def initialize_auth_tables() -> None:
    with _connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_users (
                username TEXT PRIMARY KEY,
                user_key TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                display_name TEXT NOT NULL,
                test_tier TEXT NOT NULL DEFAULT 'LOW',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000,
    )
    return digest.hex(), salt.hex()


def bootstrap_test_users() -> None:
    """기존 HIGH/MID/LOW 테스트 계정 데이터를 유지한다."""
    initialize_auth_tables()
    with _connection() as conn:
        for account in TEST_ACCOUNTS:
            exists = conn.execute(
                "SELECT 1 FROM app_users WHERE username = ?",
                (account["username"],),
            ).fetchone()
            if exists:
                continue

            password_hash, salt_hex = _hash_password(account["password"])
            conn.execute(
                """
                INSERT INTO app_users (
                    username, user_key, password_hash, password_salt,
                    display_name, test_tier, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account["username"],
                    str(account["user_id"]),
                    password_hash,
                    salt_hex,
                    account["display_name"],
                    account["tier"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        conn.commit()


def _restore_user_id(username: str, stored_user_key: str) -> Any:
    """DB에 저장된 실제 사용자 키를 그대로 복원한다."""
    if stored_user_key is not None and str(stored_user_key).strip():
        return str(stored_user_key)

    if username == "high_test":
        return LEGACY_USER_ID

    return str(stored_user_key or "")


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    username = username.strip()

    if not username or not password:
        return None

    with _connection() as conn:
        row = conn.execute(
            """
            SELECT username, user_key, password_hash, password_salt,
                   display_name, test_tier
            FROM app_users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    if not row:
        return None

    digest, _ = _hash_password(password, row["password_salt"])
    if not hmac.compare_digest(digest, row["password_hash"]):
        return None

    return {
        "username": row["username"],
        "user_id": _restore_user_id(row["username"], row["user_key"]),
        "display_name": row["display_name"],
        "test_tier": row["test_tier"],
    }


def apply_runtime_user(user_id: Any) -> None:
    """기존 repository가 쓰는 LOCAL_USER_ID를 로그인 사용자로 전환한다."""
    repository.LOCAL_USER_ID = user_id

    for module_name in ("quiz.generator", "quiz.world_generator", "quiz.ai_support"):
        try:
            module = __import__(module_name, fromlist=["*"])
            if hasattr(module, "LOCAL_USER_ID"):
                setattr(module, "LOCAL_USER_ID", user_id)
        except Exception:
            pass


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_logged_in")) and "auth_user_id" in st.session_state


def login_gate() -> bool:
    bootstrap_test_users()

    if is_logged_in():
        apply_runtime_user(st.session_state.auth_user_id)
        return True

    st.markdown('<div class="portal-mode-marker"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="portal-login-head">
            <div class="portal-kicker">LEARNING QUEST RPG</div>
            <div class="portal-login-title">세계 접속 인증</div>
            <div class="portal-login-copy">플레이어 정보를 확인한 뒤 연결할 세계를 선택합니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input(
        "플레이어 이름",
        placeholder="플레이어 이름을 입력하세요",
        key="login_username",
    )

    password = st.text_input(
        "접속 암호",
        type="password",
        placeholder="암호를 입력하세요",
        key="login_password",
    )

    if st.button("✦ 세계의 문에 접속", type="primary", width="stretch"):
        if not username.strip():
            st.error("플레이어 이름을 입력해주세요.")
            return False

        if not password:
            st.error("접속 암호를 입력해주세요.")
            return False

        user = authenticate(username, password)

        if not user:
            st.error("플레이어 정보를 확인하지 못했습니다. 이름과 접속 암호를 다시 확인하세요.")
            return False

        st.session_state.auth_logged_in = True
        st.session_state.auth_username = user["username"]
        st.session_state.auth_user_id = user["user_id"]
        st.session_state.auth_display_name = user["display_name"]
        st.session_state.auth_test_tier = user["test_tier"]
        st.session_state.world_gate_done = False
        st.session_state.world_gate_mode = "menu"

        apply_runtime_user(user["user_id"])
        st.rerun()

    return False


def logout() -> None:
    st.session_state.clear()
    st.rerun()