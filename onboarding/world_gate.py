from __future__ import annotations

import html
import time
from typing import Any

import streamlit as st

from game_core import (
    build_world_intro_lines,
    friendly_ai_error,
    generate_and_save_learning_world,
    get_learning_worlds,
    mark_world_intro_seen,
    set_active_learning_world,
    world_intro_seen,
)


THEMES = ["판타지", "무협", "SF", "귀여운 몬스터", "다크 판타지", "현대"]
LEVELS = ["입문", "초급", "중급", "고급"]


def _ensure_gate_state() -> None:
    defaults = {
        "world_gate_mode": "menu",
        "world_creation_step": 1,
        "world_creation_topic": "",
        "world_creation_goal": "",
        "world_creation_level": "초급",
        "world_creation_theme": "판타지",
        "world_gate_entry_world_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value



def _portal_scene_marker() -> None:
    """로그인/게이트/생성/인트로 동안만 전용 포털 배경을 활성화한다."""
    st.markdown('<div class="portal-mode-marker"></div>', unsafe_allow_html=True)


def _play_single_line_sequence(lines: list[str], *, hold: float = 1.35, gap: float = 0.30) -> None:
    """한 화면에 한 문장만 보여주고, 짧은 공백을 둔 뒤 다음 문장으로 교체한다."""
    stage = st.empty()
    for index, line in enumerate(lines):
        stage.markdown(
            f'<div class="portal-cinematic-line portal-line-{index}">{html.escape(str(line))}</div>',
            unsafe_allow_html=True,
        )
        time.sleep(hold)
        stage.markdown('<div class="portal-cinematic-line portal-blank">&nbsp;</div>', unsafe_allow_html=True)
        time.sleep(gap)
    stage.empty()

def _reset_creation_state() -> None:
    st.session_state.world_creation_step = 1
    st.session_state.world_creation_topic = ""
    st.session_state.world_creation_goal = ""
    st.session_state.world_creation_level = "초급"
    st.session_state.world_creation_theme = "판타지"


def open_world_gate(mode: str = "menu") -> None:
    """게임 내부에서 월드 게이트로 되돌아가기 위한 헬퍼."""
    st.session_state.world_gate_done = False
    st.session_state.world_gate_mode = mode
    if mode == "create":
        _reset_creation_state()
    st.rerun()


def _gate_header() -> None:
    _portal_scene_marker()
    st.markdown(
        """
        <div class="portal-hud-frame">
            <div class="portal-kicker">WORLD GATE</div>
            <div class="portal-gate-title">세계의 문</div>
            <div class="portal-gate-copy">오늘 이어갈 세계를 선택하거나 새로운 세계의 좌표를 개척하세요.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _back_to_menu() -> None:
    if st.button("← 세계의 문으로 돌아가기", key="gate_back_menu"):
        st.session_state.world_gate_mode = "menu"
        st.rerun()


def _render_menu() -> None:
    _gate_header()
    display_name = html.escape(str(st.session_state.get("auth_display_name", "플레이어")))
    tier = html.escape(str(st.session_state.get("auth_test_tier", "")))
    st.markdown(
        f'<div class="gate-player-line">플레이어 <b>「{display_name}」</b> 확인 · {tier} 프로필</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            """
            <div class="gate-choice-card">
                <div class="gate-choice-icon">🗝️</div>
                <div class="gate-choice-title">기존 세계로 귀환</div>
                <div class="gate-choice-copy">이미 만들어 둔 학습 월드를 불러와 이어서 플레이합니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("기존 월드 선택", key="gate_existing", type="primary", width="stretch"):
            st.session_state.world_gate_mode = "existing"
            st.rerun()

    with right:
        st.markdown(
            """
            <div class="gate-choice-card new-world">
                <div class="gate-choice-icon">✨</div>
                <div class="gate-choice-title">새로운 세계 개척</div>
                <div class="gate-choice-copy">배우고 싶은 주제와 목표를 정해 새로운 학습 세계를 생성합니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("새 월드 생성", key="gate_create", width="stretch"):
            _reset_creation_state()
            st.session_state.world_gate_mode = "create"
            st.rerun()


def _render_existing_worlds() -> None:
    _gate_header()
    worlds = get_learning_worlds()

    if not worlds:
        st.markdown(
            """
            <div class="gate-empty-card">
                <div class="gate-choice-icon">🌌</div>
                <div class="gate-choice-title">아직 기록된 세계가 없습니다.</div>
                <div class="gate-choice-copy">첫 번째 학습 세계를 생성해 여정을 시작하세요.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        if c1.button("✨ 새로운 월드 생성", type="primary", width="stretch"):
            _reset_creation_state()
            st.session_state.world_gate_mode = "create"
            st.rerun()
        if c2.button("← 돌아가기", width="stretch"):
            st.session_state.world_gate_mode = "menu"
            st.rerun()
        return

    st.markdown("### 🗺️ 귀환할 세계를 선택하세요")
    world_ids = [int(w["id"]) for w in worlds]
    active = next((w for w in worlds if w.get("is_active")), worlds[0])
    active_id = int(active["id"])
    selected_id = st.selectbox(
        "기존 월드",
        world_ids,
        index=world_ids.index(active_id) if active_id in world_ids else 0,
        format_func=lambda wid: next(
            f"{w.get('world_name', '이름 없는 세계')} · {w.get('topic', '')}"
            for w in worlds if int(w["id"]) == int(wid)
        ),
        label_visibility="collapsed",
        key="gate_existing_world_selector",
    )
    world = next(w for w in worlds if int(w["id"]) == int(selected_id))
    boss = (world.get("world_data", {}) or {}).get("boss", {}) or {}
    st.markdown(
        f"""
        <div class="gate-world-preview">
            <div class="gate-eyebrow">SELECTED WORLD</div>
            <div class="gate-world-name">🌍 {html.escape(str(world.get('world_name', '이름 없는 세계')))}</div>
            <div class="gate-world-meta">{html.escape(str(world.get('topic', '')))} · {html.escape(str(world.get('learner_level', '')))}</div>
            <div class="gate-world-goal">🎯 {html.escape(str(world.get('goal', '') or '꾸준히 성장하기'))}</div>
            <div class="gate-world-boss">👑 최종 보스 · {html.escape(str(boss.get('name', '미확인')))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 1])
    if c1.button("⚔️ 이 세계로 진입", type="primary", width="stretch"):
        set_active_learning_world(int(selected_id))
        st.session_state.world_gate_entry_world_id = int(selected_id)
        st.session_state.world_gate_mode = "entering"
        st.rerun()
    if c2.button("← 돌아가기", width="stretch"):
        st.session_state.world_gate_mode = "menu"
        st.rerun()


def _render_entry_sequence() -> None:
    _portal_scene_marker()
    worlds = get_learning_worlds()
    target_id = st.session_state.get("world_gate_entry_world_id")
    world = next((w for w in worlds if int(w["id"]) == int(target_id)), None)
    if world is None:
        st.session_state.world_gate_mode = "existing"
        st.rerun()
        return

    display_name = str(st.session_state.get("auth_display_name", "플레이어"))
    level = int(st.session_state.get("level", 1))
    world_name = str(world.get("world_name", "이름 없는 세계"))

    st.markdown('<div class="portal-sequence-kicker">WORLD CONNECTION</div>', unsafe_allow_html=True)
    _play_single_line_sequence([
        "플레이어 정보를 확인하고 있습니다...",
        f"플레이어 「{display_name}」 · Lv.{level} 확인 완료.",
        "장비와 학습 기록을 동기화하고 있습니다...",
        f"「{world_name}」의 좌표가 안정화되었습니다.",
        f"플레이어 「{display_name}」, 「{world_name}」로 진입합니다.",
    ])

    st.session_state.world_gate_done = True
    st.session_state.world_gate_mode = "menu"
    st.session_state.world_gate_entry_world_id = None
    st.rerun()


def _wizard_header(step: int, prompt: str, sub: str) -> None:
    _portal_scene_marker()
    st.markdown(
        f"""
        <div class="portal-oracle-panel">
            <div class="creation-step">WORLD CREATION · {step}/4</div>
            <div class="portal-oracle-question">{html.escape(prompt)}</div>
            <div class="portal-oracle-sub">{html.escape(sub)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _wizard_nav(*, can_next: bool = True, next_label: str = "다음 →") -> tuple[bool, bool]:
    left, right = st.columns([1, 2])
    back = left.button("← 이전", width="stretch", key=f"wizard_back_{st.session_state.world_creation_step}")
    nxt = right.button(next_label, type="primary", width="stretch", disabled=not can_next, key=f"wizard_next_{st.session_state.world_creation_step}")
    return back, nxt


def _render_creation_wizard() -> None:
    _gate_header()
    step = int(st.session_state.world_creation_step)

    if step == 1:
        _wizard_header(1, "여행자여, 무엇을 배우기 위해 이 세계의 문을 두드렸습니까?", "새로운 세계의 중심이 될 학습 주제를 알려주세요.")
        topic = st.text_input(
            "배우고 싶은 것",
            value=st.session_state.world_creation_topic,
            placeholder="예: 데이터분석에 이용되는 통계",
            key="wizard_topic_input",
        )
        st.session_state.world_creation_topic = topic
        c1, c2 = st.columns([1, 2])
        if c1.button("← 취소", width="stretch"):
            st.session_state.world_gate_mode = "menu"
            st.rerun()
        if c2.button("답을 전한다 →", type="primary", width="stretch", disabled=not bool(topic.strip())):
            st.session_state.world_creation_step = 2
            st.rerun()
        return

    if step == 2:
        _wizard_header(2, "그 배움을 통해 어디까지 도달하고 싶습니까?", "당신이 이 세계에서 이루고 싶은 최종 목표를 기록합니다.")
        goal = st.text_area(
            "도달하고 싶은 목표",
            value=st.session_state.world_creation_goal,
            placeholder="예: 실제 프로젝트에서 통계를 선택하고 해석할 수 있는 수준",
            height=120,
            key="wizard_goal_input",
        )
        st.session_state.world_creation_goal = goal
        back, nxt = _wizard_nav(can_next=bool(goal.strip()))
        if back:
            st.session_state.world_creation_step = 1
            st.rerun()
        if nxt:
            st.session_state.world_creation_step = 3
            st.rerun()
        return

    if step == 3:
        _wizard_header(3, "현재 당신이 가진 지식의 힘은 어느 정도입니까?", "현재 수준에 맞춰 세계의 학습 난이도를 설계합니다.")
        current_index = LEVELS.index(st.session_state.world_creation_level) if st.session_state.world_creation_level in LEVELS else 1
        level = st.radio(
            "현재 수준",
            LEVELS,
            index=current_index,
            horizontal=True,
            key="wizard_level_input",
        )
        st.session_state.world_creation_level = level
        back, nxt = _wizard_nav()
        if back:
            st.session_state.world_creation_step = 2
            st.rerun()
        if nxt:
            st.session_state.world_creation_step = 4
            st.rerun()
        return

    if step == 4:
        _wizard_header(4, "마지막으로, 당신이 발을 들일 세계의 모습을 선택하세요.", "세계관은 지역·몬스터·보스의 분위기에 반영됩니다.")
        theme_index = THEMES.index(st.session_state.world_creation_theme) if st.session_state.world_creation_theme in THEMES else 0
        theme = st.selectbox("세계관", THEMES, index=theme_index, key="wizard_theme_input")
        st.session_state.world_creation_theme = theme

        st.markdown(
            f"""
            <div class="creation-summary">
                <div><span>학습 주제</span><b>{html.escape(st.session_state.world_creation_topic)}</b></div>
                <div><span>목표</span><b>{html.escape(st.session_state.world_creation_goal)}</b></div>
                <div><span>현재 수준</span><b>{html.escape(st.session_state.world_creation_level)}</b></div>
                <div><span>세계관</span><b>{html.escape(st.session_state.world_creation_theme)}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        left, right = st.columns([1, 2])
        if left.button("← 이전", width="stretch"):
            st.session_state.world_creation_step = 3
            st.rerun()
        if right.button("✨ 이 설정으로 세계 생성", type="primary", width="stretch"):
            with st.spinner("세계의 좌표를 계산하고 있습니다... Gemini가 커리큘럼과 세계를 생성합니다."):
                try:
                    new_world = generate_and_save_learning_world(
                        topic=st.session_state.world_creation_topic,
                        goal=st.session_state.world_creation_goal,
                        learner_level=st.session_state.world_creation_level,
                        game_theme=st.session_state.world_creation_theme,
                    )
                except Exception as exc:
                    st.error(friendly_ai_error(exc))
                    return

            new_world_id = int(new_world.get("world_id") or new_world.get("id"))
            set_active_learning_world(new_world_id)
            st.session_state.world_gate_entry_world_id = new_world_id
            if new_world.get("_reused_existing_world"):
                st.session_state.world_gate_mode = "entering"
            else:
                st.session_state.world_gate_mode = "intro"
            st.rerun()


def _render_new_world_intro() -> None:
    _portal_scene_marker()
    worlds = get_learning_worlds()
    world_id = st.session_state.get("world_gate_entry_world_id")
    world = next((w for w in worlds if int(w["id"]) == int(world_id)), None)
    if world is None:
        st.session_state.world_gate_mode = "menu"
        st.rerun()
        return

    if world_intro_seen(int(world_id)):
        st.session_state.world_gate_mode = "entering"
        st.rerun()
        return

    st.markdown('<div class="portal-sequence-kicker">NEW WORLD AWAKENING</div>', unsafe_allow_html=True)

    # 재생 전에는 스킵할 수 있고, 재생이 시작되면 한 문장씩 화면을 완전히 교체한다.
    skip_col, play_col = st.columns([1, 3])
    if skip_col.button("⏭ 스킵", key="gate_intro_skip", width="stretch"):
        mark_world_intro_seen(int(world_id))
        st.session_state.world_gate_mode = "entering"
        st.rerun()
    start_intro = play_col.button("✦ 세계의 목소리를 듣는다", type="primary", key="gate_intro_play", width="stretch")

    if not start_intro:
        st.markdown(
            f'<div class="portal-intro-ready">「{html.escape(str(world.get("world_name", "새로운 세계")))}」가 당신의 응답을 기다리고 있습니다.</div>',
            unsafe_allow_html=True,
        )
        return

    intro_lines = [str(line) for line in build_world_intro_lines(world) if str(line).strip()]
    # 마지막은 별도 진입 화면을 덧붙이지 않고 이 문장으로 끝낸다.
    intro_lines.append(f'「{world.get("world_name", "새로운 세계")}」의 첫 번째 여정을 시작합니다.')
    _play_single_line_sequence(intro_lines, hold=1.55, gap=0.38)

    mark_world_intro_seen(int(world_id))
    st.session_state.world_gate_mode = "entering"
    st.rerun()


def render_world_gate() -> bool:
    """로그인 후 게임 홈 진입 전에 표시되는 월드 게이트.

    True를 반환하면 게임 본문을 렌더링해도 된다.
    """
    _ensure_gate_state()
    _portal_scene_marker()
    if st.session_state.get("world_gate_done"):
        return True

    mode = st.session_state.world_gate_mode
    if mode == "existing":
        _render_existing_worlds()
    elif mode == "create":
        _render_creation_wizard()
    elif mode == "entering":
        _render_entry_sequence()
    elif mode == "intro":
        _render_new_world_intro()
    else:
        _render_menu()
    return False
