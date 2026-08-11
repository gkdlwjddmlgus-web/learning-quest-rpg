from __future__ import annotations

import hashlib
import json
import sqlite3

import psycopg
import streamlit as st
from psycopg.rows import dict_row
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "game.db"
LOCAL_USER_ID = "local_user"


def _database_url() -> str:
    try:
        value = str(st.secrets["DATABASE_URL"]).strip()
    except Exception as exc:
        raise RuntimeError("DATABASE_URL을 찾을 수 없습니다.") from exc

    if not value:
        raise RuntimeError("DATABASE_URL이 비어 있습니다.")

    return value


def get_player_connection():
    return psycopg.connect(
        _database_url(),
        row_factory=dict_row,
        connect_timeout=10,
    )


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _ensure_column(conn: sqlite3.Connection, table: str, name: str, ddl: str) -> None:
    if name not in _table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def initialize_database() -> None:
    """기존 game.db를 보존하면서 현재 코드가 요구하는 스키마만 보강한다.

    SQLite는 ALTER TABLE ... ADD COLUMN에서 CURRENT_TIMESTAMP 같은
    비상수 기본값을 허용하지 않는 경우가 있으므로, 레거시 테이블의 시간
    컬럼은 우선 TEXT로 추가한 뒤 기존 행을 현재 시각으로 백필한다.
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_state (
                user_id TEXT PRIMARY KEY,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                stat_points INTEGER NOT NULL DEFAULT 0,
                intelligence INTEGER NOT NULL DEFAULT 1,
                wisdom INTEGER NOT NULL DEFAULT 1,
                vitality INTEGER NOT NULL DEFAULT 1,
                luck INTEGER NOT NULL DEFAULT 1,
                player_hp INTEGER NOT NULL DEFAULT 50,
                battle_tickets INTEGER NOT NULL DEFAULT 5,
                inventory TEXT NOT NULL DEFAULT '[]',
                equipped_item TEXT NOT NULL DEFAULT '{}',
                extra_state TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                question_type TEXT NOT NULL DEFAULT 'multiple_choice',
                question TEXT NOT NULL,
                options TEXT,
                answer TEXT,
                explanation TEXT NOT NULL DEFAULT '',
                keywords TEXT,
                xp INTEGER NOT NULL DEFAULT 10,
                source TEXT NOT NULL DEFAULT '',
                solved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_worlds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'local_user',
                world_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                goal TEXT NOT NULL DEFAULT '',
                learner_level TEXT NOT NULL DEFAULT '초급',
                game_theme TEXT NOT NULL DEFAULT '판타지',
                subjects TEXT NOT NULL DEFAULT '[]',
                regions TEXT NOT NULL DEFAULT '[]',
                monsters TEXT NOT NULL DEFAULT '[]',
                world_data TEXT NOT NULL DEFAULT '{}',
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS question_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                world_id INTEGER,
                question_id INTEGER,
                category TEXT,
                category_key TEXT,
                subject_id TEXT,
                difficulty TEXT,
                question_type TEXT,
                is_correct INTEGER NOT NULL DEFAULT 0,
                user_answer TEXT,
                correct_answer TEXT,
                xp_earned INTEGER NOT NULL DEFAULT 0,
                attempt_type TEXT NOT NULL DEFAULT 'quest',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # player_state -------------------------------------------------------
        for name, ddl in [
            ("level", "INTEGER NOT NULL DEFAULT 1"),
            ("xp", "INTEGER NOT NULL DEFAULT 0"),
            ("stat_points", "INTEGER NOT NULL DEFAULT 0"),
            ("intelligence", "INTEGER NOT NULL DEFAULT 1"),
            ("wisdom", "INTEGER NOT NULL DEFAULT 1"),
            ("vitality", "INTEGER NOT NULL DEFAULT 1"),
            ("luck", "INTEGER NOT NULL DEFAULT 1"),
            ("player_hp", "INTEGER NOT NULL DEFAULT 50"),
            ("battle_tickets", "INTEGER NOT NULL DEFAULT 5"),
            ("inventory", "TEXT NOT NULL DEFAULT '[]'"),
            ("equipped_item", "TEXT NOT NULL DEFAULT '{}'"),
            ("extra_state", "TEXT NOT NULL DEFAULT '{}'"),
            ("updated_at", "TEXT"),
        ]:
            _ensure_column(conn, "player_state", name, ddl)
        conn.execute(
            "UPDATE player_state SET updated_at = CURRENT_TIMESTAMP "
            "WHERE updated_at IS NULL OR updated_at = ''"
        )

        # questions ----------------------------------------------------------
        for name, ddl in [
            ("category", "TEXT NOT NULL DEFAULT ''"),
            ("difficulty", "TEXT NOT NULL DEFAULT '쉬움'"),
            ("question_type", "TEXT NOT NULL DEFAULT 'multiple_choice'"),
            ("question", "TEXT NOT NULL DEFAULT ''"),
            ("options", "TEXT"),
            ("answer", "TEXT"),
            ("explanation", "TEXT NOT NULL DEFAULT ''"),
            ("keywords", "TEXT"),
            ("xp", "INTEGER NOT NULL DEFAULT 10"),
            ("source", "TEXT NOT NULL DEFAULT ''"),
            ("solved", "INTEGER NOT NULL DEFAULT 0"),
            ("created_at", "TEXT"),
        ]:
            _ensure_column(conn, "questions", name, ddl)

        question_columns = _table_columns(conn, "questions")
        if "is_solved" in question_columns:
            conn.execute(
                "UPDATE questions SET solved = COALESCE(is_solved, 0) "
                "WHERE COALESCE(solved, 0) = 0"
            )
        if "correct_answer" in question_columns:
            conn.execute(
                "UPDATE questions SET answer = correct_answer "
                "WHERE (answer IS NULL OR answer = '') AND correct_answer IS NOT NULL"
            )
        if "choices" in question_columns:
            conn.execute(
                "UPDATE questions SET options = choices "
                "WHERE options IS NULL AND choices IS NOT NULL"
            )
        conn.execute(
            "UPDATE questions SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL OR created_at = ''"
        )

        # learning_worlds ----------------------------------------------------
        for name, ddl in [
            ("user_id", "TEXT NOT NULL DEFAULT 'local_user'"),
            ("world_name", "TEXT NOT NULL DEFAULT '학습 월드'"),
            ("topic", "TEXT NOT NULL DEFAULT ''"),
            ("goal", "TEXT NOT NULL DEFAULT ''"),
            ("learner_level", "TEXT NOT NULL DEFAULT '초급'"),
            ("game_theme", "TEXT NOT NULL DEFAULT '판타지'"),
            ("subjects", "TEXT NOT NULL DEFAULT '[]'"),
            ("regions", "TEXT NOT NULL DEFAULT '[]'"),
            ("monsters", "TEXT NOT NULL DEFAULT '[]'"),
            ("world_data", "TEXT NOT NULL DEFAULT '{}'"),
            ("is_active", "INTEGER NOT NULL DEFAULT 0"),
            ("created_at", "TEXT"),
        ]:
            _ensure_column(conn, "learning_worlds", name, ddl)
        conn.execute(
            "UPDATE learning_worlds SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL OR created_at = ''"
        )

        # question_attempts --------------------------------------------------
        # 이전 버전에서는 이 테이블이 훨씬 단순했기 때문에 로그인/학습기록
        # 도입 후 필요한 모든 컬럼을 인덱스 생성 전에 보강한다.
        for name, ddl in [
            ("user_id", "TEXT NOT NULL DEFAULT 'local_user'"),
            ("world_id", "INTEGER"),
            ("question_id", "INTEGER"),
            ("category", "TEXT"),
            ("category_key", "TEXT"),
            ("subject_id", "TEXT"),
            ("difficulty", "TEXT"),
            ("question_type", "TEXT"),
            ("is_correct", "INTEGER NOT NULL DEFAULT 0"),
            ("user_answer", "TEXT"),
            ("correct_answer", "TEXT"),
            ("xp_earned", "INTEGER NOT NULL DEFAULT 0"),
            ("attempt_type", "TEXT NOT NULL DEFAULT 'quest'"),
            ("created_at", "TEXT"),
        ]:
            _ensure_column(conn, "question_attempts", name, ddl)

        attempt_columns = _table_columns(conn, "question_attempts")
        # 가능한 레거시 시간 컬럼을 새 created_at으로 이관한다.
        for legacy_time in ("attempted_at", "timestamp", "answered_at"):
            if legacy_time in attempt_columns:
                conn.execute(
                    f"UPDATE question_attempts SET created_at = {legacy_time} "
                    f"WHERE (created_at IS NULL OR created_at = '') AND {legacy_time} IS NOT NULL"
                )
                break
        conn.execute(
            "UPDATE question_attempts SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL OR created_at = ''"
        )

        # 인덱스는 필요한 컬럼이 모두 보장된 뒤 마지막에 만든다.
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_questions_pool "
            "ON questions(category, difficulty, solved)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_worlds_user "
            "ON learning_worlds(user_id, is_active)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_user_world "
            "ON question_attempts(user_id, world_id, created_at)"
        )
        conn.commit()


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _player_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    data["inventory"] = _loads(data.get("inventory"), [])
    data["equipped_item"] = _loads(data.get("equipped_item"), {})
    data["extra_state"] = _loads(data.get("extra_state"), {})
    return data


def get_or_create_player_state(
    user_id: str = LOCAL_USER_ID,
) -> dict[str, Any]:
    uid = str(user_id)

    with get_player_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM public.player_state
                WHERE user_id = %s
                """,
                (uid,),
            )
            row = cur.fetchone()

            if row is None:
                cur.execute(
                    """
                    INSERT INTO public.player_state (
                        user_id, level, xp, stat_points,
                        intelligence, wisdom, vitality, luck,
                        player_hp, battle_tickets,
                        inventory, equipped_item, extra_state, updated_at
                    )
                    VALUES (
                        %s, 1, 0, 0,
                        1, 1, 1, 1,
                        50, 5,
                        '[]', '{}', '{}', %s
                    )
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    (
                        uid,
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
                conn.commit()

                cur.execute(
                    """
                    SELECT *
                    FROM public.player_state
                    WHERE user_id = %s
                    """,
                    (uid,),
                )
                row = cur.fetchone()

    if row is None:
        raise RuntimeError(
            f"player_state를 생성하거나 불러오지 못했습니다: {uid}"
        )

    return _player_row_to_dict(row)


def save_player_state(
    state: dict[str, Any],
    user_id: str = LOCAL_USER_ID,
) -> None:
    uid = str(user_id or state.get("user_id") or LOCAL_USER_ID)

    current = get_or_create_player_state(uid)
    merged = {**current, **state, "user_id": uid}
    updated_at = datetime.now().isoformat(timespec="seconds")

    with get_player_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.player_state (
                    user_id, level, xp, stat_points,
                    intelligence, wisdom, vitality, luck,
                    player_hp, battle_tickets,
                    inventory, equipped_item, extra_state, updated_at
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    level = EXCLUDED.level,
                    xp = EXCLUDED.xp,
                    stat_points = EXCLUDED.stat_points,
                    intelligence = EXCLUDED.intelligence,
                    wisdom = EXCLUDED.wisdom,
                    vitality = EXCLUDED.vitality,
                    luck = EXCLUDED.luck,
                    player_hp = EXCLUDED.player_hp,
                    battle_tickets = EXCLUDED.battle_tickets,
                    inventory = EXCLUDED.inventory,
                    equipped_item = EXCLUDED.equipped_item,
                    extra_state = EXCLUDED.extra_state,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    uid,
                    int(merged.get("level", 1)),
                    int(merged.get("xp", 0)),
                    int(merged.get("stat_points", 0)),
                    int(merged.get("intelligence", 1)),
                    int(merged.get("wisdom", 1)),
                    int(merged.get("vitality", 1)),
                    int(merged.get("luck", 1)),
                    int(merged.get("player_hp", 50)),
                    int(merged.get("battle_tickets", 5)),
                    json.dumps(merged.get("inventory", []), ensure_ascii=False),
                    json.dumps(merged.get("equipped_item", {}), ensure_ascii=False),
                    json.dumps(merged.get("extra_state", {}), ensure_ascii=False),
                    updated_at,
                ),
            )

        conn.commit()



def _build_question_hash(category: str, difficulty: str, question_text: str) -> str:
    """레거시 questions.question_hash 컬럼과 호환되는 안정적인 문제 식별자."""
    payload = f"{str(category).strip()}|{str(difficulty).strip()}|{str(question_text).strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def save_question(question: dict[str, Any]) -> bool:
    initialize_database()

    category = str(question.get("category", "")).strip()
    difficulty = str(question.get("difficulty", "")).strip()
    qtext = str(question.get("question", "")).strip()

    if not category or not difficulty or not qtext:
        raise ValueError("문제 저장에 필요한 category/difficulty/question이 없습니다.")

    question_type = str(question.get("question_type", "multiple_choice"))
    options = (
        json.dumps(question.get("options"), ensure_ascii=False)
        if question.get("options") is not None
        else None
    )
    answer = (
        json.dumps(question.get("answer"), ensure_ascii=False)
        if isinstance(question.get("answer"), (list, dict))
        else str(question.get("answer", ""))
    )
    explanation = str(question.get("explanation", ""))
    keywords = (
        json.dumps(question.get("keywords"), ensure_ascii=False)
        if question.get("keywords") is not None
        else None
    )
    xp = int(question.get("xp", 10))
    source = str(question.get("source", ""))

    with get_connection() as conn:
        columns = _table_columns(conn, "questions")
        has_question_hash = "question_hash" in columns

        dup = conn.execute(
            "SELECT id FROM questions "
            "WHERE category=? AND difficulty=? AND question=? LIMIT 1",
            (category, difficulty, qtext),
        ).fetchone()
        if dup is not None:
            return False

        if has_question_hash:
            question_hash = _build_question_hash(category, difficulty, qtext)

            hash_dup = conn.execute(
                "SELECT id FROM questions WHERE question_hash=? LIMIT 1",
                (question_hash,),
            ).fetchone()
            if hash_dup is not None:
                return False

            conn.execute(
                """
                INSERT INTO questions (
                    category, difficulty, question_type, question, options, answer,
                    explanation, keywords, xp, source, solved, question_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    category,
                    difficulty,
                    question_type,
                    qtext,
                    options,
                    answer,
                    explanation,
                    keywords,
                    xp,
                    source,
                    question_hash,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO questions (
                    category, difficulty, question_type, question, options, answer,
                    explanation, keywords, xp, source, solved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    category,
                    difficulty,
                    question_type,
                    qtext,
                    options,
                    answer,
                    explanation,
                    keywords,
                    xp,
                    source,
                ),
            )

        conn.commit()

    return True


def _question_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["options"] = _loads(data.get("options"), [])
    data["keywords"] = _loads(data.get("keywords"), [])
    ans = data.get("answer")
    if isinstance(ans, str) and ans[:1] in ("[", "{"):
        data["answer"] = _loads(ans, ans)
    return data


def count_available_questions(category: str, difficulty: str) -> int:
    initialize_database()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM questions WHERE category=? AND difficulty=? AND COALESCE(solved,0)=0",
            (str(category), str(difficulty)),
        ).fetchone()
    return int(row["n"] if row else 0)


def get_available_questions(category: str, difficulty: str, limit: int = 1) -> list[dict[str, Any]]:
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM questions
            WHERE category=? AND difficulty=? AND COALESCE(solved,0)=0
            ORDER BY RANDOM() LIMIT ?
            """,
            (str(category), str(difficulty), int(limit)),
        ).fetchall()
    return [_question_row_to_dict(r) for r in rows]


def mark_question_as_solved(question_id: int) -> None:
    initialize_database()
    with get_connection() as conn:
        conn.execute("UPDATE questions SET solved=1 WHERE id=?", (int(question_id),))
        conn.commit()


def _world_row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    data["subjects"] = _loads(data.get("subjects"), [])
    data["regions"] = _loads(data.get("regions"), [])
    data["monsters"] = _loads(data.get("monsters"), [])
    data["world_data"] = _loads(data.get("world_data"), {})
    data["is_active"] = bool(data.get("is_active", 0))
    return data


def create_learning_world(
    *,
    world_name: str,
    topic: str,
    goal: str,
    learner_level: str,
    game_theme: str,
    subjects: list[dict[str, Any]],
    regions: list[dict[str, Any]],
    monsters: list[dict[str, Any]],
    world_data: dict[str, Any],
    user_id: str = LOCAL_USER_ID,
) -> int:
    uid = str(user_id)

    with get_player_connection() as conn:
        with conn.cursor() as cur:
            # 한 사용자당 활성 월드는 하나만 유지
            cur.execute(
                """
                UPDATE public.learning_worlds
                SET is_active = 0
                WHERE user_id = %s
                """,
                (uid,),
            )

            cur.execute(
                """
                INSERT INTO public.learning_worlds (
                    user_id,
                    world_name,
                    topic,
                    goal,
                    learner_level,
                    game_theme,
                    subjects,
                    regions,
                    monsters,
                    world_data,
                    is_active,
                    created_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, 1, %s
                )
                RETURNING id
                """,
                (
                    uid,
                    str(world_name),
                    str(topic),
                    str(goal),
                    str(learner_level),
                    str(game_theme),
                    json.dumps(subjects, ensure_ascii=False),
                    json.dumps(regions, ensure_ascii=False),
                    json.dumps(monsters, ensure_ascii=False),
                    json.dumps(world_data, ensure_ascii=False),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

            row = cur.fetchone()

        conn.commit()

    if row is None:
        raise RuntimeError("새 학습 월드의 ID를 받아오지 못했습니다.")

    return int(row["id"])


def get_learning_worlds(
    user_id: str = LOCAL_USER_ID,
) -> list[dict[str, Any]]:
    uid = str(user_id)

    with get_player_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM public.learning_worlds
                WHERE user_id = %s
                ORDER BY is_active DESC, id DESC
                """,
                (uid,),
            )
            rows = cur.fetchall()

    return [_world_row_to_dict(row) for row in rows]


def get_active_learning_world(
    user_id: str = LOCAL_USER_ID,
) -> dict[str, Any] | None:
    uid = str(user_id)

    with get_player_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM public.learning_worlds
                WHERE user_id = %s
                  AND is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """,
                (uid,),
            )
            row = cur.fetchone()

            if row is None:
                cur.execute(
                    """
                    SELECT *
                    FROM public.learning_worlds
                    WHERE user_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (uid,),
                )
                row = cur.fetchone()

    return _world_row_to_dict(row) if row is not None else None


def set_active_learning_world(
    world_id: int,
    user_id: str = LOCAL_USER_ID,
) -> bool:
    uid = str(user_id)
    wid = int(world_id)

    with get_player_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM public.learning_worlds
                WHERE id = %s
                  AND user_id = %s
                """,
                (wid, uid),
            )

            if cur.fetchone() is None:
                return False

            cur.execute(
                """
                UPDATE public.learning_worlds
                SET is_active = 0
                WHERE user_id = %s
                """,
                (uid,),
            )

            cur.execute(
                """
                UPDATE public.learning_worlds
                SET is_active = 1
                WHERE id = %s
                  AND user_id = %s
                """,
                (wid, uid),
            )

        conn.commit()

    return True



def record_question_attempt(
    *,
    user_id: str,
    world_id: int | None,
    question_id: int | None,
    category: str | None,
    category_key: str | None,
    subject_id: str | None,
    difficulty: str | None,
    question_type: str | None,
    is_correct: bool,
    user_answer: Any,
    correct_answer: Any,
    xp_earned: int = 0,
    attempt_type: str = "quest",
) -> None:
    with get_player_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.question_attempts (
                    user_id,
                    world_id,
                    question_id,
                    category,
                    category_key,
                    subject_id,
                    difficulty,
                    question_type,
                    is_correct,
                    user_answer,
                    correct_answer,
                    xp_earned,
                    attempt_type,
                    created_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    str(user_id),
                    int(world_id) if world_id is not None else None,
                    int(question_id) if question_id is not None else None,
                    category,
                    category_key,
                    subject_id,
                    difficulty,
                    question_type,
                    1 if is_correct else 0,
                    json.dumps(user_answer, ensure_ascii=False)
                    if isinstance(user_answer, (list, dict))
                    else str(user_answer or ""),
                    json.dumps(correct_answer, ensure_ascii=False)
                    if isinstance(correct_answer, (list, dict))
                    else str(correct_answer or ""),
                    int(xp_earned),
                    str(attempt_type or "quest"),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

        conn.commit()


def get_question_attempts(
    user_id: str,
    world_id: int | None = None,
    days: int | None = None,
) -> list[dict[str, Any]]:
    clauses = ["user_id = %s"]
    params: list[Any] = [str(user_id)]

    if world_id is not None:
        clauses.append("world_id = %s")
        params.append(int(world_id))

    if days is not None:
        cutoff = (
            datetime.now() - timedelta(days=int(days))
        ).isoformat(timespec="seconds")
        clauses.append("created_at >= %s")
        params.append(cutoff)

    sql = (
        "SELECT * FROM public.question_attempts WHERE "
        + " AND ".join(clauses)
        + " ORDER BY id DESC"
    )

    with get_player_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

    result: list[dict[str, Any]] = []

    for row in rows:
        data = dict(row)
        data["is_correct"] = bool(data.get("is_correct", 0))
        result.append(data)

    return result




# 모듈 import 시 DB를 파괴하지 않고 필요한 테이블/컬럼만 보강한다.
initialize_database()
