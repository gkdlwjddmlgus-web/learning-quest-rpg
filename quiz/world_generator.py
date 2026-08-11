from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

from quiz.ai_support import call_gemini, get_cached_json, set_cached_json
from quiz.repository import (
    LOCAL_USER_ID,
    create_learning_world,
    get_learning_worlds,
    set_active_learning_world,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEMINI_MODEL = "gemini-flash-latest"


def load_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        if api_key:
            return str(api_key)
    except Exception:
        pass
    raise RuntimeError("GEMINI_API_KEY를 찾을 수 없습니다.")


def get_client():
    return genai.Client(api_key=load_api_key())


WORLD_SCHEMA = {
    "type": "object",
    "properties": {
        "world_name": {"type": "string"},
        "world_description": {"type": "string"},
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["subject_id", "name", "description"],
            },
        },
        "regions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "region_id": {"type": "string"},
                    "name": {"type": "string"},
                    "subject_id": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["region_id", "name", "subject_id", "description"],
            },
        },
        "monsters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "monster_id": {"type": "string"},
                    "name": {"type": "string"},
                    "subject_id": {"type": "string"},
                    "rarity": {"type": "string"},
                    "description": {"type": "string"},
                    "base_capture_rate": {"type": "number"},
                },
                "required": [
                    "monster_id",
                    "name",
                    "subject_id",
                    "rarity",
                    "description",
                    "base_capture_rate",
                ],
            },
        },
        "boss": {
            "type": "object",
            "properties": {
                "monster_id": {"type": "string"},
                "name": {"type": "string"},
                "subject_id": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["monster_id", "name", "subject_id", "description"],
        },
    },
    "required": [
        "world_name",
        "world_description",
        "subjects",
        "regions",
        "monsters",
        "boss",
    ],
}


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _world_cache_payload(
    topic: str,
    goal: str,
    learner_level: str,
    game_theme: str,
) -> dict[str, str]:
    return {
        "model": GEMINI_MODEL,
        "topic": _normalize(topic),
        "goal": _normalize(goal),
        "learner_level": _normalize(learner_level),
        "game_theme": _normalize(game_theme),
    }


def build_world_prompt(topic: str, goal: str, learner_level: str, game_theme: str) -> str:
    return f"""
사용자가 공부하려는 내용을 기반으로 학습용 RPG 게임 세계를 설계하라.

[학습 주제]
{topic}

[학습 목표]
{goal}

[현재 학습 수준]
{learner_level}

[게임 테마]
{game_theme}

조건:
1. 학습 주제를 정확히 5개의 핵심 세부 분야로 나눈다.
2. 각 세부 분야마다 하나의 사냥 지역을 만든다.
3. 총 15마리의 일반 몬스터를 만든다. 각 분야마다 3마리씩 만든다.
4. rarity는 일반 / 고급 / 희귀 중 하나만 사용한다.
5. base_capture_rate는 0.15~0.70 사이로 한다.
   일반은 0.50~0.70, 고급은 0.30~0.50, 희귀는 0.15~0.30을 권장한다.
6. 전체 학습 주제를 대표하는 보스 몬스터 1마리를 만든다.
7. subject_id, region_id, monster_id는 영어 소문자와 underscore만 사용한다.
8. 모든 설명은 한국어로 작성한다.
9. 학습자의 목표를 달성하는 데 실제로 필요한 커리큘럼 중심으로 구성한다.
10. 각 region/monster/boss의 subject_id는 subjects에 실제 존재하는 값이어야 한다.
"""



def _subject_key(value: Any) -> str:
    """subject 참조 비교용 키. 공백/기호 차이 정도는 동일하게 취급한다."""
    return re.sub(r"[^0-9a-zA-Z가-힣]+", "", str(value or "").strip().lower())


def _best_subject_id(value: Any, subjects: list[dict[str, Any]]) -> str | None:
    """AI가 subject_id 대신 이름/유사 문자열을 반환했을 때 가장 가까운 subject_id를 찾는다."""
    raw = _subject_key(value)
    if not raw:
        return None

    candidates: list[tuple[float, str]] = []
    for subject in subjects:
        subject_id = str(subject.get("subject_id", "")).strip()
        if not subject_id:
            continue
        aliases = {
            _subject_key(subject_id),
            _subject_key(subject.get("name", "")),
        }
        aliases.discard("")
        if raw in aliases:
            return subject_id
        score = max((SequenceMatcher(None, raw, alias).ratio() for alias in aliases), default=0.0)
        candidates.append((score, subject_id))

    if not candidates:
        return None
    score, subject_id = max(candidates, key=lambda item: item[0])
    return subject_id if score >= 0.55 else None


def repair_learning_world_relations(world: dict[str, Any]) -> dict[str, Any]:
    """
    Gemini가 올바른 JSON 형태를 반환했지만 region/monster/boss의 subject_id만
    subjects와 어긋난 경우 추가 API 호출 없이 관계를 보정한다.

    학습 커리큘럼 자체를 새로 만들지는 않고, subject 연결 관계만 복구한다.
    """
    if not isinstance(world, dict):
        return world

    subjects = world.get("subjects")
    regions = world.get("regions")
    monsters = world.get("monsters")
    boss = world.get("boss")
    if not isinstance(subjects, list) or not subjects:
        return world

    subject_ids = [str(s.get("subject_id", "")).strip() for s in subjects]
    subject_ids = [sid for sid in subject_ids if sid]
    if not subject_ids:
        return world

    # 1) 지역: 유사 참조를 먼저 고치고, 그래도 미해결이면 5개 지역/5개 분야 순서를 이용한다.
    if isinstance(regions, list):
        for idx, region in enumerate(regions):
            if not isinstance(region, dict):
                continue
            current = str(region.get("subject_id", "")).strip()
            if current in subject_ids:
                continue
            resolved = _best_subject_id(current, subjects)
            if resolved is None and idx < len(subject_ids):
                resolved = subject_ids[idx]
            if resolved:
                region["subject_id"] = resolved

    # 2) 몬스터: 먼저 유사 참조를 고친다.
    if isinstance(monsters, list):
        for monster in monsters:
            if not isinstance(monster, dict):
                continue
            current = str(monster.get("subject_id", "")).strip()
            if current in subject_ids:
                continue
            resolved = _best_subject_id(current, subjects)
            if resolved:
                monster["subject_id"] = resolved

        # 각 분야 정확히 3마리 조건을 복구한다.
        counts = {sid: 0 for sid in subject_ids}
        overflow: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []

        for monster in monsters:
            if not isinstance(monster, dict):
                continue
            sid = str(monster.get("subject_id", "")).strip()
            if sid not in counts:
                unresolved.append(monster)
                continue
            if counts[sid] < 3:
                counts[sid] += 1
            else:
                overflow.append(monster)

        deficits: list[str] = []
        for sid in subject_ids:
            deficits.extend([sid] * max(0, 3 - counts[sid]))

        to_reassign = unresolved + overflow
        for monster, sid in zip(to_reassign, deficits):
            monster["subject_id"] = sid

    # 3) 보스: 잘못된 참조만 가장 가까운 분야로 복구한다.
    if isinstance(boss, dict):
        current = str(boss.get("subject_id", "")).strip()
        if current not in subject_ids:
            resolved = _best_subject_id(current, subjects) or subject_ids[-1]
            boss["subject_id"] = resolved

    return world


def validate_learning_world(world: dict[str, Any]) -> None:
    required = ["world_name", "world_description", "subjects", "regions", "monsters", "boss"]
    for key in required:
        if key not in world:
            raise ValueError(f"월드 데이터에 '{key}'가 없습니다.")

    subjects = world["subjects"]
    regions = world["regions"]
    monsters = world["monsters"]
    boss = world["boss"]

    if not isinstance(subjects, list) or len(subjects) != 5:
        raise ValueError("subjects는 정확히 5개여야 합니다.")
    subject_ids = [str(item.get("subject_id", "")).strip() for item in subjects]
    if any(not item for item in subject_ids) or len(set(subject_ids)) != 5:
        raise ValueError("subject_id가 비어 있거나 중복되었습니다.")

    if not isinstance(regions, list) or len(regions) != 5:
        raise ValueError("regions는 정확히 5개여야 합니다.")
    for region in regions:
        if str(region.get("subject_id", "")).strip() not in subject_ids:
            raise ValueError("region의 subject_id가 subjects와 연결되지 않습니다.")

    if not isinstance(monsters, list) or len(monsters) != 15:
        raise ValueError("monsters는 정확히 15마리여야 합니다.")

    allowed = {"일반", "고급", "희귀"}
    counts = {subject_id: 0 for subject_id in subject_ids}
    monster_ids: list[str] = []
    for monster in monsters:
        monster_id = str(monster.get("monster_id", "")).strip()
        subject_id = str(monster.get("subject_id", "")).strip()
        rarity = str(monster.get("rarity", "")).strip()
        rate = float(monster.get("base_capture_rate", 0))
        if not monster_id:
            raise ValueError("monster_id가 비어 있습니다.")
        monster_ids.append(monster_id)
        if subject_id not in subject_ids:
            raise ValueError("monster의 subject_id가 subjects와 연결되지 않습니다.")
        counts[subject_id] += 1
        if rarity not in allowed:
            raise ValueError(f"허용되지 않은 rarity: {rarity}")
        if not 0.15 <= rate <= 0.70:
            raise ValueError(f"base_capture_rate 범위 오류: {rate}")

    if len(set(monster_ids)) != len(monster_ids):
        raise ValueError("중복된 monster_id가 있습니다.")
    if any(count != 3 for count in counts.values()):
        raise ValueError("각 세부 분야에는 정확히 3마리의 몬스터가 필요합니다.")
    if str(boss.get("subject_id", "")).strip() not in subject_ids:
        raise ValueError("boss의 subject_id가 subjects와 연결되지 않습니다.")


def generate_learning_world(
    topic: str,
    goal: str,
    learner_level: str = "초급",
    game_theme: str = "판타지",
) -> dict[str, Any]:
    topic = str(topic).strip()
    goal = str(goal).strip() or f"{topic}의 핵심 개념을 체계적으로 학습한다."
    learner_level = str(learner_level).strip()
    game_theme = str(game_theme).strip()

    if not topic:
        raise ValueError("학습 주제를 입력해야 합니다.")

    cache_payload = _world_cache_payload(topic, goal, learner_level, game_theme)
    cached = get_cached_json("learning_world", cache_payload)
    if isinstance(cached, dict):
        cached = repair_learning_world_relations(cached)
        validate_learning_world(cached)
        set_cached_json("learning_world", cache_payload, cached)
        cached["_cache_hit"] = True
        return cached

    client = get_client()

    def _request():
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=build_world_prompt(topic, goal, learner_level, game_theme),
            config=types.GenerateContentConfig(
                system_instruction=(
                    "너는 학습 커리큘럼 설계자이자 RPG 게임 콘텐츠 디자이너다. "
                    "학습적으로 타당한 커리큘럼을 만들고 이를 수집형 RPG 세계로 변환한다."
                ),
                temperature=0.8,
                response_mime_type="application/json",
                response_json_schema=WORLD_SCHEMA,
            ),
        )

    response = call_gemini(_request)
    if not response.text:
        raise RuntimeError("Gemini가 월드 데이터를 반환하지 않았습니다.")

    world = json.loads(response.text)
    world = repair_learning_world_relations(world)
    validate_learning_world(world)
    set_cached_json("learning_world", cache_payload, world)
    world["_cache_hit"] = False
    return world


def _existing_equivalent_world(
    topic: str,
    goal: str,
    learner_level: str,
    game_theme: str,
    user_id: str,
) -> dict[str, Any] | None:
    target = (
        _normalize(topic),
        _normalize(goal),
        _normalize(learner_level),
        _normalize(game_theme),
    )
    for world in get_learning_worlds(user_id):
        current = (
            _normalize(world.get("topic", "")),
            _normalize(world.get("goal", "")),
            _normalize(world.get("learner_level", "")),
            _normalize(world.get("game_theme", "")),
        )
        if current == target:
            return world
    return None


def _record_to_generated(world: dict[str, Any], cache_hit: bool) -> dict[str, Any]:
    world_data = world.get("world_data", {}) or {}
    return {
        "world_id": int(world["id"]),
        "world_name": world["world_name"],
        "world_description": world_data.get("world_description", ""),
        "subjects": world.get("subjects", []),
        "regions": world.get("regions", []),
        "monsters": world.get("monsters", []),
        "boss": world_data.get("boss", {}),
        "_cache_hit": cache_hit,
        "_reused_existing_world": True,
    }


def generate_and_save_learning_world(
    topic: str,
    goal: str,
    learner_level: str = "초급",
    game_theme: str = "판타지",
    user_id: str = LOCAL_USER_ID,
) -> dict[str, Any]:
    topic = str(topic).strip()
    goal = str(goal).strip() or f"{topic}의 핵심 개념을 체계적으로 학습한다."

    # 같은 설정의 월드가 이미 DB에 있으면 Gemini를 전혀 호출하지 않고 재사용한다.
    existing = _existing_equivalent_world(topic, goal, learner_level, game_theme, user_id)
    if existing is not None:
        set_active_learning_world(int(existing["id"]), user_id)
        return _record_to_generated(existing, cache_hit=True)

    world = generate_learning_world(topic, goal, learner_level, game_theme)
    world_data = {
        "world_description": world["world_description"],
        "boss": world["boss"],
    }
    world_id = create_learning_world(
        world_name=world["world_name"],
        topic=topic,
        goal=goal,
        learner_level=learner_level,
        game_theme=game_theme,
        subjects=world["subjects"],
        regions=world["regions"],
        monsters=world["monsters"],
        world_data=world_data,
        user_id=user_id,
    )
    world["world_id"] = world_id
    return world


if __name__ == "__main__":
    world = generate_and_save_learning_world(
        topic="SQL",
        goal="데이터 분석 취업을 위한 SQL 실력 향상",
        learner_level="초급",
        game_theme="판타지",
    )
    print(json.dumps(world, ensure_ascii=False, indent=2))
