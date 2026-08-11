from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from datetime import datetime
from typing import Any

import psycopg
import streamlit as st
from psycopg.rows import dict_row

import quiz.repository as repository


LEGACY_USER_ID = "local_player"

TEST_ACCOUNTS = (
    {
        "username": "high_test",
        "password": "high1234",
        "user_id": LEGACY_USER_ID,
        "tier": "HIGH",
        "display_name": "고레벨 테스트",
    },
    {
        "username": "mid_test",
        "password": "mid1234",
        "user_id": "mid_test_user",
        "tier": "MID",
        "display_name": "중레벨 테스트",
    },
    {
        "username": "low_test",
        "password": "low1234",
        "user_id": "low_test_user",
        "tier": "LOW",
        "display_name": "저레벨 테스트",
    },
)


def _database_url() -> str:
    try:
        value = str(st.secrets["DATABASE_URL"]).strip()
    except Exception as exc:
        raise RuntimeError("DATABASE_URL을 찾을 수 없습니다.") from exc

    if not value:
        raise RuntimeError("DATABASE_URL이 비어 있습니다.")

    return value


def _auth_connection():
    return psycopg.connect(
        _database_url(),
        row_factory=dict_row,
        connect_timeout=10,
    )


def initialize_auth_tables() -> None:
    with _auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS public.app_users (
                    username TEXT PRIMARY KEY,
                    user_key TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    test_tier TEXT NOT NULL DEFAULT 'LOW',
                    created_at TIMESTAMP NOT NULL
                )
                """
            )
        conn.commit()


def _hash_password(
    password: str,
    salt_hex: str | None = None,
) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000,
    )

    return digest.hex(), salt.hex()


def bootstrap_test_users() -> None:
    """기존 HIGH/MID/LOW 테스트 계정을 Supabase에 보존한다."""
    initialize_auth_tables()

    with _auth_connection() as conn:
        with conn.cursor() as cur:
            for account in TEST_ACCOUNTS:
                cur.execute(
                    """
                    SELECT 1
                    FROM public.app_users
                    WHERE username = %s
                    """,
                    (account["username"],),
                )

                if cur.fetchone():
                    continue

                password_hash, salt_hex = _hash_password(
                    account["password"]
                )

                cur.execute(
                    """
                    INSERT INTO public.app_users (
                        username,
                        user_key,
                        password_hash,
                        password_salt,
                        display_name,
                        test_tier,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        account["username"],
                        str(account["user_id"]),
                        password_hash,
                        salt_hex,
                        account["display_name"],
                        account["tier"],
                        datetime.now(),
                    ),
                )

        conn.commit()


def _restore_user_id(
    username: str,
    stored_user_key: str,
) -> Any:
    if stored_user_key is not None and str(stored_user_key).strip():
        return str(stored_user_key)

    if username == "high_test":
        return LEGACY_USER_ID

    return str(stored_user_key or "")


def authenticate(
    username: str,
    password: str,
) -> dict[str, Any] | None:
    username = username.strip()

    if not username or not password:
        return None

    with _auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    username,
                    user_key,
                    password_hash,
                    password_salt,
                    display_name,
                    test_tier
                FROM public.app_users
                WHERE username = %s
                """,
                (username,),
            )
            row = cur.fetchone()

    if not row:
        return None

    digest, _ = _hash_password(
        password,
        row["password_salt"],
    )

    if not hmac.compare_digest(
        digest,
        row["password_hash"],
    ):
        return None

    return {
        "username": row["username"],
        "user_id": _restore_user_id(
            row["username"],
            row["user_key"],
        ),
        "display_name": row["display_name"],
        "test_tier": row["test_tier"],
    }


def create_account(
    username: str,
    password: str,
    password_confirm: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    username = username.strip()

    if len(username) < 3:
        return False, "플레이어 이름은 3자 이상 입력해주세요.", None

    if len(username) > 24:
        return False, "플레이어 이름은 24자 이하로 입력해주세요.", None

    if not all(
        ch.isalnum() or ch in ("_", "-")
        for ch in username
    ):
        return (
            False,
            "플레이어 이름은 영문, 숫자, `_`, `-`만 사용할 수 있습니다.",
            None,
        )

    if len(password) < 6:
        return False, "접속 암호는 6자 이상 입력해주세요.", None

    if password != password_confirm:
        return False, "접속 암호가 서로 일치하지 않습니다.", None

    initialize_auth_tables()

    with _auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM public.app_users
                WHERE username = %s
                """,
                (username,),
            )

            if cur.fetchone():
                return False, "이미 사용 중인 플레이어 이름입니다.", None

            user_key = f"user_{uuid.uuid4().hex}"
            password_hash, salt_hex = _hash_password(password)

            try:
                cur.execute(
                    """
                    INSERT INTO public.app_users (
                        username,
                        user_key,
                        password_hash,
                        password_salt,
                        display_name,
                        test_tier,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        user_key,
                        password_hash,
                        salt_hex,
                        username,
                        "NEW",
                        datetime.now(),
                    ),
                )
                conn.commit()

            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return False, "이미 사용 중인 플레이어 이름입니다.", None

    user = {
        "username": username,
        "user_id": user_key,
        "display_name": username,
        "test_tier": "NEW",
    }

    return True, "새로운 플레이어 기록이 생성되었습니다.", user


def apply_runtime_user(user_id: Any) -> None:
    """
    인증은 Supabase를 사용하지만,
    게임 데이터 계층은 아직 기존 SQLite repository를 사용한다.
    """
    repository.LOCAL_USER_ID = user_id

    for module_name in (
        "quiz.generator",
        "quiz.world_generator",
        "quiz.ai_support",
    ):
        try:
            module = __import__(module_name, fromlist=["*"])
            if hasattr(module, "LOCAL_USER_ID"):
                setattr(module, "LOCAL_USER_ID", user_id)
        except Exception:
            pass


def is_logged_in() -> bool:
    return (
        bool(st.session_state.get("auth_logged_in"))
        and "auth_user_id" in st.session_state
    )


def _complete_login(user: dict[str, Any]) -> None:
    st.session_state.auth_logged_in = True
    st.session_state.auth_username = user["username"]
    st.session_state.auth_user_id = user["user_id"]
    st.session_state.auth_display_name = user["display_name"]
    st.session_state.auth_test_tier = user["test_tier"]

    st.session_state.world_gate_done = False
    st.session_state.world_gate_mode = "menu"

    apply_runtime_user(user["user_id"])


def login_gate() -> bool:
    try:
        bootstrap_test_users()
    except Exception as exc:
        st.error(
            "계정 서버에 연결하지 못했습니다. "
            f"잠시 후 다시 시도해주세요. ({exc})"
        )
        return False

    if is_logged_in():
        apply_runtime_user(st.session_state.auth_user_id)
        return True

    st.markdown(
        '<div class="portal-mode-marker"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="portal-login-head">
            <div class="portal-kicker">LEARNING QUEST RPG</div>
            <div class="portal-login-title">세계 접속 인증</div>
            <div class="portal-login-copy">
                기존 세계에 접속하거나 새로운 플레이어 기록을 생성합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(
        [
            "✦ 세계의 문에 접속",
            "✧ 새로운 플레이어 등록",
        ]
    )

    with login_tab:
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

        if st.button(
            "✦ 세계의 문에 접속",
            type="primary",
            width="stretch",
            key="login_submit",
        ):
            if not username.strip():
                st.error("플레이어 이름을 입력해주세요.")

            elif not password:
                st.error("접속 암호를 입력해주세요.")

            else:
                try:
                    user = authenticate(
                        username,
                        password,
                    )
                except Exception as exc:
                    st.error(
                        "계정 서버에 연결하지 못했습니다. "
                        f"잠시 후 다시 시도해주세요. ({exc})"
                    )
                    return False

                if not user:
                    st.error(
                        "플레이어 정보를 확인하지 못했습니다. "
                        "이름과 접속 암호를 다시 확인하세요."
                    )
                else:
                    _complete_login(user)
                    st.rerun()

    with register_tab:
        st.caption(
            "새로운 플레이어 기록을 생성합니다. "
            "생성된 계정은 아직 어떤 학습 월드도 보유하지 않습니다."
        )

        new_username = st.text_input(
            "새 플레이어 이름",
            placeholder="3~24자의 영문·숫자 이름",
            key="register_username",
        )

        new_password = st.text_input(
            "새 접속 암호",
            type="password",
            placeholder="6자 이상 입력하세요",
            key="register_password",
        )

        new_password_confirm = st.text_input(
            "접속 암호 확인",
            type="password",
            placeholder="같은 암호를 다시 입력하세요",
            key="register_password_confirm",
        )

        if st.button(
            "✧ 새로운 세계의 문 열기",
            type="primary",
            width="stretch",
            key="register_submit",
        ):
            try:
                ok, message, user = create_account(
                    new_username,
                    new_password,
                    new_password_confirm,
                )
            except Exception as exc:
                st.error(
                    "계정 생성 중 데이터베이스 연결 오류가 발생했습니다. "
                    f"({exc})"
                )
                return False

            if not ok:
                st.error(message)

            elif user is not None:
                _complete_login(user)

                st.session_state.new_account_created = True
                st.session_state.new_account_name = user["username"]

                st.rerun()

    return False


def logout() -> None:
    st.session_state.clear()
    st.rerun()