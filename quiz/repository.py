from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "game.db"
LOCAL_USER_ID = "local_user"


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


def _player_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["inventory"] = _loads(data.get("inventory"), [])
    data["equipped_item"] = _loads(data.get("equipped_item"), {})
    data["extra_state"] = _loads(data.get("extra_state"), {})
    return data


def get_or_create_player_state(user_id: str = LOCAL_USER_ID) -> dict[str, Any]:
    initialize_database()
    uid = str(user_id)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM player_state WHERE user_id = ?", (uid,)).fetchone()
        if row is None:
            conn.execute("INSERT INTO player_state (user_id) VALUES (?)", (uid,))
            conn.commit()
            row = conn.execute("SELECT * FROM player_state WHERE user_id = ?", (uid,)).fetchone()
    return _player_row_to_dict(row)


def save_player_state(state: dict[str, Any], user_id: str = LOCAL_USER_ID) -> None:
    initialize_database()
    uid = str(user_id or state.get("user_id") or LOCAL_USER_ID)
    current = get_or_create_player_state(uid)
    merged = {**current, **state, "user_id": uid}
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO player_state (
                user_id, level, xp, stat_points, intelligence, wisdom, vitality, luck,
                player_hp, battle_tickets, inventory, equipped_item, extra_state, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                level=excluded.level,
                xp=excluded.xp,
                stat_points=excluded.stat_points,
                intelligence=excluded.intelligence,
                wisdom=excluded.wisdom,
                vitality=excluded.vitality,
                luck=excluded.luck,
                player_hp=excluded.player_hp,
                battle_tickets=excluded.battle_tickets,
                inventory=excluded.inventory,
                equipped_item=excluded.equipped_item,
                extra_state=excluded.extra_state,
                updated_at=CURRENT_TIMESTAMP
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
            ),
        )
        conn.commit()


def save_question(question: dict[str, Any]) -> bool:
    initialize_database()
    category = str(question.get("category", "")).strip()
    difficulty = str(question.get("difficulty", "")).strip()
    qtext = str(question.get("question", "")).strip()
    if not category or not difficulty or not qtext:
        raise ValueError("문제 저장에 필요한 category/difficulty/question이 없습니다.")
    with get_connection() as conn:
        dup = conn.execute(
            "SELECT id FROM questions WHERE category=? AND difficulty=? AND question=? LIMIT 1",
            (category, difficulty, qtext),
        ).fetchone()
        if dup is not None:
            return False
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
                str(question.get("question_type", "multiple_choice")),
                qtext,
                json.dumps(question.get("options"), ensure_ascii=False) if question.get("options") is not None else None,
                json.dumps(question.get("answer"), ensure_ascii=False) if isinstance(question.get("answer"), (list, dict)) else str(question.get("answer", "")),
                str(question.get("explanation", "")),
                json.dumps(question.get("keywords"), ensure_ascii=False) if question.get("keywords") is not None else None,
                int(question.get("xp", 10)),
                str(question.get("source", "")),
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


def _world_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
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
    initialize_database()
    uid = str(user_id)
    with get_connection() as conn:
        conn.execute("UPDATE learning_worlds SET is_active=0 WHERE user_id=?", (uid,))
        cur = conn.execute(
            """
            INSERT INTO learning_worlds (
                user_id, world_name, topic, goal, learner_level, game_theme,
                subjects, regions, monsters, world_data, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                uid,
                str(world_name), str(topic), str(goal), str(learner_level), str(game_theme),
                json.dumps(subjects, ensure_ascii=False),
                json.dumps(regions, ensure_ascii=False),
                json.dumps(monsters, ensure_ascii=False),
                json.dumps(world_data, ensure_ascii=False),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_learning_worlds(user_id: str = LOCAL_USER_ID) -> list[dict[str, Any]]:
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM learning_worlds WHERE user_id=? ORDER BY is_active DESC, id DESC",
            (str(user_id),),
        ).fetchall()
    return [_world_row_to_dict(r) for r in rows]


def get_active_learning_world(user_id: str = LOCAL_USER_ID) -> dict[str, Any] | None:
    initialize_database()
    uid = str(user_id)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM learning_worlds WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (uid,),
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT * FROM learning_worlds WHERE user_id=? ORDER BY id DESC LIMIT 1",
                (uid,),
            ).fetchone()
    return _world_row_to_dict(row) if row is not None else None


def set_active_learning_world(world_id: int, user_id: str = LOCAL_USER_ID) -> bool:
    initialize_database()
    uid = str(user_id)
    wid = int(world_id)
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM learning_worlds WHERE id=? AND user_id=?", (wid, uid)).fetchone()
        if row is None:
            return False
        conn.execute("UPDATE learning_worlds SET is_active=0 WHERE user_id=?", (uid,))
        conn.execute("UPDATE learning_worlds SET is_active=1 WHERE id=? AND user_id=?", (wid, uid))
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
    initialize_database()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO question_attempts (
                user_id, world_id, question_id, category, category_key, subject_id,
                difficulty, question_type, is_correct, user_answer, correct_answer,
                xp_earned, attempt_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(user_id), int(world_id) if world_id is not None else None,
                int(question_id) if question_id is not None else None,
                category, category_key, subject_id, difficulty, question_type,
                1 if is_correct else 0,
                json.dumps(user_answer, ensure_ascii=False) if isinstance(user_answer, (list, dict)) else str(user_answer or ""),
                json.dumps(correct_answer, ensure_ascii=False) if isinstance(correct_answer, (list, dict)) else str(correct_answer or ""),
                int(xp_earned), str(attempt_type or "quest"),
            ),
        )
        conn.commit()


def get_question_attempts(user_id: str, world_id: int | None = None, days: int | None = None) -> list[dict[str, Any]]:
    initialize_database()
    clauses = ["user_id=?"]
    params: list[Any] = [str(user_id)]
    if world_id is not None:
        clauses.append("world_id=?")
        params.append(int(world_id))
    if days is not None:
        cutoff = (datetime.now() - timedelta(days=int(days))).isoformat(timespec="seconds")
        clauses.append("datetime(created_at) >= datetime(?)")
        params.append(cutoff)
    sql = "SELECT * FROM question_attempts WHERE " + " AND ".join(clauses) + " ORDER BY id DESC"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        data = dict(row)
        data["is_correct"] = bool(data.get("is_correct", 0))
        result.append(data)
    return result


# 모듈 import 시 DB를 파괴하지 않고 필요한 테이블/컬럼만 보강한다.
initialize_database()
