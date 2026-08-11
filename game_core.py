from __future__ import annotations

import ast
import html
import json
import math
import random
import re
import uuid
from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
import pandas as pd

from quiz.generator import (
    build_world_category_key,
    ensure_question_pool,
    ensure_world_subject_pool,
)
import quiz.repository as repository

from quiz.repository import (
    get_available_questions,
    get_or_create_player_state,
    initialize_database,
    mark_question_as_solved,
    save_player_state,
    get_connection,
    record_question_attempt,
    get_question_attempts,
)
from quiz.world_generator import generate_and_save_learning_world as _generate_and_save_learning_world
from quiz.ai_support import friendly_ai_error

def current_user_id():
    """현재 로그인 사용자의 user_id를 반환한다."""
    return st.session_state.get("auth_user_id", repository.LOCAL_USER_ID)


# -----------------------------------------------------------------------------
# 로그인 사용자별 월드 격리 래퍼
# -----------------------------------------------------------------------------
# repository / world_generator 쪽 함수의 ``user_id=LOCAL_USER_ID`` 기본값은
# 함수가 정의될 때 평가된다. 로그인 후 repository.LOCAL_USER_ID를 바꿔도
# 이미 잡힌 기본 인자는 바뀌지 않으므로, 월드 관련 호출은 항상 현재
# 로그인 사용자의 ID를 명시적으로 전달한다.

def get_learning_worlds(user_id=None):
    uid = current_user_id() if user_id is None else user_id
    return repository.get_learning_worlds(uid)


def get_active_learning_world(user_id=None):
    uid = current_user_id() if user_id is None else user_id
    return repository.get_active_learning_world(uid)


def set_active_learning_world(world_id, user_id=None):
    uid = current_user_id() if user_id is None else user_id
    return repository.set_active_learning_world(world_id, uid)


def generate_and_save_learning_world(
    topic: str,
    goal: str,
    learner_level: str = "초급",
    game_theme: str = "판타지",
    user_id=None,
):
    uid = current_user_id() if user_id is None else user_id
    return _generate_and_save_learning_world(
        topic=topic,
        goal=goal,
        learner_level=learner_level,
        game_theme=game_theme,
        user_id=uid,
    )


EQUIPMENT_SLOTS = ["무기", "투구", "갑옷", "장갑", "신발"]
CATEGORIES = ["Python", "SQL", "통계", "데이터분석", "면접"]
DIFFICULTIES = ["쉬움", "보통", "어려움"]
MAX_ENHANCE_LEVEL = 15
ENHANCE_RATE = 0.20
REST_HEAL_RATE = 0.40
POTION_HEAL_RATE = 0.30
POTION_DROP_CHANCE = 0.35
DAILY_DUNGEON_LIMIT = 3
DUNGEON_XP_MULTIPLIER = 1.25
DUNGEON_EQUIPMENT_DROP_BONUS = 0.20
DUNGEON_POTION_DROP_BONUS = 0.20
DUNGEON_BALL_DROP_BONUS = 0.15
HEALING_POTION_ID = "healing_potion"
BASIC_BALL_ID = "basic_data_ball"
GREAT_BALL_ID = "great_data_ball"
ULTRA_BALL_ID = "ultra_data_ball"
CAPTURE_ITEMS = {
    BASIC_BALL_ID: {"name": "일반 데이터볼", "bonus": 0.00, "icon": "⚪"},
    GREAT_BALL_ID: {"name": "고급 데이터볼", "bonus": 0.15, "icon": "🔵"},
    ULTRA_BALL_ID: {"name": "정제된 데이터볼", "bonus": 0.30, "icon": "🟣"},
}
NATURES = [
    {"name": "성실함", "description": "학습 경험치 보너스가 조금 높습니다.", "xp_add": 0.02},
    {"name": "집요함", "description": "오답 복습과 잘 어울리는 성격입니다.", "xp_add": 0.01},
    {"name": "행운아", "description": "희귀한 개체로 느껴지는 성격입니다.", "xp_add": 0.00},
    {"name": "분석적", "description": "통계·분석 계열 학습에 강합니다.", "xp_add": 0.02},
    {"name": "빠름", "description": "민첩하고 공격적인 성격입니다.", "xp_add": 0.01},
]

CLASS_INFO = {
    "미전직": {"description": "레벨 5에 전직 가능", "xp_bonus": 0.0, "attack_bonus": 0, "defense_bonus": 0, "drop_bonus": 0.0},
    "Python 개발자": {"description": "Python 경험치 +20%, 공격력 +2", "xp_bonus": 0.20, "attack_bonus": 2, "defense_bonus": 0, "drop_bonus": 0.0},
    "SQL 마법사": {"description": "SQL 경험치 +20%, 치명타 +5%", "xp_bonus": 0.20, "attack_bonus": 0, "defense_bonus": 0, "drop_bonus": 0.0},
    "통계학자": {"description": "통계 경험치 +20%, 방어력 +3", "xp_bonus": 0.20, "attack_bonus": 0, "defense_bonus": 3, "drop_bonus": 0.0},
    "데이터 분석가": {"description": "모든 경험치 +10%, 장비 드랍 +5%", "xp_bonus": 0.10, "attack_bonus": 0, "defense_bonus": 0, "drop_bonus": 0.05},
}

SKILLS = {
    # 내부 key는 기존 저장 데이터/로직 호환을 위해 유지하고, 화면에는 display_name을 사용한다.
    "데이터 스캔": {
        "display_name": "정찰",
        "icon": "👁️",
        "description": "눈앞의 선택지를 살펴 허점을 찾습니다.",
        "effect": "객관식 문제에서 오답 보기 1개를 제거합니다.",
        "daily_limit": 2,
    },
    "쿼리 가속": {
        "display_name": "몰입",
        "icon": "✨",
        "description": "잠시 주변을 잊고 다음 학습에 온전히 집중합니다.",
        "effect": "다음 정답에서 획득하는 경험치를 2배로 만듭니다.",
        "daily_limit": 1,
    },
    "응급 복구": {
        "display_name": "티타임",
        "icon": "☕",
        "description": "모험 도중 잠깐 쉬며 몸과 마음을 추스릅니다.",
        "effect": "전투 중 최대 HP의 20%를 회복합니다.",
        "daily_limit": 1,
    },
}

ITEMS = [
    {"item_id": "python_dagger", "name": "낡은 파이썬 단검", "slot": "무기", "rarity": "일반", "base_attack": 2, "base_defense": 0, "set_name": "판다스"},
    {"item_id": "sql_staff", "name": "정제된 SQL 지팡이", "slot": "무기", "rarity": "고급", "base_attack": 4, "base_defense": 0, "set_name": "SQL 마도사"},
    {"item_id": "modeling_sword", "name": "모델링의 대검", "slot": "무기", "rarity": "희귀", "base_attack": 7, "base_defense": 1, "set_name": "분석가"},
    {"item_id": "statistics_hat", "name": "통계학자의 모자", "slot": "투구", "rarity": "고급", "base_attack": 1, "base_defense": 3, "set_name": "통계학자"},
    {"item_id": "visualization_crown", "name": "시각화의 왕관", "slot": "투구", "rarity": "희귀", "base_attack": 3, "base_defense": 4, "set_name": "분석가"},
    {"item_id": "analyst_eye", "name": "분석가의 심안", "slot": "투구", "rarity": "영웅", "base_attack": 4, "base_defense": 3, "set_name": "분석가"},
    {"item_id": "data_armor", "name": "데이터 정제 갑옷", "slot": "갑옷", "rarity": "고급", "base_attack": 0, "base_defense": 4, "set_name": "판다스"},
    {"item_id": "statistics_robe", "name": "통계학자의 로브", "slot": "갑옷", "rarity": "희귀", "base_attack": 1, "base_defense": 5, "set_name": "통계학자"},
    {"item_id": "pipeline_plate", "name": "파이프라인 판금갑옷", "slot": "갑옷", "rarity": "영웅", "base_attack": 2, "base_defense": 8, "set_name": "SQL 마도사"},
    {"item_id": "numpy_gloves", "name": "넘파이의 장갑", "slot": "장갑", "rarity": "일반", "base_attack": 2, "base_defense": 1, "set_name": "판다스"},
    {"item_id": "pandas_gloves", "name": "판다스의 장갑", "slot": "장갑", "rarity": "고급", "base_attack": 3, "base_defense": 2, "set_name": "판다스"},
    {"item_id": "feature_gauntlets", "name": "특성공학의 건틀릿", "slot": "장갑", "rarity": "희귀", "base_attack": 5, "base_defense": 3, "set_name": "분석가"},
    {"item_id": "preprocessing_boots", "name": "전처리의 장화", "slot": "신발", "rarity": "일반", "base_attack": 1, "base_defense": 2, "set_name": "판다스"},
    {"item_id": "query_boots", "name": "쿼리 최적화 신발", "slot": "신발", "rarity": "고급", "base_attack": 2, "base_defense": 3, "set_name": "SQL 마도사"},
    {"item_id": "deployment_boots", "name": "배포자의 전투화", "slot": "신발", "rarity": "희귀", "base_attack": 3, "base_defense": 5, "set_name": "통계학자"},
]
ITEM_CATALOG = {item["item_id"]: item for item in ITEMS}
ITEM_NAME_CATALOG = {item["name"]: item for item in ITEMS}
RARITY_WEIGHTS = {"일반": 60, "고급": 25, "희귀": 10, "영웅": 5}
RARITY_ICONS = {"일반": "⚪", "고급": "🟢", "희귀": "🔵", "영웅": "🟣"}
SLOT_ICONS = {"무기": "⚔️", "투구": "🪖", "갑옷": "🛡️", "장갑": "🧤", "신발": "🥾"}

STAGES = [
    {"stage": 1, "name": "전처리의 숲", "emoji": "🌲", "hp": 35, "attack": 4, "xp": 15, "boss": False},
    {"stage": 2, "name": "쿼리 동굴", "emoji": "🕳️", "hp": 55, "attack": 7, "xp": 25, "boss": False},
    {"stage": 3, "name": "통계의 탑", "emoji": "🗼", "hp": 75, "attack": 10, "xp": 40, "boss": False},
    {"stage": 4, "name": "전처리 골렘의 성소", "emoji": "🏛️", "hp": 130, "attack": 14, "xp": 100, "boss": True},
]

MONSTER_CATALOG = {
    "missing_slime": {"name": "결측치 슬라임", "emoji": "🟢", "element": "전처리", "rarity": "일반", "base_capture_rate": 0.55, "category": "Python", "xp_bonus": 0.04},
    "duplicate_goblin": {"name": "중복 데이터 고블린", "emoji": "👺", "element": "전처리", "rarity": "일반", "base_capture_rate": 0.50, "category": "데이터분석", "xp_bonus": 0.04},
    "outlier_mimic": {"name": "이상치 미믹", "emoji": "📦", "element": "전처리", "rarity": "고급", "base_capture_rate": 0.40, "category": "통계", "xp_bonus": 0.05},
    "join_wyvern": {"name": "조인 와이번", "emoji": "🐉", "element": "SQL", "rarity": "고급", "base_capture_rate": 0.38, "category": "SQL", "xp_bonus": 0.06},
    "index_mole": {"name": "인덱스 두더지", "emoji": "🦫", "element": "SQL", "rarity": "일반", "base_capture_rate": 0.52, "category": "SQL", "xp_bonus": 0.04},
    "query_specter": {"name": "서브쿼리 망령", "emoji": "👻", "element": "SQL", "rarity": "희귀", "base_capture_rate": 0.28, "category": "SQL", "xp_bonus": 0.08},
    "hypothesis_sage": {"name": "가설검정 현자", "emoji": "🧙", "element": "통계", "rarity": "희귀", "base_capture_rate": 0.26, "category": "통계", "xp_bonus": 0.08},
    "regression_fox": {"name": "회귀 여우", "emoji": "🦊", "element": "통계", "rarity": "고급", "base_capture_rate": 0.36, "category": "통계", "xp_bonus": 0.06},
    "distribution_owl": {"name": "분포 부엉이", "emoji": "🦉", "element": "통계", "rarity": "일반", "base_capture_rate": 0.48, "category": "통계", "xp_bonus": 0.04},
    "dashboard_sprite": {"name": "대시보드 요정", "emoji": "🧚", "element": "시각화", "rarity": "희귀", "base_capture_rate": 0.25, "category": "데이터분석", "xp_bonus": 0.08},
    "interview_knight": {"name": "면접 기사", "emoji": "🗡️", "element": "면접", "rarity": "고급", "base_capture_rate": 0.34, "category": "면접", "xp_bonus": 0.06},
    "preprocess_golem": {"name": "전처리 골렘", "emoji": "🗿", "element": "보스", "rarity": "영웅", "base_capture_rate": 0.00, "category": "데이터분석", "xp_bonus": 0.10},
}

ENCOUNTER_POOLS = {
    1: ["missing_slime", "duplicate_goblin", "outlier_mimic"],
    2: ["index_mole", "join_wyvern", "query_specter"],
    3: ["distribution_owl", "regression_fox", "hypothesis_sage", "dashboard_sprite", "interview_knight"],
    4: ["preprocess_golem"],
}


ACHIEVEMENTS = {
    "첫걸음": {"condition": lambda s: s["total_correct"] >= 1, "reward": "XP 20"},
    "Python 입문자": {"condition": lambda s: s["category_correct"].get("Python", 0) >= 10, "reward": "전투권 2"},
    "끈기의 분석가": {"condition": lambda s: s["streak"] >= 7, "reward": "희귀 장비 상자"},
    "오답 수집가": {"condition": lambda s: len(s["wrong_questions"]) >= 10, "reward": "기억의 조각 5"},
    "던전 정복자": {"condition": lambda s: s["stage_unlocked"] >= 4, "reward": "칭호: 데이터 정복자"},
    "첫 포획": {"condition": lambda s: s.get("total_captures", 0) >= 1, "reward": "고급 데이터볼 1"},
    "몬스터 수집가": {"condition": lambda s: len({m.get("monster_id") for m in s.get("captured_monsters", [])}) >= 5, "reward": "정제된 데이터볼 1"},
}


LEGACY_SHORT_ANSWER_SIGNALS = (
    "빈칸",
    "키워드",
    "함수명",
    "명령어",
    "연산자",
    "순서대로",
    "입력하세요",
    "작성하시오",
    "작성하세요",
    "영문 대문자",
    "영문으로",
    "SQL 키워드",
)


def looks_like_legacy_short_answer(
    question_text: str,
    answer: Any,
    question_type: str | None = None,
) -> bool:
    """과거 subjective 문제 중 실제로는 단답형인 문제를 판별한다."""
    if str(question_type or "").strip() == "multiple_choice":
        return False

    qtext = str(question_text or "").strip()
    answer_text = str(answer or "").strip()

    if not answer_text or len(answer_text) > 100:
        return False

    # 빈칸/키워드/명령어를 요구하는 문제는 단답형으로 간주한다.
    if any(signal in qtext for signal in LEGACY_SHORT_ANSWER_SIGNALS):
        return True

    # SQL 키워드·함수·짧은 기호 답처럼 명백히 짧은 답도 단답형으로 간주한다.
    # 문장형 모범답안은 마침표나 긴 한글 설명을 포함하는 경우가 많으므로 제외한다.
    compact = answer_text.replace("\n", " ").strip()
    if len(compact) <= 40 and not re.search(r"[.!?。]$", compact):
        token_like = bool(
            re.fullmatch(
                r"[A-Za-z0-9_()+\-*/<>=.,%\s|]+",
                compact,
            )
        )
        if token_like:
            return True

    return False


def migrate_legacy_short_answer_questions() -> int:
    """
    기존 DB에서 subjective로 저장됐지만 실제로는 단답형인 문제를 short_answer로 1회성 자동 보정한다.
    기존 문제/정답 내용은 변경하지 않고 question_type만 수정한다.
    """
    changed = 0

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, question_type, question, answer
            FROM questions
            WHERE question_type = 'subjective'
            """
        ).fetchall()

        target_ids = []
        for row in rows:
            if looks_like_legacy_short_answer(
                question_text=row["question"],
                answer=row["answer"],
                question_type=row["question_type"],
            ):
                target_ids.append(int(row["id"]))

        if target_ids:
            connection.executemany(
                """
                UPDATE questions
                SET question_type = 'short_answer'
                WHERE id = ?
                """,
                [(question_id,) for question_id in target_ids],
            )
            connection.commit()
            changed = len(target_ids)

    return changed


initialize_database()
migrate_legacy_short_answer_questions()


def default_extra_state() -> dict[str, Any]:
    return {
        "streak": 0,
        "last_study_date": None,
        "daily_date": None,
        "daily_progress": {"correct": 0, "sql": 0, "battles": 0},  # 레거시 호환
        "daily_progress_by_world": {},
        "daily_claimed": False,  # 레거시 호환
        "daily_claimed_by_world": {},
        "daily_dungeon_runs": 0,
        "daily_dungeon_runs_by_world": {},
        "total_correct": 0,
        "category_correct": {category: 0 for category in CATEGORIES},
        "wrong_questions": [],
        "memory_shards": 0,
        "dismantle_shards": 0,
        "world_intro_seen": {},
        "boss_quiz_seen": {},
        "boss_attack_buff_turns": 0,
        "stage_unlocked": 1,
        "boss_cleared": False,
        "job": "미전직",
        "skill_uses": {skill: 0 for skill in SKILLS},
        "skill_date": None,
        "xp_boost": False,
        "achievements": [],
        "titles": ["초보 분석가"],
        "selected_title": "초보 분석가",
        "event_log": [],
        "captured_monsters": [],
        "monster_dex": {},
        "active_monster_team": [None, None, None],
        "capture_starter_granted": False,
        "total_captures": 0,
    }


def merge_defaults(current: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    result = defaults.copy()
    for key, value in current.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_defaults(value, result[key])
        else:
            result[key] = value
    return result


def create_empty_slots() -> dict[str, str | None]:
    return {slot: None for slot in EQUIPMENT_SLOTS}


def normalize_inventory_item(item: dict[str, Any]) -> dict[str, Any]:
    item_id = str(item.get("item_id", ""))
    if item_id == HEALING_POTION_ID or item.get("name") == "회복 물약":
        return {"item_id": HEALING_POTION_ID, "item_type": "consumable", "name": "회복 물약", "quantity": max(1, int(item.get("quantity", 1)))}
    if item_id in CAPTURE_ITEMS:
        capture = CAPTURE_ITEMS[item_id]
        return {"item_id": item_id, "item_type": "capture_item", "name": capture["name"], "capture_bonus": capture["bonus"], "quantity": max(1, int(item.get("quantity", 1)))}
    name = str(item.get("name", "이름 없는 장비"))
    catalog = ITEM_NAME_CATALOG.get(name) or ITEM_CATALOG.get(str(item.get("item_id", "")))
    item_id = str(item.get("item_id") or (catalog["item_id"] if catalog else f"legacy_{re.sub(r'[^0-9a-zA-Z가-힣]+', '_', name)}"))
    slot = str(item.get("slot") or (catalog["slot"] if catalog else "무기"))
    return {
        "item_id": item_id,
        "item_type": "equipment",
        "name": name,
        "slot": slot if slot in EQUIPMENT_SLOTS else "무기",
        "rarity": str(item.get("rarity") or (catalog["rarity"] if catalog else "일반")),
        "base_attack": max(0, int(item.get("base_attack", item.get("attack", catalog["base_attack"] if catalog else 0)))),
        "base_defense": max(0, int(item.get("base_defense", item.get("defense", catalog["base_defense"] if catalog else 0)))),
        "enhance_level": max(0, min(MAX_ENHANCE_LEVEL, int(item.get("enhance_level", 0)))),
        "quantity": max(1, int(item.get("quantity", 1))),
        "set_name": str(item.get("set_name") or (catalog.get("set_name") if catalog else "기타")),
    }


def merge_inventory(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for raw in inventory:
        if not isinstance(raw, dict):
            continue
        item = normalize_inventory_item(raw)
        item_id = item["item_id"]
        if item_id not in merged:
            merged[item_id] = item
        else:
            merged[item_id]["quantity"] += item["quantity"]
            if item.get("item_type") == "equipment":
                merged[item_id]["enhance_level"] = max(merged[item_id]["enhance_level"], item["enhance_level"])
    return list(merged.values())


def migrate_equipped(raw: Any, inventory: list[dict[str, Any]]) -> dict[str, str | None]:
    result = create_empty_slots()
    valid_ids = {item["item_id"] for item in inventory if item.get("item_type") == "equipment"}
    if isinstance(raw, dict) and any(slot in raw for slot in EQUIPMENT_SLOTS):
        for slot in EQUIPMENT_SLOTS:
            value = raw.get(slot)
            if isinstance(value, str) and value in valid_ids:
                result[slot] = value
            elif isinstance(value, dict):
                item_id = normalize_inventory_item(value)["item_id"]
                if item_id in valid_ids:
                    result[slot] = item_id
    elif isinstance(raw, dict):
        item = normalize_inventory_item(raw)
        if item["item_id"] in valid_ids:
            result[item["slot"]] = item["item_id"]
    return result


def initialize_player_session() -> None:
    """로그인 사용자별 플레이어 상태를 세션에 적재한다.

    계정이 바뀌면 이전 계정의 세션 데이터를 재사용하지 않고 DB에서 다시 읽는다.
    """
    uid = current_user_id()
    if st.session_state.get("player_loaded_user_id") == uid and st.session_state.get("player_loaded"):
        return

    saved = get_or_create_player_state(current_user_id())
    st.session_state.level = int(saved["level"])
    st.session_state.xp = int(saved["xp"])
    st.session_state.stat_points = int(saved["stat_points"])
    st.session_state.intelligence = int(saved["intelligence"])
    st.session_state.wisdom = int(saved["wisdom"])
    st.session_state.vitality = int(saved["vitality"])
    st.session_state.luck = int(saved["luck"])
    st.session_state.player_hp = int(saved["player_hp"])
    st.session_state.battle_tickets = int(saved["battle_tickets"])
    st.session_state.inventory = merge_inventory(saved.get("inventory", []))
    st.session_state.equipped_items = migrate_equipped(saved.get("equipped_item"), st.session_state.inventory)
    st.session_state.extra = merge_defaults(saved.get("extra_state", {}), default_extra_state())
    # 더 이상 사용하지 않는 레거시 행동(재분석/재정비) 기록을 정리한다.
    st.session_state.extra.setdefault("skill_uses", {}).pop("재분석", None)
    if not st.session_state.extra.get("capture_starter_granted"):
        st.session_state.inventory.append({"item_id": BASIC_BALL_ID, "item_type": "capture_item", "name": CAPTURE_ITEMS[BASIC_BALL_ID]["name"], "capture_bonus": 0.0, "quantity": 5})
        st.session_state.extra["capture_starter_granted"] = True
    st.session_state.player_loaded = True
    st.session_state.player_loaded_user_id = uid
    st.session_state._save_baseline_signature = _state_signature()
    st.session_state.save_dirty = False
    st.session_state.last_manual_save_at = None



TEMP = {
    "current_question": None,
    "answer_checked": False,
    "answer_is_correct": None,
    "answer_message": "",
    "selected_category": "Python",
    "selected_difficulty": "쉬움",
    "pool_message": "",
    "monster": None,
    "battle_log": [],
    "inventory_message": "",
    "event_message": "",
    "hidden_option": None,
    "capture_message": "",
    "selected_capture_ball": BASIC_BALL_ID,
    "monster_message": "",
    "boss_quiz": None,
    "boss_quiz_threshold": None,
}
def initialize_temp_session() -> None:
    """계정 전환/로그아웃 후 필요한 일시적 UI 상태를 다시 만든다."""
    for key, value in TEMP.items():
        if key not in st.session_state:
            # list/dict 등 가변 객체를 계정 간 공유하지 않도록 복사한다.
            if isinstance(value, list):
                st.session_state[key] = list(value)
            elif isinstance(value, dict):
                st.session_state[key] = dict(value)
            else:
                st.session_state[key] = value


def _current_player_payload() -> dict[str, Any]:
    """현재 세션의 영구 저장 대상만 한곳에서 수집한다."""
    return {
        "user_id": current_user_id(),
        "level": st.session_state.level,
        "xp": st.session_state.xp,
        "stat_points": st.session_state.stat_points,
        "intelligence": st.session_state.intelligence,
        "wisdom": st.session_state.wisdom,
        "vitality": st.session_state.vitality,
        "luck": st.session_state.luck,
        "player_hp": st.session_state.player_hp,
        "battle_tickets": st.session_state.battle_tickets,
        "inventory": st.session_state.inventory,
        "equipped_item": st.session_state.equipped_items,
        "extra_state": st.session_state.extra,
    }


def _state_signature(payload: dict[str, Any] | None = None) -> str:
    """
    DB 조회 없이 현재 상태가 마지막 저장본과 달라졌는지 비교하기 위한 서명.
    JSON 직렬화만 하므로 네트워크 지연이 없다.
    """
    data = payload if payload is not None else _current_player_payload()
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def mark_saved_baseline() -> None:
    """현재 세션 상태를 '마지막으로 저장된 상태' 기준점으로 기록한다."""
    st.session_state._save_baseline_signature = _state_signature()
    st.session_state.save_dirty = False


def has_unsaved_changes() -> bool:
    """현재 상태와 마지막 저장 기준점을 비교한다."""
    if not st.session_state.get("player_loaded"):
        return False

    baseline = st.session_state.get("_save_baseline_signature")
    if baseline is None:
        return bool(st.session_state.get("save_dirty", False))

    dirty = _state_signature() != baseline
    st.session_state.save_dirty = dirty
    return dirty


def persist() -> None:
    """
    기존 게임 코드와의 호환용 함수.

    과거에는 호출 즉시 Supabase에 저장했지만,
    이제는 현재 상태가 바뀌었는지만 표시한다.
    실제 외부 저장은 save_now()가 담당한다.
    """
    st.session_state.save_dirty = has_unsaved_changes()


def save_now(force: bool = False) -> bool:
    """
    현재 플레이어 상태를 Supabase에 한 번 저장한다.

    Returns:
        True  -> 실제 DB 저장 수행
        False -> 변경사항이 없어 저장 생략
    """
    if not st.session_state.get("player_loaded"):
        return False

    dirty = has_unsaved_changes()
    if not force and not dirty:
        return False

    payload = _current_player_payload()
    save_player_state(
        payload,
        current_user_id(),
    )

    mark_saved_baseline()
    st.session_state.last_manual_save_at = datetime.now().isoformat(
        timespec="seconds"
    )
    return True


def seed_test_profile_if_needed() -> None:
    """MID 테스트 계정에만 중간 성장 상태를 최초 1회 구성한다.

    HIGH는 기존 데이터 보존, LOW는 신규 기본값을 그대로 사용한다.
    """
    tier = str(st.session_state.get("auth_test_tier", "")).upper()
    if tier != "MID":
        return
    if st.session_state.extra.get("mid_test_profile_seeded_v1"):
        return

    st.session_state.level = 8
    st.session_state.xp = 45
    st.session_state.stat_points = 0
    st.session_state.intelligence = 7
    st.session_state.wisdom = 5
    st.session_state.vitality = 5
    st.session_state.luck = 4
    st.session_state.battle_tickets = max(int(st.session_state.battle_tickets), 15)

    starter_equipment = [
        ("python_dagger", 3),
        ("statistics_hat", 2),
        ("data_armor", 2),
        ("pandas_gloves", 3),
        ("preprocessing_boots", 2),
    ]
    for item_id, enhance_level in starter_equipment:
        catalog = ITEM_CATALOG[item_id]
        existing = next((x for x in st.session_state.inventory if x.get("item_id") == item_id), None)
        if existing is None:
            existing = normalize_inventory_item({**catalog, "item_type": "equipment", "quantity": 1})
            st.session_state.inventory.append(existing)
        existing["quantity"] = max(1, int(existing.get("quantity", 1)))
        existing["enhance_level"] = max(int(existing.get("enhance_level", 0)), enhance_level)
        st.session_state.equipped_items[catalog["slot"]] = item_id

    st.session_state.extra["mid_test_profile_seeded_v1"] = True
    st.session_state.player_hp = max_hp()
    persist()



def grant_enhancement_test_supply() -> None:
    """강화 시스템 점검용 자원을 최초 1회만 지급한다."""
    flag_key = "enhance_test_supply_v1_granted"
    if st.session_state.extra.get(flag_key):
        return

    # 전투권 테스트 보급
    st.session_state.battle_tickets += 50

    # 기존 python_dagger와 강화 단계를 공유하지 않도록 별도 item_id 사용
    test_dagger_id = "test_python_dagger"
    test_dagger = next(
        (item for item in st.session_state.inventory if item.get("item_id") == test_dagger_id),
        None,
    )

    if test_dagger:
        test_dagger["quantity"] = int(test_dagger.get("quantity", 0)) + 50
    else:
        st.session_state.inventory.append({
            "item_id": test_dagger_id,
            "item_type": "equipment",
            "name": "테스트용 낡은 파이썬 단검",
            "slot": "무기",
            "rarity": "일반",
            "base_attack": 2,
            "base_defense": 0,
            "enhance_level": 0,
            "quantity": 50,
            "set_name": "판다스",
        })

    st.session_state.extra[flag_key] = True
    st.session_state.inventory_message = (
        "🧪 강화 테스트 보급 완료: 전투권 +50 · 테스트용 낡은 파이썬 단검 +0 ×50"
    )
    persist()


def today_str() -> str:
    return date.today().isoformat()


def refresh_daily_state() -> None:
    extra = st.session_state.extra
    today = date.today()
    today_text = today.isoformat()
    if extra["daily_date"] != today_text:
        extra["daily_date"] = today_text
        extra["daily_progress"] = {"correct": 0, "sql": 0, "battles": 0}
        extra["daily_progress_by_world"] = {}
        extra["daily_claimed"] = False
        extra["daily_claimed_by_world"] = {}
        extra["daily_dungeon_runs"] = 0
        extra["daily_dungeon_runs_by_world"] = {}
    if extra["skill_date"] != today_text:
        extra["skill_date"] = today_text
        extra["skill_uses"] = {skill: 0 for skill in SKILLS}
    last = extra.get("last_study_date")
    if last:
        last_date = date.fromisoformat(last)
        if today - last_date > timedelta(days=1):
            extra["streak"] = 0
    persist()




def capture_item_count(item_id: str) -> int:
    item = get_item(item_id)
    return int(item.get("quantity", 0)) if item else 0


def add_capture_item(item_id: str, quantity: int = 1) -> None:
    if item_id not in CAPTURE_ITEMS:
        return
    add_item({"item_id": item_id, "item_type": "capture_item", "name": CAPTURE_ITEMS[item_id]["name"], "capture_bonus": CAPTURE_ITEMS[item_id]["bonus"], "quantity": quantity})


def get_captured_monster(instance_id: str | None) -> dict[str, Any] | None:
    if not instance_id:
        return None
    return next((monster for monster in st.session_state.extra["captured_monsters"] if monster.get("instance_id") == instance_id), None)


def team_monsters() -> list[dict[str, Any]]:
    result = []
    for instance_id in st.session_state.extra.get("active_monster_team", [None, None, None]):
        monster = get_captured_monster(instance_id)
        if monster:
            result.append(monster)
    return result


def team_xp_bonus(category: str) -> float:
    total = 0.0
    for monster in team_monsters():
        if monster.get("category") == category:
            total += float(monster.get("xp_bonus", 0.0)) + float(monster.get("nature_xp_add", 0.0))
    return min(total, 0.25)


def record_seen(monster_id: str) -> None:
    dex = st.session_state.extra["monster_dex"].setdefault(monster_id, {"seen": 0, "captured": 0})
    dex["seen"] += 1


def capture_probability(monster: dict[str, Any], ball_id: str) -> float:
    if monster.get("boss"):
        return 0.0
    hp_ratio = max(0.0, min(1.0, monster["hp"] / monster["max_hp"]))
    hp_bonus = (1.0 - hp_ratio) * 0.35
    ball_bonus = CAPTURE_ITEMS.get(ball_id, {}).get("bonus", 0.0)
    luck_bonus = min(st.session_state.luck * 0.01, 0.15)
    streak_bonus = min(st.session_state.extra.get("streak", 0) * 0.01, 0.10)
    return min(0.95, max(0.03, float(monster.get("base_capture_rate", 0.25)) + hp_bonus + ball_bonus + luck_bonus + streak_bonus))


def capture_monster(monster: dict[str, Any], ball_id: str) -> tuple[bool, str]:
    if monster.get("boss"):
        return False, "보스 몬스터는 포획할 수 없습니다."
    item = get_item(ball_id)
    if not item or item.get("quantity", 0) <= 0:
        return False, "선택한 데이터볼이 없습니다."

    item["quantity"] -= 1
    if item["quantity"] <= 0:
        st.session_state.inventory = [
            x for x in st.session_state.inventory
            if x.get("item_id") != ball_id
        ]

    chance = capture_probability(monster, ball_id)
    if random.random() >= chance:
        persist()
        return False, f"포획 실패! 성공 확률은 {chance:.0%}였습니다."

    nature = random.choice(NATURES)
    captured = {
        "instance_id": str(uuid.uuid4()),
        "world_id": monster.get("world_id"),
        "monster_id": monster["monster_id"],
        "name": monster["name"],
        "emoji": monster["emoji"],
        "element": monster["element"],
        "rarity": monster["rarity"],
        "category": monster["category"],
        "subject_id": monster.get("subject_id"),
        "xp_bonus": monster.get("xp_bonus", 0.04),
        "nature": nature["name"],
        "nature_xp_add": nature["xp_add"],
        "attack_iv": random.randint(1, 10),
        "defense_iv": random.randint(1, 10),
        "learning_iv": random.randint(1, 10),
        "friendship": 0,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
    }
    st.session_state.extra["captured_monsters"].append(captured)

    dex_key = monster.get("dex_key", monster["monster_id"])
    dex = st.session_state.extra["monster_dex"].setdefault(
        dex_key, {"seen": 0, "captured": 0}
    )
    dex["captured"] += 1
    st.session_state.extra["total_captures"] += 1

    if (
        st.session_state.extra["total_captures"] == 1
        and "초보 테이머" not in st.session_state.extra["titles"]
    ):
        st.session_state.extra["titles"].append("초보 테이머")

    persist()
    unlocked = evaluate_achievements()
    achievement_text = f" · 업적: {', '.join(unlocked)}" if unlocked else ""
    return True, (
        f"{monster['emoji']} {monster['name']} 포획 성공! "
        f"성격: {nature['name']}{achievement_text}"
    )

def finish_encounter(monster: dict[str, Any], captured: bool = False) -> None:
    active_world = get_active_learning_world()
    if active_world is not None:
        get_daily_world_progress(active_world)["battles"] += 1
    else:
        st.session_state.extra["daily_progress"]["battles"] += 1
    if captured:
        capture_xp = max(1, round(monster["xp"] * 0.5))
        if monster.get("encounter_type") == "dungeon":
            capture_xp = round(capture_xp * DUNGEON_XP_MULTIPLIER)
        st.session_state.battle_log.extend(
            gain_xp(capture_xp, monster.get("category", ""))
        )
    persist()

def required_xp(level: int) -> int:
    return level * 100


def max_hp() -> int:
    return 40 + st.session_state.vitality * 10


def round_stat(value: float) -> int:
    return math.floor(value + 0.5)


def get_item(item_id: str | None) -> dict[str, Any] | None:
    if not item_id:
        return None
    return next((item for item in st.session_state.inventory if item.get("item_id") == item_id), None)


def equipped_item(slot: str) -> dict[str, Any] | None:
    item = get_item(st.session_state.equipped_items.get(slot))
    return item if item and item.get("item_type") == "equipment" else None


def item_attack(item: dict[str, Any]) -> int:
    return round_stat(item["base_attack"] * (1 + item["enhance_level"] * ENHANCE_RATE))


def item_defense(item: dict[str, Any]) -> int:
    return round_stat(item["base_defense"] * (1 + item["enhance_level"] * ENHANCE_RATE))


def enhancement_success_rate(target_level: int) -> float:
    """목표 강화 단계 기준 성공 확률을 반환한다."""
    target_level = int(target_level)
    if target_level <= 0 or target_level > MAX_ENHANCE_LEVEL:
        return 0.0
    if target_level <= 3:
        return 1.0
    if target_level <= 10:
        return max(0.0, 1.0 - (target_level - 3) * 0.10)
    return max(0.0, 0.25 - (target_level - 11) * 0.05)


def enhancement_failure_drops(current_level: int) -> bool:
    """현재 강화 단계가 +11 이상일 때 실패하면 단계가 1 감소한다.

    예:
    - +10 -> +11 실패: +10 유지
    - +11 -> +12 실패: +10으로 하락
    """
    return int(current_level) >= 11


def attempt_equipment_enhancement(item: dict[str, Any]) -> tuple[bool, int, int, float]:
    """동일 장비 1개를 소비해 강화 1회를 시도한다.

    반환값: (성공 여부, 시도 전 단계, 시도 후 단계, 성공 확률)
    """
    before = int(item.get("enhance_level", 0))
    if before >= MAX_ENHANCE_LEVEL or int(item.get("quantity", 0)) < 2:
        return False, before, before, 0.0

    target = before + 1
    success_rate = enhancement_success_rate(target)
    item["quantity"] -= 1

    if random.random() < success_rate:
        item["enhance_level"] = target
        return True, before, target, success_rate

    if enhancement_failure_drops(before):
        item["enhance_level"] = max(0, before - 1)
    return False, before, int(item["enhance_level"]), success_rate


def set_bonus() -> tuple[int, int, float]:
    counts: dict[str, int] = {}
    for slot in EQUIPMENT_SLOTS:
        item = equipped_item(slot)
        if item:
            counts[item.get("set_name", "기타")] = counts.get(item.get("set_name", "기타"), 0) + 1
    attack = defense = 0
    xp_bonus = 0.0
    for count in counts.values():
        if count >= 2:
            attack += 3
        if count >= 3:
            defense += 3
        if count >= 5:
            xp_bonus += 0.10
    return attack, defense, xp_bonus


def equipment_attack() -> int:
    base = sum(item_attack(item) for slot in EQUIPMENT_SLOTS if (item := equipped_item(slot)))
    return base + set_bonus()[0]


def equipment_defense() -> int:
    base = sum(item_defense(item) for slot in EQUIPMENT_SLOTS if (item := equipped_item(slot)))
    return base + set_bonus()[1]


def equipment_totals_for_map(equipped_map: dict[str, str | None]) -> tuple[int, int, float]:
    """장착 맵을 기준으로 장비 공격/방어/XP 세트 보너스를 계산한다."""
    counts: dict[str, int] = {}
    attack = 0
    defense = 0

    for slot in EQUIPMENT_SLOTS:
        item_id = equipped_map.get(slot)
        item = get_item(item_id)
        if not item or item.get("item_type") != "equipment":
            continue
        attack += item_attack(item)
        defense += item_defense(item)
        set_name = str(item.get("set_name", "기타"))
        counts[set_name] = counts.get(set_name, 0) + 1

    xp_bonus = 0.0
    for count in counts.values():
        if count >= 2:
            attack += 3
        if count >= 3:
            defense += 3
        if count >= 5:
            xp_bonus += 0.10

    return attack, defense, xp_bonus


def equipment_swap_delta(candidate: dict[str, Any]) -> tuple[int, int, str]:
    """후보 장비 장착 시 현재 장비 총 공격/방어 변화량과 비교 대상 이름을 반환한다."""
    slot = str(candidate.get("slot", ""))
    current_item = equipped_item(slot)
    current_map = dict(st.session_state.equipped_items)
    current_attack, current_defense, _ = equipment_totals_for_map(current_map)

    preview_map = dict(current_map)
    preview_map[slot] = str(candidate.get("item_id"))
    preview_attack, preview_defense, _ = equipment_totals_for_map(preview_map)

    compare_name = (
        f"{current_item['name']} +{current_item['enhance_level']}"
        if current_item
        else "빈 슬롯"
    )
    return preview_attack - current_attack, preview_defense - current_defense, compare_name


def format_stat_delta(value: int) -> str:
    if value > 0:
        return f"+{value}"
    return str(value)


def player_attack() -> int:
    return 5 + st.session_state.intelligence * 2 + equipment_attack() + CLASS_INFO[st.session_state.extra["job"]]["attack_bonus"]


def player_defense() -> int:
    return st.session_state.wisdom + equipment_defense() + CLASS_INFO[st.session_state.extra["job"]]["defense_bonus"]


def class_xp_bonus(category: str) -> float:
    job = st.session_state.extra["job"]
    if job == "데이터 분석가":
        return 0.10
    if job == "Python 개발자" and category == "Python":
        return 0.20
    if job == "SQL 마법사" and category == "SQL":
        return 0.20
    if job == "통계학자" and category == "통계":
        return 0.20
    return 0.0


def gain_xp(amount: int, category: str = "") -> list[str]:
    bonus = class_xp_bonus(category) + set_bonus()[2] + team_xp_bonus(category)
    if st.session_state.extra.get("xp_boost"):
        bonus += 1.0
        st.session_state.extra["xp_boost"] = False
    final = max(1, round(amount * (1 + bonus)))
    st.session_state.xp += final
    messages = [f"✨ 경험치 {final} XP를 획득했습니다."]
    while st.session_state.xp >= required_xp(st.session_state.level):
        st.session_state.xp -= required_xp(st.session_state.level)
        st.session_state.level += 1
        st.session_state.stat_points += 3
        st.session_state.player_hp = max_hp()
        messages.append(f"🎉 레벨 {st.session_state.level} 달성! 스탯 포인트 3개 획득")
    return messages


def add_item(item: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    normalized = normalize_inventory_item(item)
    existing = get_item(normalized["item_id"])
    if existing:
        existing["quantity"] += normalized.get("quantity", 1)
        persist()
        return existing, True
    st.session_state.inventory.append(normalized)
    persist()
    return normalized, False


def potion_count() -> int:
    item = get_item(HEALING_POTION_ID)
    return int(item.get("quantity", 0)) if item else 0


def use_potion() -> str:
    item = get_item(HEALING_POTION_ID)
    if not item or item["quantity"] <= 0:
        return "회복 물약이 없습니다."
    if st.session_state.player_hp >= max_hp():
        return "이미 체력이 가득 찼습니다."
    before = st.session_state.player_hp
    st.session_state.player_hp = min(max_hp(), before + max(1, round(max_hp() * POTION_HEAL_RATE)))
    item["quantity"] -= 1
    if item["quantity"] <= 0:
        st.session_state.inventory = [x for x in st.session_state.inventory if x.get("item_id") != HEALING_POTION_ID]
    persist()
    return f"🧪 체력 {st.session_state.player_hp - before} 회복"


def rest() -> str:
    if st.session_state.monster:
        return "전투 중에는 휴식할 수 없습니다."
    if st.session_state.player_hp >= max_hp():
        return "이미 체력이 가득 찼습니다."
    if st.session_state.battle_tickets < 1:
        return "전투권 1개가 필요합니다."
    before = st.session_state.player_hp
    st.session_state.player_hp = min(max_hp(), before + max(1, round(max_hp() * REST_HEAL_RATE)))
    st.session_state.battle_tickets -= 1
    persist()
    return f"🏕️ 전투권 1개를 소모해 체력 {st.session_state.player_hp - before} 회복"


def get_daily_world_progress(world: dict[str, Any] | None = None) -> dict[str, Any]:
    """현재 활성 월드 기준의 일일 퀘스트 진행도를 반환한다."""
    if world is None:
        world = get_active_learning_world()

    if world is None:
        p = st.session_state.extra.setdefault(
            "daily_progress", {"correct": 0, "sql": 0, "battles": 0}
        )
        return {
            "correct": int(p.get("correct", 0)),
            "focus": int(p.get("sql", 0)),
            "battles": int(p.get("battles", 0)),
            "focus_subject_id": None,
            "focus_subject_name": "선택 분야",
        }

    world_id = str(int(world["id"]))
    progress_map = st.session_state.extra.setdefault("daily_progress_by_world", {})
    subjects = world.get("subjects", []) or []

    if subjects:
        index = (date.today().toordinal() + int(world["id"])) % len(subjects)
        focus_subject = subjects[index]
        focus_id = str(focus_subject.get("subject_id", ""))
        focus_name = str(focus_subject.get("name", focus_id or "선택 분야"))
    else:
        focus_id = ""
        focus_name = "선택 분야"

    p = progress_map.setdefault(
        world_id,
        {
            "correct": 0,
            "focus": 0,
            "battles": 0,
            "focus_subject_id": focus_id,
            "focus_subject_name": focus_name,
        },
    )
    p.setdefault("correct", 0)
    p.setdefault("focus", 0)
    p.setdefault("battles", 0)
    p["focus_subject_id"] = focus_id
    p["focus_subject_name"] = focus_name
    return p


def record_study(
    category: str,
    *,
    subject_id: str | None = None,
    world_id: int | None = None,
) -> None:
    extra = st.session_state.extra
    today = today_str()
    last = extra.get("last_study_date")
    if last != today:
        if last and date.fromisoformat(last) == date.today() - timedelta(days=1):
            extra["streak"] += 1
        else:
            extra["streak"] = 1
        extra["last_study_date"] = today

    extra["total_correct"] += 1
    extra["category_correct"][category] = extra["category_correct"].get(category, 0) + 1

    active_world = get_active_learning_world()
    if active_world is not None and (world_id is None or int(active_world["id"]) == int(world_id)):
        p = get_daily_world_progress(active_world)
        p["correct"] += 1
        if subject_id and subject_id == p.get("focus_subject_id"):
            p["focus"] += 1
    else:
        extra["daily_progress"]["correct"] += 1


def evaluate_achievements() -> list[str]:
    extra = st.session_state.extra
    unlocked = []
    for name, data in ACHIEVEMENTS.items():
        if name not in extra["achievements"] and data["condition"](extra):
            extra["achievements"].append(name)
            unlocked.append(name)
            if name == "첫걸음":
                st.session_state.xp += 20
            elif name == "Python 입문자":
                st.session_state.battle_tickets += 2
            elif name == "끈기의 분석가":
                rare = random.choice([item for item in ITEMS if item["rarity"] in {"희귀", "영웅"}])
                add_item(rare)
            elif name == "오답 수집가":
                extra["memory_shards"] += 5
            elif name == "던전 정복자":
                if "데이터 정복자" not in extra["titles"]:
                    extra["titles"].append("데이터 정복자")
            elif name == "첫 포획":
                add_capture_item(GREAT_BALL_ID, 1)
            elif name == "몬스터 수집가":
                add_capture_item(ULTRA_BALL_ID, 1)
                if "데이터 테이머" not in extra["titles"]:
                    extra["titles"].append("데이터 테이머")
    persist()
    return unlocked


def daily_complete(world: dict[str, Any] | None = None) -> bool:
    p = get_daily_world_progress(world)
    return p["correct"] >= 3 and p["focus"] >= 1 and p["battles"] >= 1


def daily_claimed(world: dict[str, Any] | None = None) -> bool:
    if world is None:
        world = get_active_learning_world()
    if world is None:
        return bool(st.session_state.extra.get("daily_claimed", False))
    return bool(
        st.session_state.extra.setdefault("daily_claimed_by_world", {}).get(
            str(int(world["id"])), False
        )
    )


def claim_daily(world: dict[str, Any] | None = None) -> str:
    extra = st.session_state.extra
    if world is None:
        world = get_active_learning_world()
    if not daily_complete(world):
        return "아직 일일 퀘스트를 완료하지 않았습니다."
    if daily_claimed(world):
        return "오늘 보상은 이미 받았습니다."

    if world is None:
        extra["daily_claimed"] = True
    else:
        extra.setdefault("daily_claimed_by_world", {})[str(int(world["id"]))] = True

    st.session_state.xp += 50
    st.session_state.battle_tickets += 2
    add_item({"item_id": HEALING_POTION_ID, "name": "회복 물약", "item_type": "consumable", "quantity": 1})
    persist()
    return "🎁 일일 보상: XP 50, 전투권 2개, 회복 물약 1개"


def random_event() -> str:
    if random.random() > 0.22:
        return ""
    events = [
        ("상인", "수상한 데이터 상인이 전투권 1개를 물약 1개로 교환했습니다."),
        ("보물", "숨겨진 캐시에서 XP 20을 발견했습니다."),
        ("함정", "데이터 누수 함정으로 체력 5를 잃었습니다."),
    ]
    kind, text = random.choice(events)
    if kind == "상인" and st.session_state.battle_tickets > 0:
        st.session_state.battle_tickets -= 1
        add_item({"item_id": HEALING_POTION_ID, "name": "회복 물약", "item_type": "consumable", "quantity": 1})
    elif kind == "보물":
        st.session_state.xp += 20
    elif kind == "함정":
        st.session_state.player_hp = max(1, st.session_state.player_hp - 5)
    st.session_state.extra["event_log"].append({"time": datetime.now().isoformat(timespec="minutes"), "text": text})
    persist()
    return text


def log_question_attempt(
    question: dict[str, Any],
    user_answer: Any,
    is_correct: bool,
    *,
    xp_earned: int = 0,
    attempt_type: str = "quest",
) -> None:
    """현재 문제 제출 결과를 학습 기록 DB에 남긴다."""
    try:
        record_question_attempt(
            user_id=current_user_id(),
            world_id=question.get("_world_id") or question.get("world_id"),
            question_id=question.get("id"),
            category=question.get("_display_category", question.get("category", "기타")),
            category_key=question.get("_category_key", question.get("category_key", question.get("category"))),
            subject_id=question.get("_subject_id") or question.get("subject_id"),
            difficulty=question.get("difficulty", ""),
            question_type=get_effective_question_type(question),
            is_correct=is_correct,
            user_answer=user_answer,
            correct_answer=question.get("answer", ""),
            xp_earned=xp_earned,
            attempt_type=attempt_type,
        )
    except Exception as error:
        # 학습 기록 저장 실패가 실제 문제 풀이를 막지 않도록 한다.
        st.session_state.event_message = f"⚠️ 학습 기록 저장 실패: {error}"


def complete_question(question: dict[str, Any], user_answer: Any = "") -> list[str]:
    mark_question_as_solved(int(question["id"]))
    category = question.get("_display_category", question["category"])
    record_study(
        category,
        subject_id=question.get("_subject_id"),
        world_id=question.get("_world_id"),
    )

    # gain_xp 내부와 같은 계산을 먼저 해두어 실제 획득 XP를 로그에 저장한다.
    bonus = class_xp_bonus(category) + set_bonus()[2] + team_xp_bonus(category)
    if st.session_state.extra.get("xp_boost"):
        bonus += 1.0
    earned_xp = max(1, round(int(question["xp"]) * (1 + bonus)))

    messages = gain_xp(int(question["xp"]), category)
    log_question_attempt(
        question,
        user_answer=user_answer,
        is_correct=True,
        xp_earned=earned_xp,
        attempt_type="quest",
    )

    st.session_state.battle_tickets += 1
    messages.append("🎫 전투권 1개 획득")
    event = random_event()
    if event:
        messages.append("🎲 " + event)
    achievements = evaluate_achievements()
    if achievements:
        messages.append("🏆 업적 달성: " + ", ".join(achievements))
    persist()
    return messages


def save_wrong_question(question: dict[str, Any]) -> None:
    wrongs = st.session_state.extra["wrong_questions"]
    if not any(w.get("id") == question["id"] for w in wrongs):
        wrongs.append({
            "id": question["id"],
            "category": question.get("_display_category", question["category"]),
            "category_key": question.get("_category_key", question["category"]),
            "difficulty": question["difficulty"],
            "question_type": question.get("question_type", "multiple_choice"),
            "question": question["question"],
            "options": question.get("options"),
            "answer": question.get("answer"),
            "keywords": question.get("keywords"),
            "explanation": question.get("explanation"),
            "subject_id": question.get("_subject_id"),
            "world_id": question.get("_world_id"),
        })
    persist()


def use_skill(skill: str) -> str:
    extra = st.session_state.extra
    if skill not in SKILLS:
        return "알 수 없는 스킬입니다."
    used = extra["skill_uses"].get(skill, 0)
    if used >= SKILLS[skill]["daily_limit"]:
        return "오늘 사용 횟수를 모두 소진했습니다."
    if skill == "데이터 스캔":
        q = st.session_state.current_question
        if not q or q.get("question_type") != "multiple_choice" or not q.get("options"):
            return "현재 문제에는 사용할 수 없습니다."
        wrong_options = [x for x in q["options"] if x != q["answer"]]
        if not wrong_options:
            return "제거할 보기가 없습니다."
        st.session_state.hidden_option = random.choice(wrong_options)
    elif skill == "쿼리 가속":
        extra["xp_boost"] = True
    elif skill == "응급 복구":
        if not st.session_state.monster:
            return "전투 중에만 사용할 수 있습니다."
        st.session_state.player_hp = min(max_hp(), st.session_state.player_hp + max(1, round(max_hp() * 0.2)))
    extra["skill_uses"][skill] = used + 1
    persist()
    return f"✨ {skill} 사용"


def reset_question() -> None:
    st.session_state.current_question = None
    st.session_state.answer_checked = False
    st.session_state.answer_is_correct = None
    st.session_state.answer_message = ""
    st.session_state.hidden_option = None


def load_question(
    category: str,
    difficulty: str,
    *,
    world: dict[str, Any] | None = None,
    subject: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    기존 하드코딩 카테고리와 새 학습 월드 카테고리를 모두 지원한다.

    동적 월드에서는 DB 내부 category를
    world_<id>__<subject_id> 형태로 사용하여
    서로 다른 월드의 문제은행이 섞이지 않게 한다.
    """
    if world is not None and subject is not None:
        subject_id = str(subject["subject_id"])
        category_key = build_world_category_key(
            world_id=int(world["id"]),
            subject_id=subject_id,
        )

        try:
            result = ensure_world_subject_pool(
                world=world,
                subject_id=subject_id,
                difficulty=difficulty,
                minimum_count=5,
                generate_count=5,
            )
            if result.get("errors"):
                st.session_state.pool_message = f"⚠️ {result['errors'][0]}"
            elif result["api_called"]:
                st.session_state.pool_message = (
                    f"🤖 Gemini 1회 호출로 {result['saved_count']}개 문제를 문제은행에 추가했습니다."
                )
            else:
                st.session_state.pool_message = (
                    f"📚 저장된 미풀이 문제 {result['after_count']}개를 사용합니다. API 호출 없음"
                )
        except Exception as error:
            st.session_state.pool_message = f"⚠️ {friendly_ai_error(error)}"

        questions = get_available_questions(
            category_key,
            difficulty,
            1,
        )

        if not questions:
            return None

        question = questions[0]
        question["_category_key"] = category_key
        question["_display_category"] = str(subject.get("name", subject_id))
        question["_subject_id"] = subject_id
        question["_world_id"] = int(world["id"])
        question["_world_topic"] = str(world.get("topic", ""))
        return question

    # 기존 데이터분석 월드 하위 호환
    try:
        result = ensure_question_pool(
            category=category,
            difficulty=difficulty,
            minimum_count=5,
            generate_count=5,
        )
        if result.get("errors"):
            st.session_state.pool_message = f"⚠️ {result['errors'][0]}"
        elif result["api_called"]:
            st.session_state.pool_message = (
                f"🤖 Gemini 1회 호출로 {result['saved_count']}개 문제를 문제은행에 추가했습니다."
            )
        else:
            st.session_state.pool_message = (
                f"📚 저장된 미풀이 문제 {result['after_count']}개를 사용합니다. API 호출 없음"
            )
    except Exception as error:
        st.session_state.pool_message = f"⚠️ {friendly_ai_error(error)}"

    questions = get_available_questions(category, difficulty, 1)
    return questions[0] if questions else None



def get_effective_question_type(question: dict[str, Any]) -> str:
    """
    DB의 question_type을 그대로 신뢰하지 않고 실제 문제 형태까지 함께 본다.
    과거 subjective로 저장된 빈칸/키워드형 문제도 즉시 short_answer로 처리한다.
    """
    qtype = str(question.get("question_type", "")).strip()
    options = question.get("options") or []

    if qtype == "multiple_choice" or (not qtype and options):
        return "multiple_choice"

    if qtype == "short_answer":
        return "short_answer"

    if looks_like_legacy_short_answer(
        question_text=str(question.get("question", "")),
        answer=question.get("answer", ""),
        question_type=qtype,
    ):
        return "short_answer"

    return "subjective"


def normalize_question_text(text: str) -> str:
    text = re.sub(r"\s+/\s+", "\n", str(text).strip())
    return re.sub(r";\s+(?=[A-Za-z_][A-Za-z0-9_]*\s*=)", ";\n", text)


def find_code_start(text: str) -> int | None:
    patterns = [r"\b[A-Za-z_][A-Za-z0-9_]*\s*=\s*", r"\bSELECT\s+", r"\bWITH\s+", r"\bdf\[", r"\bpd\.", r"\bprint\("]
    starts = [m.start() for pattern in patterns if (m := re.search(pattern, text, flags=re.I))]
    return min(starts) if starts else None


def normalize_answer_text(text: str) -> str:
    """객관식/단답형/레거시 주관식 비교용 문자열 정규화."""
    normalized = str(text or "").strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip(" .,!?:;\"'`")
    return normalized


def normalize_short_token(text: str) -> str:
    """단답형 비교용. SQL/영문 키워드의 공백과 단순 문장부호 차이를 흡수한다."""
    text = normalize_answer_text(text)
    # 'HAVING 절'처럼 답 뒤에 붙는 흔한 한국어 표현은 허용
    text = re.sub(r"\s*(절|문|키워드|명령어)$", "", text)
    text = re.sub(r"[\[\](){}]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_short_answers(correct_answer: Any) -> list[str]:
    """
    단답형 정답 저장값을 항상 리스트로 변환한다.

    지원 형식
    - 실제 list: ["EXISTS"]
    - JSON 문자열: '["EXISTS"]'
    - Python 리스트 문자열: "['EXISTS']"
    - 레거시 문자열: 'GROUP BY / HAVING'
    """
    if isinstance(correct_answer, list):
        return [str(x).strip() for x in correct_answer if str(x).strip()]

    raw = str(correct_answer or "").strip()
    if not raw:
        return []

    # 1) JSON 배열 문자열
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]
    except Exception:
        pass

    # 2) 과거 DB에 Python repr 형태로 들어간 리스트
    #    예: ['EXISTS'], ['DENSE_RANK()', 'DENSE_RANK']
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, (list, tuple)):
            return [str(x).strip() for x in parsed if str(x).strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]
    except Exception:
        pass

    # 3) 레거시 문자열
    parts = re.split(r"\s*(?:\|\||\||\n|,|/|→)\s*", raw)
    parts = [p.strip() for p in parts if p.strip()]
    return parts if parts else [raw]


def is_multi_slot_short_answer(question_text: str, expected: list[str]) -> bool:
    """
    answers 배열이 '허용 가능한 동의어 목록'인지
    '여러 빈칸의 순차 정답'인지 판별한다.

    예:
    - ["DENSE_RANK()", "DENSE_RANK"] -> 둘 중 하나만 맞으면 정답
    - ["군집", "클러스터"] -> 둘 중 하나만 맞으면 정답
    - (가), (나)에 순서대로 작성 -> 두 답을 모두 순서대로 요구
    """
    if len(expected) <= 1:
        return False

    text = str(question_text or "")

    multi_slot_patterns = [
        r"\(가\).+\(나\)",
        r"\[가\].+\[나\]",
        r"빈칸\s*\(?가\)?.*\(?나\)?",
        r"순서대로",
        r"각\s*빈칸",
        r"두\s*빈칸",
        r"2개\s*빈칸",
    ]

    return any(
        re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        for pattern in multi_slot_patterns
    )


def get_short_answer_placeholder(question_text: str, expected: list[str] | None = None) -> str:
    """정답 내용을 노출하지 않고 입력 형식만 안내한다."""
    text = str(question_text or "")
    expected = expected or []

    if is_multi_slot_short_answer(text, expected):
        return "예: 첫 번째 답 / 두 번째 답"

    if re.search(r"SQL|쿼리|키워드|함수명|명령어|연산자", text, flags=re.IGNORECASE):
        return "키워드 또는 함수명을 직접 입력하세요"

    if re.search(r"숫자|값|개수|몇\s*개|확률|비율|평균|중앙값", text, flags=re.IGNORECASE):
        return "숫자 또는 값을 직접 입력하세요"

    return "짧은 정답을 직접 입력하세요"


def evaluate_short_answer(
    user_answer: str,
    correct_answer: Any,
    question_text: str = "",
) -> tuple[bool, str]:
    """
    단답형 전용 채점.

    핵심 규칙
    1. ["EXISTS"]처럼 저장돼 있어도 사용자는 EXISTS만 입력하면 된다.
    2. ["DENSE_RANK()", "DENSE_RANK"]처럼 여러 값이 있더라도
       보통은 '허용 가능한 정답 표현'이므로 하나만 맞으면 정답이다.
    3. 문제에 (가)/(나), '순서대로', '두 빈칸'이 명시된 경우에만
       여러 답을 모두 순서대로 요구한다.
    """
    user_raw = str(user_answer or "").strip()
    if not user_raw:
        return False, "답변을 입력해주세요."

    expected = parse_short_answers(correct_answer)
    if not expected:
        return False, "저장된 정답 정보를 확인할 수 없습니다."

    expected_norm = [normalize_short_token(x) for x in expected]
    expected_norm = [x for x in expected_norm if x]

    if not expected_norm:
        return False, "저장된 정답 정보를 확인할 수 없습니다."

    user_joined = normalize_short_token(user_raw)

    # -----------------------------------------------------
    # A. 여러 빈칸 문제
    # -----------------------------------------------------
    if is_multi_slot_short_answer(question_text, expected):
        user_parts = re.split(r"\s*(?:\|\||\||\n|,|/|→)\s*", user_raw)
        user_parts = [
            normalize_short_token(x)
            for x in user_parts
            if str(x).strip()
        ]

        if user_parts == expected_norm:
            return True, "정답입니다."

        # 사용자가 구분자 없이 한 줄로 이어 쓴 경우도 허용
        expected_joined = normalize_short_token(" ".join(expected))
        if user_joined == expected_joined:
            return True, "정답입니다."

        return (
            False,
            "정답이 아닙니다. 여러 빈칸은 순서대로 입력해주세요.",
        )

    # -----------------------------------------------------
    # B. 일반 단답형: expected 배열은 '허용 정답 목록'
    # -----------------------------------------------------
    for candidate in expected_norm:
        if user_joined == candidate:
            return True, "정답입니다."

        # 함수 괄호 유무 허용
        # DENSE_RANK() == DENSE_RANK
        user_no_paren = re.sub(r"\(\)$", "", user_joined).strip()
        candidate_no_paren = re.sub(r"\(\)$", "", candidate).strip()
        if user_no_paren == candidate_no_paren:
            return True, "정답입니다."

        # HAVING 절 / EXISTS 키워드 같은 짧은 부가 표현 허용
        if len(candidate) <= 40 and (
            user_joined == candidate
            or user_joined.startswith(candidate + " ")
        ):
            return True, "정답입니다."

    return False, "정답이 아닙니다. 허용되는 짧은 용어/값 중 하나를 입력해주세요."


def evaluate_subjective_answer(
    user_answer: str,
    correct_answer: str,
    keywords: list[str] | None,
) -> tuple[bool, str]:
    """과거 DB에 남아 있는 subjective 문제를 위한 호환 채점."""
    user_normalized = normalize_answer_text(user_answer)
    correct_normalized = normalize_answer_text(correct_answer)

    if not user_normalized:
        return False, "답변을 입력해주세요."

    # 과거 subjective 중 실제로는 단답형인 문제를 먼저 단답 방식으로 판정
    if correct_normalized and len(correct_normalized) <= 80:
        short_ok, short_msg = evaluate_short_answer(user_answer, correct_answer)
        if short_ok:
            return True, short_msg

    if correct_normalized and user_normalized == correct_normalized:
        return True, "정답입니다."

    cleaned_keywords = [
        normalize_answer_text(keyword)
        for keyword in (keywords or [])
        if str(keyword).strip()
    ]
    cleaned_keywords = list(dict.fromkeys(cleaned_keywords))
    matched_keywords = [k for k in cleaned_keywords if k and k in user_normalized]

    if not cleaned_keywords:
        if len(user_answer.strip()) >= 50:
            return True, "정답입니다."
        return False, "핵심 내용을 조금 더 구체적으로 작성해주세요."

    match_ratio = len(matched_keywords) / len(cleaned_keywords)
    if len(user_answer.strip()) >= 50 and match_ratio >= 0.4:
        return True, "정답입니다."

    return False, "핵심 내용과 구체적인 근거를 더 작성하세요."

def render_question(text: str, category: str, *, connected: bool = False) -> None:
    text = normalize_question_text(text)
    start = find_code_start(text)
    question_class = "question-box quest-question-box" if connected else "question-box"
    if start is None:
        st.markdown(f'<div class="{question_class}">{html.escape(text).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        return
    description, code = text[:start].strip(), text[start:].strip()
    if description:
        st.markdown(f'<div class="{question_class}">{html.escape(description)}</div>', unsafe_allow_html=True)
    category_lower = str(category).lower()
    if "python" in category_lower or "파이썬" in category_lower:
        language = "python"
    elif "sql" in category_lower or "쿼리" in category_lower:
        language = "sql"
    else:
        language = "text"
    st.code(code, language=language)


def rarity_emoji(rarity: str) -> str:
    return {
        "일반": "🟢",
        "고급": "🔵",
        "희귀": "🟣",
        "영웅": "🟠",
    }.get(rarity, "👾")


def world_subject_map(world: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(subject.get("subject_id")): subject
        for subject in world.get("subjects", [])
        if subject.get("subject_id")
    }


def world_monsters_for_region(
    world: dict[str, Any],
    region: dict[str, Any],
) -> list[dict[str, Any]]:
    subject_id = str(region.get("subject_id", ""))
    return [
        monster for monster in world.get("monsters", [])
        if str(monster.get("subject_id", "")) == subject_id
    ]


def get_world_boss(world: dict[str, Any]) -> dict[str, Any] | None:
    boss = world.get("world_data", {}).get("boss")
    return boss if isinstance(boss, dict) and boss.get("monster_id") else None


def dynamic_monster_catalog(world: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = [dict(monster) for monster in world.get("monsters", [])]
    boss = get_world_boss(world)
    if boss:
        boss_copy = dict(boss)
        boss_copy["rarity"] = "영웅"
        boss_copy["base_capture_rate"] = 0.0
        boss_copy["boss"] = True
        catalog.append(boss_copy)
    return catalog


def create_world_monster(
    world: dict[str, Any],
    region: dict[str, Any] | None,
    encounter_type: str = "hunt",
    *,
    boss: bool = False,
) -> dict[str, Any]:
    subjects = world_subject_map(world)
    world_id = int(world["id"])

    if boss:
        template = get_world_boss(world)
        if template is None:
            raise ValueError("현재 월드에 보스 정보가 없습니다.")
        subject_id = str(template.get("subject_id", ""))
        region_index = max(1, len(world.get("regions", []))) + 1
        rarity = "영웅"
        base_hp = 110 + region_index * 15
        base_attack = 11 + region_index
        base_defense = 3 + region_index
        base_xp = 70 + region_index * 10
        capture_rate = 0.0
        region_name = "최종 보스 영역"
    else:
        if region is None:
            raise ValueError("일반 몬스터 생성에는 region이 필요합니다.")
        pool = world_monsters_for_region(world, region)
        if not pool:
            raise ValueError(f"{region.get('name', '지역')}에 출현 몬스터가 없습니다.")
        template = random.choice(pool)
        subject_id = str(template.get("subject_id", region.get("subject_id", "")))
        regions = world.get("regions", [])
        region_index = next(
            (idx for idx, item in enumerate(regions, start=1)
             if item.get("region_id") == region.get("region_id")),
            1,
        )
        rarity = str(template.get("rarity", "일반"))
        base_hp = 28 + region_index * 12
        base_attack = 3 + region_index * 2
        base_defense = 1 + region_index
        base_xp = 12 + region_index * 8
        capture_rate = float(template.get("base_capture_rate", 0.35))
        region_name = str(region.get("name", "미지의 지역"))

    rarity_multiplier = {
        "일반": 1.0,
        "고급": 1.12,
        "희귀": 1.28,
        "영웅": 1.55,
    }.get(rarity, 1.0)

    subject = subjects.get(subject_id, {})
    subject_name = str(subject.get("name", subject_id or "범용"))
    category_key = (
        build_world_category_key(world_id, subject_id)
        if subject_id
        else subject_name
    )
    xp_bonus = {
        "일반": 0.04,
        "고급": 0.06,
        "희귀": 0.08,
        "영웅": 0.10,
    }.get(rarity, 0.04)

    monster_id = str(template.get("monster_id", f"monster_{uuid.uuid4().hex[:8]}"))
    dex_key = f"world_{world_id}__{monster_id}"
    max_monster_hp = max(10, round(base_hp * rarity_multiplier))

    monster = {
        "world_id": world_id,
        "monster_id": monster_id,
        "dex_key": dex_key,
        "region_id": None if region is None else region.get("region_id"),
        "region_name": region_name,
        "name": str(template.get("name", "이름 없는 몬스터")),
        "emoji": "👑" if boss else rarity_emoji(rarity),
        "element": subject_name,
        "rarity": rarity,
        "category": subject_name,
        "category_key": category_key,
        "subject_id": subject_id,
        "description": str(template.get("description", "")),
        "base_capture_rate": capture_rate,
        "max_hp": max_monster_hp,
        "hp": max_monster_hp,
        "attack": max(1, round(base_attack * rarity_multiplier)),
        "defense": max(0, round(base_defense * rarity_multiplier)),
        "xp": max(1, round(base_xp * rarity_multiplier)),
        "xp_bonus": xp_bonus,
        "boss": boss,
        "encounter_type": encounter_type,
        "drop_buff": encounter_type == "dungeon",
    }
    record_seen(dex_key)
    return monster



def dismantle_reward(item: dict[str, Any]) -> int:
    """장비 희귀도와 강화 단계에 따라 분해 파편 보상을 계산한다."""
    rarity_base = {"일반": 1, "고급": 2, "희귀": 4, "영웅": 7}.get(str(item.get("rarity", "일반")), 1)
    enhance = max(0, int(item.get("enhance_level", 0)))
    return max(1, rarity_base + enhance // 2)


def dismantle_equipment(item_id: str, quantity: int = 1) -> tuple[bool, str]:
    """장착하지 않은 장비를 분해해 강화 파편으로 변환한다."""
    item = get_item(item_id)
    if not item or item.get("item_type") != "equipment":
        return False, "분해할 장비를 찾을 수 없습니다."
    if item_id in st.session_state.equipped_items.values():
        return False, "장착 중인 장비는 먼저 해제해야 합니다."
    qty = max(1, min(int(quantity), int(item.get("quantity", 0))))
    if int(item.get("quantity", 0)) - qty < 0:
        return False, "보유 수량이 부족합니다."
    reward_each = dismantle_reward(item)
    reward = reward_each * qty
    item["quantity"] = int(item.get("quantity", 0)) - qty
    if item["quantity"] <= 0:
        st.session_state.inventory = [x for x in st.session_state.inventory if x.get("item_id") != item_id]
    st.session_state.extra["dismantle_shards"] = int(st.session_state.extra.get("dismantle_shards", 0)) + reward
    persist()
    return True, f"♻️ {item.get('name', item_id)} {qty}개 분해 · 강화 파편 +{reward}"


def world_intro_seen(world_id: int) -> bool:
    return bool(st.session_state.extra.setdefault("world_intro_seen", {}).get(str(int(world_id)), False))


def mark_world_intro_seen(world_id: int) -> None:
    st.session_state.extra.setdefault("world_intro_seen", {})[str(int(world_id))] = True
    persist()


def build_world_intro_lines(world: dict[str, Any]) -> list[str]:
    data = world.get("world_data", {}) or {}
    boss = data.get("boss", {}) if isinstance(data.get("boss", {}), dict) else {}
    world_name = str(world.get("world_name", "이름 없는 세계"))
    topic = str(world.get("topic", "배움"))
    goal = str(world.get("goal", "새로운 지식을 익히는 것"))
    boss_name = str(boss.get("name", "최후의 수호자"))
    return [
        "오래전, 아직 정복되지 않은 지식의 세계가 있었다.",
        f"그 세계의 이름은 「{world_name}」.",
        f"이곳에서 당신은 「{topic}」의 영역을 하나씩 탐험하게 된다.",
        "배움은 힘이 되고, 힘은 새로운 길을 연다.",
        f"당신이 이 세계에서 이루어야 할 목표는 「{goal}」.",
        "그러나 여정의 끝에는 모든 배움을 시험하는 존재가 기다리고 있다.",
        f"그 이름은 「{boss_name}」.",
        "배우고, 성장하고, 세계를 변화시켜라.",
        "이제 첫 번째 여정을 시작한다.",
    ]


def subject_building_name(subject_name: str, index: int) -> str:
    suffixes = ["연구소", "훈련관", "공방", "기록원", "관측탑"]
    return f"{subject_name} {suffixes[(index - 1) % len(suffixes)]}"


def build_subject_buildings(world: dict[str, Any]) -> list[dict[str, Any]]:
    """학습 기록을 게임 내 건물 상태로 번역한다. AI 호출 없음."""
    if not world:
        return []
    attempts = get_question_attempts(current_user_id(), world_id=int(world["id"]), days=None)
    rows = []
    for idx, subject in enumerate(world.get("subjects", []), start=1):
        sid = str(subject.get("subject_id", ""))
        name = str(subject.get("name", sid or f"분야 {idx}"))
        records = [a for a in attempts if str(a.get("subject_id") or "") == sid or str(a.get("category") or "") == name]
        total = len(records)
        correct = sum(1 for a in records if bool(a.get("is_correct")))
        accuracy = correct / total if total else 0.0
        # 학습량과 정확도를 함께 반영한 단순 성장 단계. 밸런스는 후반 조정 예정.
        score = total * 8 + accuracy * 40
        level = 1 if score < 25 else 2 if score < 55 else 3 if score < 90 else 4 if score < 130 else 5
        if total == 0:
            state = "미개척"
            message = "학습 기록이 없습니다. 첫 퀘스트를 수행해 건물의 기반을 세우세요."
        elif accuracy < 0.5:
            state = "보수 필요"
            message = "정확도가 낮습니다. 기초 퀘스트로 건물을 보강하세요."
        elif accuracy < 0.75:
            state = "강화 권장"
            message = "성장 중입니다. 반복 학습으로 다음 단계 강화를 노려보세요."
        else:
            state = "안정 성장"
            message = "안정적으로 성장하고 있습니다. 더 높은 난이도로 확장할 수 있습니다."
        rows.append({
            "subject_id": sid, "subject_name": name, "building_name": subject_building_name(name, idx),
            "level": level, "attempts": total, "correct": correct, "accuracy": accuracy,
            "state": state, "message": message,
        })
    return rows


def boss_threshold_crossed(monster: dict[str, Any], before_hp: int, after_hp: int) -> int | None:
    """75/50/25% 임계점을 처음 통과했는지 반환한다."""
    if not monster.get("boss"):
        return None
    max_hp_value = max(1, int(monster.get("max_hp", 1)))
    seen = monster.setdefault("boss_quiz_thresholds", [])
    for threshold in (75, 50, 25):
        hp_line = max_hp_value * threshold / 100
        if threshold not in seen and before_hp > hp_line >= max(0, after_hp):
            seen.append(threshold)
            return threshold
    return None


def prepare_boss_quiz(world: dict[str, Any], monster: dict[str, Any], threshold: int) -> dict[str, Any] | None:
    subject_id = str(monster.get("subject_id", ""))
    subject = next((s for s in world.get("subjects", []) if str(s.get("subject_id", "")) == subject_id), None)
    if subject is None and world.get("subjects"):
        subject = world["subjects"][0]
    if subject is None:
        return None
    # 보스 문제도 기존 문제은행을 우선 사용하고, 부족할 때만 기존 생성 파이프라인을 따른다.
    question = load_question(str(subject.get("name", "")), "보통", world=world, subject=subject)
    if question:
        question = dict(question)
        question["_boss_threshold"] = threshold
    return question


def evaluate_boss_quiz(question: dict[str, Any], user_answer: Any) -> tuple[bool, str]:
    qtype = get_effective_question_type(question)
    if qtype == "multiple_choice":
        ok = str(user_answer).strip() == str(question.get("answer", "")).strip()
        return ok, "정답입니다." if ok else "오답입니다."
    if qtype == "short_answer":
        return evaluate_short_answer(str(user_answer or ""), question.get("answer"), str(question.get("question", "")))
    ok = normalize_answer_text(str(user_answer or "")) == normalize_answer_text(str(question.get("answer", "")))
    return ok, "정답입니다." if ok else "오답입니다."


def resolve_boss_quiz(question: dict[str, Any], user_answer: Any) -> tuple[bool, str]:
    ok, message = evaluate_boss_quiz(question, user_answer)
    try:
        mark_question_as_solved(int(question["id"]))
    except Exception:
        pass
    log_question_attempt(question, user_answer, ok, xp_earned=0, attempt_type="boss")
    if ok:
        st.session_state.extra["boss_attack_buff_turns"] = 3
        result = "✨ 정답! 다음 3회의 공격력이 25% 증가합니다."
    else:
        save_wrong_question(question)
        result = "📚 오답입니다. 추가 패널티는 없으며 오답 던전에 기록됩니다."
    persist()
    return ok, result


def drop_equipment(drop_bonus: float = 0.0) -> dict[str, Any] | None:
    chance = min(0.35 + st.session_state.luck * 0.05 + CLASS_INFO[st.session_state.extra["job"]]["drop_bonus"] + drop_bonus, 0.95)
    if random.random() > chance:
        return None
    weights = [RARITY_WEIGHTS[item["rarity"]] + (st.session_state.luck if item["rarity"] in {"희귀", "영웅"} else 0) for item in ITEMS]
    return {**random.choices(ITEMS, weights=weights, k=1)[0], "item_type": "equipment", "enhance_level": 0, "quantity": 1}


st.markdown("""
<style>
.block-container{max-width:1200px;padding-top:1.2rem}
.quest-card{padding:1.2rem 1.4rem;border:1px solid rgba(120,120,140,.25);border-radius:16px;background:rgba(120,120,160,.06);margin:.8rem 0 1rem}
.question-box{padding:1.1rem 1.2rem;border-left:5px solid #6c7ae0;border-radius:8px;background:rgba(110,120,190,.07);font-size:1.08rem;font-weight:600;line-height:1.8}
.game-card{padding:1rem;border:1px solid rgba(120,120,140,.2);border-radius:12px;background:rgba(100,110,160,.05);margin:.4rem 0}
.boss{border:2px solid rgba(180,80,80,.5)}

/* Sidebar HUD */
[data-testid="stSidebar"]{border-right:1px solid rgba(120,120,140,.16)}
[data-testid="stSidebar"] .block-container{padding-top:1.05rem;padding-left:1rem;padding-right:1rem}
.hud-card{padding:1rem;border:1px solid rgba(110,120,160,.22);border-radius:18px;background:linear-gradient(145deg,rgba(104,117,214,.10),rgba(120,120,160,.035));box-shadow:0 8px 24px rgba(20,25,50,.045);margin:.25rem 0 .75rem}
.hud-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:800;opacity:.58;margin-bottom:.25rem}
.hud-title{font-size:1.05rem;font-weight:800;line-height:1.25;margin-bottom:.14rem}
.hud-subtitle{font-size:.75rem;opacity:.67;margin-bottom:.8rem}
.hud-level-row{display:flex;justify-content:space-between;align-items:end;margin:.15rem 0 .3rem}
.hud-level{font-size:1.75rem;font-weight:900;line-height:1}
.hud-xp{font-size:.72rem;opacity:.68}
.hud-bar{height:8px;border-radius:999px;background:rgba(120,120,140,.14);overflow:hidden;margin-bottom:.9rem}
.hud-bar-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#ff4b4b,#ff8a5b)}
.hud-hp-row{display:flex;justify-content:space-between;align-items:center;font-size:.78rem;margin-bottom:.35rem}
.hud-hp-value{font-weight:800}
.hud-hp-bar{height:7px;border-radius:999px;background:rgba(120,120,140,.14);overflow:hidden;margin-bottom:.85rem}
.hud-hp-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#ef476f,#ff6b81)}
.hud-grid{display:grid;grid-template-columns:1fr 1fr;gap:.42rem}
.hud-stat{padding:.55rem .6rem;border:1px solid rgba(120,120,140,.15);border-radius:12px;background:rgba(255,255,255,.34)}
.hud-stat-label{font-size:.66rem;opacity:.62;margin-bottom:.08rem}
.hud-stat-value{font-size:.88rem;font-weight:800}
.hud-resource-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.38rem;margin-top:.48rem}
.hud-resource{text-align:center;padding:.5rem .2rem;border-radius:11px;background:rgba(110,120,160,.06);border:1px solid rgba(120,120,140,.12)}
.hud-resource-value{font-size:.9rem;font-weight:850}
.hud-resource-label{font-size:.60rem;opacity:.58;margin-top:.08rem}
.hud-section-title{font-size:.72rem;letter-spacing:.08em;font-weight:850;opacity:.63;margin:.9rem 0 .38rem}
.hud-world{padding:.78rem .85rem;border:1px solid rgba(70,160,130,.19);border-radius:14px;background:rgba(55,180,130,.055);margin-bottom:.6rem}
.hud-world-name{font-size:.92rem;font-weight:850;margin-bottom:.12rem}
.hud-world-topic{font-size:.70rem;opacity:.66}
.hud-stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:.4rem;margin-bottom:.55rem}
.hud-mini-stat{display:flex;justify-content:space-between;align-items:center;padding:.48rem .55rem;border-radius:10px;background:rgba(110,120,160,.045);border:1px solid rgba(120,120,140,.11);font-size:.72rem}
.hud-mini-stat b{font-size:.82rem}
[data-testid="stSidebar"] hr{margin:.75rem 0}
[data-testid="stSidebar"] .stButton button{border-radius:10px;min-height:2.25rem;font-size:.75rem}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label{font-size:.72rem;font-weight:700}

/* ACTIONS help button: Streamlit 기본 popover 화살표 없이 hover 설명만 표시 */
[data-testid="stSidebar"] .action-help-anchor + div button,
[data-testid="stSidebar"] button[aria-label="action help"]{
    min-width:2.25rem!important;
    width:2.25rem!important;
    padding-left:0!important;
    padding-right:0!important;
    justify-content:center!important;
    font-weight:800!important;
}

/* Learning World */
.world-hero{padding:1.35rem 1.45rem;border:1px solid rgba(88,118,190,.20);border-radius:20px;background:linear-gradient(145deg,rgba(91,111,201,.10),rgba(55,180,130,.045));box-shadow:0 10px 28px rgba(20,25,50,.045);margin:.5rem 0 1rem}
.world-hero-top{display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;margin-bottom:.9rem}
.world-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.22rem}
.world-name{font-size:1.45rem;font-weight:900;line-height:1.2;margin-bottom:.22rem}
.world-meta{font-size:.83rem;opacity:.72}
.world-badge{display:inline-flex;align-items:center;gap:.28rem;padding:.34rem .58rem;border-radius:999px;font-size:.68rem;font-weight:850;border:1px solid rgba(47,150,110,.23);background:rgba(47,180,120,.08);white-space:nowrap}
.world-goal{padding:.78rem .9rem;border-radius:13px;background:rgba(255,255,255,.38);border:1px solid rgba(120,120,140,.12);font-size:.80rem;line-height:1.55;margin-bottom:.78rem}
.world-description{font-size:.82rem;line-height:1.65;opacity:.78;margin-bottom:.9rem}
.world-content-strip{display:flex;align-items:center;justify-content:space-around;gap:.7rem;padding:.78rem .9rem;border-radius:13px;background:rgba(255,255,255,.34);border:1px solid rgba(120,120,140,.12);margin-top:.15rem}
.world-content-item{display:flex;align-items:center;gap:.34rem;white-space:nowrap;font-size:.76rem;opacity:.78}
.world-content-item b{font-size:.96rem;opacity:1;color:var(--text-color)}
.world-nav-card{padding:.78rem .9rem .66rem;border:1px solid rgba(120,120,140,.16);border-radius:15px;background:rgba(255,255,255,.30);min-height:92px;margin-bottom:.45rem}
.world-nav-title{font-size:.88rem;font-weight:850;margin-bottom:.16rem}
.world-nav-copy{font-size:.69rem;opacity:.62;line-height:1.45}
.world-create-head{margin-bottom:.25rem}
.world-create-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:850;opacity:.56}
.world-create-title{font-size:1.05rem;font-weight:900;margin:.08rem 0 .15rem}
.world-create-copy{font-size:.73rem;opacity:.66;line-height:1.5}
@media (max-width:700px){.world-content-strip{align-items:flex-start;flex-direction:column;gap:.35rem}}

/* Quest */
.quest-page-head{margin:.15rem 0 .9rem}
.quest-page-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.18rem}
.quest-page-title{font-size:1.35rem;font-weight:900;line-height:1.22;margin-bottom:.20rem}
.quest-page-copy{font-size:.76rem;opacity:.66;line-height:1.5}
.quest-recommend{padding:.72rem .86rem;border:1px solid rgba(120,120,140,.16);border-radius:15px;background:linear-gradient(145deg,rgba(255,193,79,.075),rgba(110,120,210,.035));margin:.35rem 0 .35rem}
.quest-recommend-top{display:flex;align-items:center;justify-content:space-between;gap:.65rem;margin-bottom:.35rem}
.quest-recommend-eyebrow{font-size:.61rem;letter-spacing:.09em;font-weight:850;opacity:.56;margin-bottom:.07rem}
.quest-recommend-title{font-size:.95rem;font-weight:900;line-height:1.2}
.quest-recommend-badge{padding:.22rem .44rem;border-radius:999px;background:rgba(255,180,50,.08);border:1px solid rgba(220,150,30,.18);font-size:.62rem;font-weight:800;white-space:nowrap}
.quest-recommend-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:.34rem;margin:.36rem 0 .28rem}
.quest-recommend-stat{padding:.38rem .50rem;border:1px solid rgba(120,120,140,.10);border-radius:9px;background:rgba(255,255,255,.27)}
.quest-recommend-stat span{display:block;font-size:.57rem;opacity:.56;margin-bottom:.05rem}
.quest-recommend-stat b{font-size:.75rem}
.quest-recommend-reason{font-size:.67rem;line-height:1.4;opacity:.64}
.quest-prep-head{margin-bottom:.25rem}
.quest-prep-eyebrow{font-size:.68rem;letter-spacing:.09em;font-weight:850;opacity:.56;margin-bottom:.10rem}
.quest-prep-title{font-size:1rem;font-weight:900;margin-bottom:.10rem}
.quest-prep-copy{font-size:.71rem;opacity:.64;line-height:1.45}
.quest-card{padding:1.05rem 1.15rem;border:1px solid rgba(100,110,190,.20);border-radius:17px;background:linear-gradient(145deg,rgba(101,111,210,.095),rgba(255,255,255,.18));margin:.9rem 0 .75rem;box-shadow:0 8px 22px rgba(20,25,50,.035)}
.quest-card-connected{margin-bottom:0;border-radius:17px 17px 0 0;border-bottom-color:rgba(100,110,190,.10);box-shadow:none}
.quest-question-box{margin-top:0;border:1px solid rgba(100,110,190,.18);border-top:0;border-left:5px solid #6c7ae0;border-radius:0 0 12px 12px;background:linear-gradient(180deg,rgba(110,120,190,.075),rgba(110,120,190,.045));box-shadow:0 8px 20px rgba(20,25,50,.03)}
.quest-card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:.8rem}
.quest-card-eyebrow{font-size:.65rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.12rem}
.quest-card-title{font-size:1.08rem;font-weight:900;line-height:1.3}
.quest-card-world{font-size:.68rem;opacity:.60;margin-top:.12rem}
.quest-reward-row{display:flex;gap:.38rem;flex-wrap:wrap;margin-top:.65rem}
.quest-chip{display:inline-flex;align-items:center;padding:.29rem .50rem;border:1px solid rgba(120,120,140,.14);border-radius:999px;background:rgba(255,255,255,.38);font-size:.67rem;font-weight:750}
@media (max-width:700px){.quest-recommend-stats{grid-template-columns:1fr}.quest-card-top,.quest-recommend-top{flex-direction:column}}

/* Dungeon / Adventure UI */
.battle-ready-card{
    padding:1rem 1.05rem;
    border:1px solid rgba(120,120,150,.18);
    border-radius:16px;
    background:linear-gradient(145deg,rgba(110,120,180,.07),rgba(255,255,255,.18));
    margin:.55rem 0 .55rem;
}
.battle-ready-eyebrow{font-size:.66rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.25rem}
.battle-ready-title{font-size:1rem;font-weight:850;margin-bottom:.7rem}
.battle-ready-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem}
.battle-ready-stat{padding:.58rem .65rem;border:1px solid rgba(120,120,145,.13);border-radius:11px;background:rgba(255,255,255,.34)}
.battle-ready-label{font-size:.65rem;opacity:.6;margin-bottom:.1rem}
.battle-ready-value{font-size:.9rem;font-weight:850}
.battle-ball-line{font-size:.69rem;opacity:.68;margin-top:.55rem}
.hunt-section-head{margin:.5rem 0 .8rem}
.hunt-section-eyebrow{font-size:.66rem;letter-spacing:.09em;font-weight:850;opacity:.55;margin-bottom:.15rem}
.hunt-section-title{font-size:1.18rem;font-weight:900;margin-bottom:.12rem}
.hunt-section-copy{font-size:.76rem;opacity:.66}
.hunt-region-card{min-height:8.7rem;padding:.9rem .95rem;border:1px solid rgba(120,120,145,.17);border-radius:14px;background:rgba(105,115,165,.045);margin-bottom:.42rem}
.hunt-region-title{font-size:.95rem;font-weight:900;margin-bottom:.3rem}
.hunt-region-subject{font-size:.72rem;font-weight:750;opacity:.76;margin-bottom:.25rem}
.hunt-region-meta{font-size:.69rem;opacity:.65;margin-bottom:.4rem}
.hunt-region-desc{font-size:.72rem;line-height:1.48;opacity:.72;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
@media (max-width:800px){.battle-ready-grid{grid-template-columns:repeat(2,1fr)}}


/* Active Battle UI */
.battle-stage-head{margin:.15rem 0 .7rem}
.battle-stage-eyebrow{font-size:.66rem;letter-spacing:.10em;font-weight:850;opacity:.55;margin-bottom:.12rem}
.battle-stage-title{font-size:1.12rem;font-weight:900;margin-bottom:.12rem}
.battle-stage-copy{font-size:.72rem;opacity:.64}
.combat-card{padding:1rem 1.05rem;border:1px solid rgba(120,120,145,.17);border-radius:17px;background:linear-gradient(145deg,rgba(255,255,255,.28),rgba(105,115,175,.055));min-height:12.4rem;box-shadow:0 7px 20px rgba(20,25,50,.025)}
.combat-card.monster{background:linear-gradient(145deg,rgba(118,91,170,.075),rgba(255,255,255,.24))}
.combat-eyebrow{font-size:.61rem;letter-spacing:.09em;font-weight:850;opacity:.54;margin-bottom:.14rem}
.combat-name{font-size:1.08rem;font-weight:900;line-height:1.3;margin-bottom:.12rem}
.combat-meta{font-size:.69rem;opacity:.63;margin-bottom:.72rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.combat-hp-row{display:flex;justify-content:space-between;align-items:center;font-size:.72rem;margin-bottom:.28rem}
.combat-hp-row b{font-size:.82rem}
.combat-hp-track{height:9px;background:rgba(120,120,140,.13);border-radius:999px;overflow:hidden;margin-bottom:.72rem}
.combat-hp-fill-player{height:100%;border-radius:999px;background:linear-gradient(90deg,#32a4ff,#5b73f2)}
.combat-hp-fill-monster{height:100%;border-radius:999px;background:linear-gradient(90deg,#9b6bde,#6650b8)}
.combat-stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.38rem}
.combat-stat{padding:.48rem .55rem;border:1px solid rgba(120,120,145,.11);border-radius:10px;background:rgba(255,255,255,.28)}
.combat-stat span{display:block;font-size:.59rem;opacity:.55;margin-bottom:.04rem}
.combat-stat b{font-size:.78rem}
.combat-monster-copy{font-size:.68rem;opacity:.66;line-height:1.45;margin-top:.55rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.combat-capture{display:inline-flex;margin-top:.55rem;padding:.25rem .48rem;border-radius:999px;border:1px solid rgba(105,82,170,.18);background:rgba(111,86,185,.06);font-size:.64rem;font-weight:800}
.combat-actions-label{font-size:.66rem;letter-spacing:.10em;font-weight:850;opacity:.58;margin:.78rem 0 .38rem}
.combat-ball-note{font-size:.68rem;opacity:.62;padding-top:1.82rem;line-height:1.45}
.combat-log{padding:.62rem .78rem;border:1px solid rgba(120,120,145,.14);border-radius:13px;background:rgba(105,115,165,.035);margin-top:.68rem}
.combat-log-title{font-size:.70rem;font-weight:900;margin-bottom:.28rem}
.combat-log-line{font-size:.70rem;line-height:1.42;padding:.09rem 0;border-bottom:1px solid rgba(120,120,145,.07)}
.combat-log-line:last-child{border-bottom:0}
@media (max-width:800px){.combat-card{min-height:auto}.combat-stat-grid{grid-template-columns:1fr 1fr}}


/* Inventory */
.inventory-head{margin:.15rem 0 .8rem}
.inventory-eyebrow{font-size:.68rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.12rem}
.inventory-title{font-size:1.22rem;font-weight:900;margin-bottom:.14rem}
.inventory-copy{font-size:.74rem;opacity:.66;line-height:1.5}
.equip-slot-card{min-height:8.2rem;padding:.78rem .72rem;border:1px solid rgba(120,120,145,.16);border-radius:14px;background:linear-gradient(145deg,rgba(105,115,175,.055),rgba(255,255,255,.22));margin-bottom:.38rem}
.equip-slot-label{font-size:.66rem;letter-spacing:.07em;font-weight:850;opacity:.58;margin-bottom:.28rem}
.equip-slot-name{font-size:.88rem;font-weight:900;line-height:1.3;margin-bottom:.20rem}
.equip-slot-meta{font-size:.65rem;opacity:.62;line-height:1.4}
.item-card{min-height:9.7rem;padding:.88rem .92rem;border:1px solid rgba(120,120,145,.16);border-radius:14px;background:rgba(255,255,255,.24);margin:.28rem 0 .38rem}
.item-card-top{display:flex;justify-content:space-between;gap:.5rem;align-items:flex-start;margin-bottom:.42rem}
.item-name{font-size:.92rem;font-weight:900;line-height:1.3}
.item-badge{font-size:.60rem;font-weight:800;padding:.20rem .38rem;border-radius:999px;border:1px solid rgba(120,120,145,.14);background:rgba(110,120,180,.05);white-space:nowrap}
.item-meta{font-size:.66rem;opacity:.64;line-height:1.45;margin-bottom:.5rem}
.item-stats{display:flex;gap:.7rem;font-size:.74rem;font-weight:800}
.item-equipped{margin-top:.45rem;font-size:.63rem;font-weight:850;opacity:.72}
.item-compare{margin-top:.48rem;padding:.42rem .5rem;border-radius:9px;background:rgba(110,120,170,.045);font-size:.64rem;line-height:1.45}
.item-compare-title{opacity:.58;margin-bottom:.12rem}
.item-compare-values{display:flex;gap:.65rem;font-weight:850;flex-wrap:wrap}
.item-compare-positive{color:#168a58}
.item-compare-negative{color:#c24d5a}
.item-compare-neutral{opacity:.58}
.bulk-enhance-note{font-size:.68rem;opacity:.62;line-height:1.45;padding-top:.35rem}
.inventory-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:.45rem;margin:.3rem 0 .75rem}
.inventory-summary-card{padding:.62rem .7rem;border:1px solid rgba(120,120,145,.13);border-radius:11px;background:rgba(110,120,170,.04)}
.inventory-summary-label{font-size:.62rem;opacity:.58;margin-bottom:.07rem}
.inventory-summary-value{font-size:.88rem;font-weight:900}
.enhance-card{min-height:10.4rem;padding:.88rem .92rem;border:1px solid rgba(120,120,145,.16);border-radius:14px;background:linear-gradient(145deg,rgba(255,185,75,.045),rgba(255,255,255,.20));margin:.28rem 0 .38rem}
.enhance-title-row{display:flex;align-items:center;gap:.38rem;margin:.12rem 0 .58rem}
.enhance-title-text{font-size:1.18rem;font-weight:900}
.enhance-subtitle-row{display:flex;align-items:center;gap:.32rem;margin:.12rem 0 .42rem}
.enhance-subtitle-text{font-size:.78rem;font-weight:850;letter-spacing:.02em}
.help-dot{display:inline-flex;align-items:center;justify-content:center;width:1.15rem;height:1.15rem;border-radius:999px;border:1px solid rgba(110,115,135,.25);background:rgba(255,255,255,.72);font-size:.66rem;font-weight:900;line-height:1;cursor:help;opacity:.72;vertical-align:middle}
.help-dot:hover{opacity:1;background:rgba(110,120,180,.08)}
.enhance-card{min-height:8.2rem}
.enhance-preview{margin-top:.45rem;padding:.42rem .5rem;border-radius:9px;background:rgba(110,120,170,.045);font-size:.66rem;line-height:1.5}
.consumable-card{padding:.85rem .9rem;border:1px solid rgba(120,120,145,.15);border-radius:14px;background:rgba(255,255,255,.24);min-height:7.6rem}
.consumable-name{font-size:.86rem;font-weight:900;margin-bottom:.22rem}
.consumable-count{font-size:1.35rem;font-weight:900;margin-bottom:.14rem}
.consumable-meta{font-size:.65rem;opacity:.62}
@media (max-width:800px){.inventory-summary{grid-template-columns:1fr}.equip-slot-card{min-height:auto}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 학습 기록 기반 취약 분야 자동 추천
# =========================================================
def build_weakness_recommendation(
    world: dict[str, Any] | None,
    *,
    min_attempts: int = 2,
    recent_days: int = 30,
) -> dict[str, Any] | None:
    """AI 호출 없이 question_attempts 로그만으로 다음 학습 분야를 추천한다.

    우선순위는 낮은 정답률을 가장 크게 보고, 최근 오답 비율과 충분한 표본 수를
    보조적으로 반영한다. 아직 기록이 적으면 가장 덜 풀어본 분야를 추천한다.
    """
    if not world or not world.get("subjects"):
        return None

    world_id = int(world["id"])
    subjects = world.get("subjects", [])
    attempts = get_question_attempts(
        current_user_id(),
        world_id=world_id,
        days=recent_days,
    )

    # 최근 기록이 전혀 없으면 전체 기록을 한 번 더 확인한다.
    if not attempts:
        attempts = get_question_attempts(
            current_user_id(),
            world_id=world_id,
            days=None,
        )

    rows: list[dict[str, Any]] = []
    for subject in subjects:
        subject_id = str(subject.get("subject_id", "")).strip()
        subject_name = str(subject.get("name", subject_id or "분야")).strip()
        subject_attempts = [
            attempt
            for attempt in attempts
            if (
                str(attempt.get("subject_id") or "") == subject_id
                or str(attempt.get("category") or "") == subject_name
            )
        ]

        total = len(subject_attempts)
        correct = sum(1 for attempt in subject_attempts if bool(attempt.get("is_correct")))
        accuracy = (correct / total) if total else None

        recent_slice = subject_attempts[:5]
        recent_wrong_ratio = (
            sum(1 for attempt in recent_slice if not bool(attempt.get("is_correct"))) / len(recent_slice)
            if recent_slice
            else 0.0
        )

        rows.append({
            "subject_id": subject_id,
            "subject_name": subject_name,
            "description": subject.get("description", ""),
            "attempts": total,
            "correct": correct,
            "accuracy": accuracy,
            "recent_wrong_ratio": recent_wrong_ratio,
        })

    eligible = [row for row in rows if row["attempts"] >= min_attempts]

    if eligible:
        for row in eligible:
            # 정답률 75%, 최근 오답 20%, 표본 신뢰도 5%.
            sample_confidence = min(row["attempts"] / 10, 1.0)
            row["weakness_score"] = (
                (1.0 - float(row["accuracy"])) * 0.75
                + float(row["recent_wrong_ratio"]) * 0.20
                + sample_confidence * 0.05
            )

        target = max(
            eligible,
            key=lambda row: (row["weakness_score"], row["attempts"]),
        )
        accuracy_pct = float(target["accuracy"]) * 100

        if accuracy_pct < 50:
            difficulty = "쉬움"
            reason = "정답률이 50% 미만이라 핵심 개념을 다시 다지는 것이 우선입니다."
        elif accuracy_pct < 75:
            difficulty = "보통"
            reason = "기본 개념은 일부 익혔지만 적용 문제에서 보강이 필요한 구간입니다."
        else:
            difficulty = "어려움"
            reason = "정답률은 높지만 현재 월드에서 상대적으로 가장 보완 우선순위가 높은 분야입니다."

        return {
            **target,
            "difficulty": difficulty,
            "reason": reason,
            "mode": "weakness",
        }

    # 최소 표본이 없으면 가장 덜 풀어본 분야를 먼저 추천하여 진단 데이터를 모은다.
    target = min(rows, key=lambda row: row["attempts"])
    return {
        **target,
        "difficulty": "쉬움",
        "reason": (
            f"아직 분야별 풀이 기록이 {min_attempts}회 미만이라 취약도를 확정하기 어렵습니다. "
            "먼저 이 분야의 쉬움 문제를 풀어 진단 데이터를 쌓는 것을 추천합니다."
        ),
        "mode": "diagnostic",
        "weakness_score": None,
    }


def render_recommendation_card(
    recommendation: dict[str, Any] | None,
    *,
    title: str = "🎯 자동 학습 추천",
) -> None:
    if not recommendation:
        st.info("추천을 만들 학습 월드 또는 세부 분야가 없습니다.")
        return

    st.markdown(f"### {title}")
    r1, r2, r3 = st.columns(3)
    r1.metric("추천 분야", recommendation["subject_name"])
    r2.metric("추천 난이도", recommendation["difficulty"])
    if recommendation["attempts"]:
        r3.metric("현재 정답률", f"{float(recommendation['accuracy']) * 100:.1f}%")
    else:
        r3.metric("현재 정답률", "기록 없음")

    st.write(recommendation["reason"])
    if recommendation.get("description"):
        st.caption(recommendation["description"])

    if recommendation["attempts"]:
        st.caption(
            f"최근 분석 기록: {recommendation['attempts']}회 풀이 · "
            f"{recommendation['correct']}회 정답"
        )
    else:
        st.caption("아직 풀이 기록이 없어 진단용 학습을 먼저 추천합니다.")


