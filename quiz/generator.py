from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

from quiz.repository import (
    count_available_questions,
    get_active_learning_world,
    initialize_database,
    save_question,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEMINI_MODEL = "gemini-flash-latest"

ALLOWED_DIFFICULTIES = {"쉬움", "보통", "어려움"}
ALLOWED_QUESTION_TYPES = {"multiple_choice", "short_answer"}
XP_BY_DIFFICULTY = {"쉬움": 10, "보통": 25, "어려움": 50}


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


def build_world_category_key(world_id: int, subject_id: str) -> str:
    subject_id = str(subject_id).strip()
    if not subject_id:
        raise ValueError("subject_id는 비어 있을 수 없습니다.")
    return f"world_{int(world_id)}__{subject_id}"


QUESTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "question_type": {
                "type": "string",
                "enum": ["multiple_choice", "short_answer"],
            },
            "question": {"type": "string"},
            "options": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
            "answer": {"type": ["string", "null"]},
            "answers": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
            "explanation": {"type": "string"},
            "keywords": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
        },
        "required": [
            "question_type",
            "question",
            "options",
            "answer",
            "answers",
            "explanation",
            "keywords",
        ],
    },
}


def build_prompt(
    category: str,
    difficulty: str,
    count: int,
    *,
    world_topic: str | None = None,
    world_goal: str | None = None,
    learner_level: str | None = None,
    subject_name: str | None = None,
    subject_description: str | None = None,
) -> str:
    display_subject = str(subject_name or category).strip()
    topic = str(world_topic or display_subject).strip()
    goal = str(world_goal or f"{topic} 학습").strip()
    level = str(learner_level or "중급").strip()
    description = str(subject_description or "").strip()

    return f"""
사용자의 학습을 위한 문제를 생성하라.

[전체 학습 주제]
{topic}

[학습 목표]
{goal}

[학습자 현재 수준]
{level}

[현재 세부 학습 분야]
{display_subject}

[세부 분야 설명]
{description if description else "별도 설명 없음"}

[문제 난이도]
{difficulty}

[생성 문제 수]
{count}

다음 조건을 반드시 지켜라.

1. 문제 유형은 오직 다음 두 종류만 사용한다.
   - multiple_choice
   - short_answer

2. 전체 문제의 약 70%는 multiple_choice,
   약 30%는 short_answer가 되도록 구성한다.
   단, 생성 수가 적으면 가장 자연스러운 비율로 조정한다.

3. subjective, essay, 서술형 문제는 생성하지 않는다.

4. multiple_choice 규칙:
   - options는 정확히 4개
   - answer는 정답 선택지 문자열 1개
   - answers는 null
   - 선택지는 서로 중복되지 않음
   - 정답이 options 안에 정확히 존재해야 함

5. short_answer 규칙:
   - options는 null
   - answer는 null
   - answers는 정답 배열
   - 정답이 하나면 예: ["HAVING"]
   - 여러 빈칸이면 반드시 문제에서 요구한 순서대로 예: ["GROUP BY", "HAVING"]
   - answers의 각 항목은 가능한 한 짧고 명확한 용어, 숫자, 기호, 키워드 또는 짧은 구문으로 작성
   - 장문의 설명을 요구하는 문제를 short_answer로 만들지 않는다.

6. SQL 빈칸, 프로그래밍 함수명, 통계 용어, 공식명, 숫자 계산 결과처럼
   정답이 명확한 문제는 short_answer를 우선 사용한다.

7. '설명하시오', '근거를 서술하시오', '논하시오'처럼
   장문 답변을 요구하는 형태는 만들지 않는다.
   그런 개념은 객관식으로 변환한다.

8. 현재 분야 '{display_subject}'를 실제로 학습하는 데 도움이 되는 문제여야 한다.

9. 난이도 기준:
   쉬움 = 핵심 개념과 기본 원리
   보통 = 개념 적용과 간단한 사례
   어려움 = 복합 적용과 실무/시험형 판단

10. 정답이 애매하거나 복수 해석되는 문제를 만들지 않는다.

11. 해설에는 왜 정답인지 간결하고 정확하게 설명한다.

12. 모든 문제와 해설은 한국어로 작성하되,
    전문용어·코드·SQL 키워드는 원문 표기를 유지한다.

13. 동일하거나 거의 같은 문제를 반복하지 않는다.
"""


def normalize_question(
    raw_question: dict[str, Any],
    *,
    category: str,
    difficulty: str,
    source: str,
) -> dict[str, Any]:
    question_type = str(raw_question.get("question_type", "")).strip()

    if question_type == "short_answer":
        answers = raw_question.get("answers") or []
        cleaned_answers = [str(x).strip() for x in answers if str(x).strip()]
        # 기존 questions.answer TEXT 컬럼을 그대로 활용하기 위해 JSON 문자열로 저장
        stored_answer = json.dumps(cleaned_answers, ensure_ascii=False)
        options = None
        keywords = None
    else:
        stored_answer = str(raw_question.get("answer") or "").strip()
        options = raw_question.get("options")
        keywords = None

    return {
        "category": str(category).strip(),
        "difficulty": str(difficulty).strip(),
        "question_type": question_type,
        "question": str(raw_question.get("question", "")).strip(),
        "options": options,
        "answer": stored_answer,
        "explanation": str(raw_question.get("explanation", "")).strip(),
        "keywords": keywords,
        "xp": XP_BY_DIFFICULTY[difficulty],
        "source": source,
    }


def validate_generated_question(question: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    question_type = str(question.get("question_type", "")).strip()
    question_text = str(question.get("question", "")).strip()
    explanation = str(question.get("explanation", "")).strip()

    if question_type not in ALLOWED_QUESTION_TYPES:
        errors.append("허용되지 않은 question_type")
    if not question_text:
        errors.append("question이 비어 있음")
    if not explanation:
        errors.append("explanation이 비어 있음")

    if question_type == "multiple_choice":
        options = question.get("options")
        answer = str(question.get("answer", "")).strip()
        if not isinstance(options, list):
            errors.append("객관식 options가 리스트가 아님")
        else:
            cleaned = [str(x).strip() for x in options]
            if len(cleaned) != 4:
                errors.append("객관식 선택지가 4개가 아님")
            if len(set(cleaned)) != len(cleaned):
                errors.append("객관식 선택지 중복")
            if answer not in cleaned:
                errors.append("정답이 객관식 선택지에 없음")
            question["options"] = cleaned
        if not answer:
            errors.append("객관식 answer가 비어 있음")

    elif question_type == "short_answer":
        question["options"] = None
        raw = str(question.get("answer", "")).strip()
        try:
            answers = json.loads(raw)
        except Exception:
            answers = []
        if not isinstance(answers, list) or not answers:
            errors.append("단답형 answers가 비어 있음")
        else:
            cleaned = [str(x).strip() for x in answers if str(x).strip()]
            if not cleaned:
                errors.append("단답형 정답이 비어 있음")
            if any(len(x) > 80 for x in cleaned):
                errors.append("단답형 정답이 지나치게 김")
            question["answer"] = json.dumps(cleaned, ensure_ascii=False)
        question["keywords"] = None

    return errors


def validate_generated_questions(
    questions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    valid_questions: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()

    for index, question in enumerate(questions, start=1):
        q_errors = validate_generated_question(question)
        norm = " ".join(str(question.get("question", "")).strip().lower().split())
        if norm in seen:
            q_errors.append("같은 응답 내 중복 문제")
        if q_errors:
            errors.append(f"{index}번 문제: " + ", ".join(q_errors))
            continue
        seen.add(norm)
        valid_questions.append(question)

    return valid_questions, errors


def generate_questions(
    category: str,
    difficulty: str,
    count: int = 5,
    *,
    world_topic: str | None = None,
    world_goal: str | None = None,
    learner_level: str | None = None,
    subject_name: str | None = None,
    subject_description: str | None = None,
) -> list[dict[str, Any]]:
    category = str(category).strip()
    difficulty = str(difficulty).strip()
    count = int(count)

    if not category:
        raise ValueError("category는 비어 있을 수 없습니다.")
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty는 쉬움 / 보통 / 어려움 중 하나여야 합니다.")
    if count < 1:
        raise ValueError("count는 1 이상이어야 합니다.")

    client = get_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=build_prompt(
            category=category,
            difficulty=difficulty,
            count=count,
            world_topic=world_topic,
            world_goal=world_goal,
            learner_level=learner_level,
            subject_name=subject_name,
            subject_description=subject_description,
        ),
        config=types.GenerateContentConfig(
            system_instruction=(
                "너는 정확한 객관식과 단답형 문제를 만드는 전문 교육자다. "
                "장문 서술형은 생성하지 않는다. 정답의 명확성과 자동 채점 가능성을 최우선으로 한다."
            ),
            temperature=0.55,
            response_mime_type="application/json",
            response_json_schema=QUESTION_SCHEMA,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini가 문제 데이터를 반환하지 않았습니다.")

    raw_questions = json.loads(response.text)
    if not isinstance(raw_questions, list):
        raise TypeError("Gemini 응답이 리스트가 아닙니다.")

    source = f"gemini:{GEMINI_MODEL}"
    normalized = [
        normalize_question(
            raw,
            category=category,
            difficulty=difficulty,
            source=source,
        )
        for raw in raw_questions
        if isinstance(raw, dict)
    ]

    valid, validation_errors = validate_generated_questions(normalized)
    if not valid:
        raise RuntimeError(
            "생성된 문제를 검증했지만 사용할 수 있는 문제가 없습니다.\n\n"
            + "\n".join(validation_errors)
        )
    return valid


def ensure_question_pool(
    category: str,
    difficulty: str,
    minimum_count: int = 5,
    generate_count: int = 5,
    *,
    world_topic: str | None = None,
    world_goal: str | None = None,
    learner_level: str | None = None,
    subject_name: str | None = None,
    subject_description: str | None = None,
) -> dict[str, Any]:
    initialize_database()
    before_count = count_available_questions(category, difficulty)
    result = {
        "category": category,
        "difficulty": difficulty,
        "before_count": before_count,
        "api_called": False,
        "generated_count": 0,
        "saved_count": 0,
        "duplicate_count": 0,
        "after_count": before_count,
        "errors": [],
    }

    if before_count >= minimum_count:
        return result

    result["api_called"] = True
    try:
        generated = generate_questions(
            category=category,
            difficulty=difficulty,
            count=generate_count,
            world_topic=world_topic,
            world_goal=world_goal,
            learner_level=learner_level,
            subject_name=subject_name,
            subject_description=subject_description,
        )
    except Exception as exc:
        result["errors"].append(str(exc))
        return result

    result["generated_count"] = len(generated)
    for question in generated:
        try:
            saved = save_question(question)
            if saved:
                result["saved_count"] += 1
            else:
                result["duplicate_count"] += 1
        except Exception as exc:
            result["errors"].append(str(exc))

    result["after_count"] = count_available_questions(category, difficulty)
    return result


def find_subject(world: dict[str, Any], subject_id: str) -> dict[str, Any] | None:
    for subject in world.get("subjects", []):
        if subject.get("subject_id") == subject_id:
            return subject
    return None


def generate_world_subject_questions(
    world: dict[str, Any],
    subject_id: str,
    difficulty: str,
    count: int = 5,
) -> list[dict[str, Any]]:
    subject = find_subject(world, subject_id)
    if subject is None:
        raise ValueError(f"월드에서 subject_id를 찾을 수 없습니다: {subject_id}")

    category_key = build_world_category_key(int(world["id"]), subject_id)
    return generate_questions(
        category=category_key,
        difficulty=difficulty,
        count=count,
        world_topic=world.get("topic", ""),
        world_goal=world.get("goal", ""),
        learner_level=world.get("learner_level", "초급"),
        subject_name=subject.get("name", subject_id),
        subject_description=subject.get("description", ""),
    )


def ensure_world_subject_pool(
    world: dict[str, Any],
    subject_id: str,
    difficulty: str,
    minimum_count: int = 5,
    generate_count: int = 5,
) -> dict[str, Any]:
    subject = find_subject(world, subject_id)
    if subject is None:
        raise ValueError(f"월드에서 subject_id를 찾을 수 없습니다: {subject_id}")

    category_key = build_world_category_key(int(world["id"]), subject_id)
    result = ensure_question_pool(
        category=category_key,
        difficulty=difficulty,
        minimum_count=minimum_count,
        generate_count=generate_count,
        world_topic=world.get("topic", ""),
        world_goal=world.get("goal", ""),
        learner_level=world.get("learner_level", "초급"),
        subject_name=subject.get("name", subject_id),
        subject_description=subject.get("description", ""),
    )
    result["subject_id"] = subject_id
    result["subject_name"] = subject.get("name", subject_id)
    return result


if __name__ == "__main__":
    initialize_database()
    print("=" * 65)
    print("객관식 + 단답형 범용 문제 생성기 테스트")
    print("=" * 65)

    active_world = get_active_learning_world()
    if active_world is None:
        print("활성 학습 월드가 없습니다.")
        raise SystemExit

    subjects = active_world.get("subjects", [])
    if not subjects:
        print("현재 월드에 학습 분야가 없습니다.")
        raise SystemExit

    subject = subjects[0]
    print("현재 월드:", active_world["world_name"])
    print("주제:", active_world["topic"])
    print("테스트 분야:", subject["name"])
    print()

    result = ensure_world_subject_pool(
        world=active_world,
        subject_id=subject["subject_id"],
        difficulty="쉬움",
        minimum_count=5,
        generate_count=5,
    )

    print("Gemini API 호출:", result["api_called"])
    print("생성 문제 수:", result["generated_count"])
    print("DB 저장 수:", result["saved_count"])
    print("생성 후 문제 수:", result["after_count"])
    if result["errors"]:
        print("오류:", result["errors"])
    else:
        print("✅ 객관식 + 단답형 생성기 정상 작동")
